from __future__ import annotations

import json
import logging
import os
import shutil
import stat
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional, Union

import pygit2
import requests

# External dependencies (assumed to exist based on context)
from deploy.installer.git_backend import (
    clone_repository, ensure_origin, fetch_and_reset_branch, install_staged_repository, remote_branch_sha,
)
from deploy.installer.const import (
    GetShaMethod,
    REPO_BRANCH,
    get_remote_sha_methods_for_channel,
    repo_url_for_method,
)
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater
from deploy.installer.toml_config import DEFAULT_SETTINGS
from service.update.setup_schema import legacy_runtime_view, migrate_to_current_schema, setup_channel
from service.update.setup_io import write_setup_toml


# ==============================================================================
# 1. Utility Classes (File System & Networking)
# ==============================================================================

class FileSystemUtils:
    """
    Utilities for file system operations, downloads, and archive handling.
    """

    @staticmethod
    def on_rm_error(func: Any, path: str, _exc_info: Any) -> None:
        """
        Error handler for shutil.rmtree.
        If the error is due to read-only access, change the mode and try again.
        """
        try:
            os.chmod(path, stat.S_IWUSR)
            func(path)
        except Exception:
            pass

    @staticmethod
    def download_file(url: str, parent_path: Path) -> Path:
        """
        Downloads a file from a URL to the specified directory with progress logging.
        """
        filename = url.split("/")[-1]
        logging.info(f"Prepare for downloading {filename}")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Network error downloading {url}: {e}")

        file_path = parent_path / filename
        total_size = int(response.headers.get("Content-Length", 0))

        with open(file_path, "wb") as download_f:
            for chunk in response.iter_content(chunk_size=1024 * 64):
                if not chunk:
                    continue
                download_f.write(chunk)

        logging.info(f"Downloaded {filename} to {file_path} (Size: {total_size})")
        return file_path

    @staticmethod
    def unzip_file(zip_path: Path, out_dir: Path) -> None:
        """
        Extracts a zip archive to the target directory.
        """
        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"{zip_path} is not a valid zip file.")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(path=out_dir)
            logging.info(f"{zip_path} unzip success -> {out_dir}")

    @staticmethod
    def copy_directory_structure(source: Path, target: Path) -> None:
        """
        Recursively copies a directory structure.
        """
        target.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            target_path = target / item.relative_to(source)
            if item.is_dir():
                FileSystemUtils.copy_directory_structure(item, target_path)
            elif item.is_file():
                shutil.copy2(item, target_path)

    @staticmethod
    def delete_pid_file():
        if os.path.exists(".pid"):
            os.remove(".pid")

# ==============================================================================
# 2. Git Operation Handler (pygit2)
# ==============================================================================

class GitOperationHandler:
    """Encapsulates repository operations using the shared pygit2 backend."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.git_dir = self.repo_path / ".git"

    def is_valid_repo(self) -> bool:
        if not self.git_dir.exists():
            return False
        try:
            repo = pygit2.Repository(str(self.repo_path))
            repo.free()
            return True
        except Exception:
            return False

    def get_local_head_sha(self) -> str:
        repo = pygit2.Repository(str(self.repo_path))
        try:
            return str(repo.head.target)
        finally:
            repo.free()

    def get_remote_head_sha(self, url: str, branch: str) -> Optional[str]:
        try:
            return remote_branch_sha(url, branch)
        except Exception as exc:
            logging.error(f"[PyGit2] Failed to get remote SHA: {exc}")
            return None

    def clone(self, url: str) -> None:
        self.repo_path.mkdir(parents=True, exist_ok=True)
        logging.info("Cloning with PyGit2...")
        with tempfile.TemporaryDirectory(prefix="baas-clone-", dir=self.repo_path) as temp_dir:
            staged_path = Path(temp_dir) / "repo"
            repo = clone_repository(url, staged_path)
            repo.free()
            install_staged_repository(staged_path, self.repo_path)

    def ensure_remote_url(self, target_url: str) -> None:
        repo = pygit2.Repository(str(self.repo_path))
        try:
            ensure_origin(repo, target_url)
        finally:
            repo.free()

    def fetch_and_reset(self, branch: str) -> None:
        logging.info("Pulling updates from remote...")
        repo = pygit2.Repository(str(self.repo_path))
        try:
            fetch_and_reset_branch(repo, branch)
        except Exception as exc:
            raise RuntimeError(f"PyGit2 update failed: {exc}") from exc
        finally:
            repo.free()

    def repair_repo(self, url: str) -> None:
        """Repair metadata after a successful clone, preserving user data."""
        logging.warning("Attempting to repair invalid/corrupted Git repo...")
        self.clone(url)
        logging.info("Git repository successfully repaired.")


# ==============================================================================
# 3. Update Manager (Orchestrator)
# ==============================================================================

class UpdateManager:
    """
    Manages the update process for BAAS.
    Coordinates between Config, Git, and MirrorC.
    """

    def __init__(self, setup_data: Dict[str, Any], config_path: Path):
        self.raw_data = migrate_to_current_schema(setup_data)
        # Convert dict to SimpleNamespace for dot-access compatibility
        legacy_data = legacy_runtime_view(self.raw_data)
        if isinstance(legacy_data, dict):
            self.data = json.loads(json.dumps(legacy_data), object_hook=lambda d: SimpleNamespace(**d))
        else:
            self.data = legacy_data

        self.config_path = config_path
        self.root_path = Path(self.data.Paths.BAAS_ROOT_PATH)
        self.tmp_path = self.root_path / self.data.Paths.TMP_PATH

        self.git_ops = GitOperationHandler(self.root_path)
        self.channel = setup_channel(self.raw_data)
        self.mirrorc = MirrorC_Updater(app="BAAS_repo", current_version="", channel=self.channel)

        self.local_sha = ""
        self.remote_sha = ""
        self.update_type = "latest"  # 'latest', 'full', 'incremental'
        self.mirrorc_cdk = self.data.General.mirrorc_cdk
        self.sha_methods = get_remote_sha_methods_for_channel(self.channel)

    def save_config(self, key_path: str, value: Any) -> None:
        """Updates a specific key in the TOML config file."""
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                import tomli as tomllib
                current_data = migrate_to_current_schema(tomllib.load(f))
        else:
            current_data = migrate_to_current_schema(DEFAULT_SETTINGS)

        key_map = {
            "General.get_remote_sha_method": "general.get_remote_sha_method",
            "General.current_BAAS_version": "general.current_baas_sha",
            "General.channel": "general.channel",
            "General.dev": None,
            "URLs.REPO_URL_HTTP": None,
        }
        key_path = key_map.get(key_path, key_path)
        if key_path is None:
            return

        keys = key_path.split('.')
        ref = current_data
        for k in keys[:-1]:
            ref = ref.setdefault(k, {})
        ref[keys[-1]] = value

        write_setup_toml(current_data, self.config_path)

    def determine_update_status(self) -> None:
        """
        Checks local vs remote versions and determines if update is needed.
        """
        self.local_sha = self.data.General.current_BAAS_version

        # Case 1: No local version recorded (First install or corrupted config)
        if not self.local_sha:
            if self.git_ops.is_valid_repo():
                try:
                    self.local_sha = self.git_ops.get_local_head_sha()
                except Exception as e:
                    logging.error(f"Repo corrupted: {e}. Triggering full reinstall.")
                    self.update_type = "full"
                    return
            else:
                self.update_type = "full"
                return

        # Case 2: Standard version check
        self.mirrorc.set_version(self.local_sha)

        try:
            self.remote_sha = self._fetch_best_remote_sha()
        except Exception:
            logging.error("Could not fetch remote SHA. Skipping update.")
            self.update_type = "latest"
            return

        logging.info(f"Local SHA : {self.local_sha}")
        logging.info(f"Remote SHA: {self.remote_sha}")

        if self.local_sha == self.remote_sha:
            self.update_type = "latest"
        else:
            self.update_type = "incremental"

    def _fetch_best_remote_sha(self) -> str:
        """
        Iterates through configured methods to find the remote SHA.
        Saves the successful method for future use.
        """
        # 1. Try saved method first
        saved_method_name = self.data.General.get_remote_sha_method
        if saved_method_name:
            method_conf = next((m for m in self.sha_methods if m["name"] == saved_method_name), None)
            if method_conf:
                sha = self._get_sha_from_method(method_conf)
                if sha: return sha

        # 2. Try all methods
        for method in self.sha_methods:
            sha = self._get_sha_from_method(method)
            if sha:
                logging.info(f"Setting default remote SHA method -> [ {method['name']} ]")
                self.save_config("General.get_remote_sha_method", method["name"])
                return sha

        raise RuntimeError("All remote SHA fetch methods failed.")

    def _get_sha_from_method(self, method: Dict) -> Optional[str]:
        """executes a specific SHA retrieval strategy."""
        logging.info(f"[ {method['name']} ] Fetching latest SHA...")

        if method["method"] == GetShaMethod.GITHUB_API:
            return self._github_api_get_sha(method)
        elif method["method"] == GetShaMethod.PYGIT2:
            # We use our Git wrapper here, but adapt the input
            return self.git_ops.get_remote_head_sha(method["url"], method["branch"])
        elif method["method"] == GetShaMethod.MIRRORC_API:
            return self._mirrorc_api_get_sha()
        return None

    @staticmethod
    def _github_api_get_sha(data: Dict) -> Optional[str]:
        url = f"https://api.github.com/repos/{data['owner']}/{data['repo']}/branches/{data['branch']}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("commit", {}).get("sha")
        except Exception as e:
            logging.warning(f"GitHub API Error: {e}")
        return None

    def _mirrorc_api_get_sha(self) -> Optional[str]:
        try:
            ret = self.mirrorc.get_latest_version(cdk=self.mirrorc_cdk)
            if ret.has_data:
                return ret.latest_version_name
            logging.warning(f"MirrorC API Error: {ret.message}")
        except Exception as e:
            logging.warning(f"MirrorC API Exception: {e}")
        return None

    def execute_update(self) -> None:
        """
        Main execution flow.
        """
        if self.update_type == "latest":
            logging.info("No Update Available.")
            return

        # Strategy: Try MirrorC first (if CDK exists), then Git
        success = False
        if self.mirrorc_cdk:
            success = self._try_mirrorc_update()

        if not success:
            self._try_git_update()

    def _try_mirrorc_update(self) -> bool:
        """
        Attempts update via MirrorC (Incremental or Full).
        """
        # Get info from MirrorC
        ret = self.mirrorc.get_latest_version(cdk=self.mirrorc_cdk)
        if not ret.has_url:
            logging.warning("MirrorC valid but no download URL returned.")
            return False

        # Check versions match
        if ret.latest_version_name == self.local_sha and self.update_type != "full":
            logging.info("MirrorC indicates up to date.")
            return True

        # Handle Incremental Wait Logic
        if ret.update_type == "full" and self.update_type == "incremental":
            logging.info("Waiting for incremental package generation...")
            for i in range(10):
                time.sleep(1)
                ret = self.mirrorc.get_latest_version(cdk=self.mirrorc_cdk)
                if ret.update_type == "incremental":
                    break

        try:
            # Download
            file_mb = ret.file_size / (1024 * 1024)
            logging.info(f"Downloading MirrorC package ({ret.update_type}), Size: {file_mb:.2f} MB")
            self.tmp_path.mkdir(parents=True, exist_ok=True)
            zip_path = FileSystemUtils.download_file(ret.download_url, self.tmp_path)

            # Unzip
            FileSystemUtils.unzip_file(zip_path, self.tmp_path)

            if ret.update_type == "incremental":
                logging.info("Applying Incremental Patch...")
                MirrorC_Updater.apply_update(
                    self.tmp_path,
                    self.tmp_path / "changes.json",
                    self.root_path,
                    logging
                )
            else:
                logging.info("Applying Full Install...")
                extracted_root = self.tmp_path / "blue_archive_auto_script"
                FileSystemUtils.copy_directory_structure(extracted_root, self.root_path)

            # Cleanup .git if we are moving to pure file management via MirrorC
            if self.git_ops.git_dir.exists():
                logging.info("Removing .git directory after MirrorC update...")
                shutil.rmtree(self.git_ops.git_dir, onerror=FileSystemUtils.on_rm_error)

            self.save_config("General.current_BAAS_version", ret.latest_version_name)
            logging.info("MirrorC Update Success!")
            return True

        except Exception as e:
            logging.error(f"MirrorC Update Failed: {e}")
            return False

    def _try_git_update(self) -> None:
        """
        Attempts update via Git.
        """
        logging.info("+--------------------------------+")
        logging.info("|        GIT UPDATE BAAS         |")
        logging.info("+--------------------------------+")

        try:
            repo_url = repo_url_for_method(self.data.General.get_remote_sha_method, self.channel)
            if repo_url:
                self.data.URLs.REPO_URL_HTTP = repo_url
                self.save_config("URLs.REPO_URL_HTTP", repo_url)
            self.save_config("General.channel", self.channel)
            self.save_config("General.dev", self.channel == "dev")
            # 1. Check/Repair Repo
            if not self.git_ops.is_valid_repo():
                self.git_ops.repair_repo(self.data.URLs.REPO_URL_HTTP)

            # 2. Check Remote URL
            self.git_ops.ensure_remote_url(self.data.URLs.REPO_URL_HTTP)

            # 3. Clean if requested
            if self.data.General.refresh:
                logging.info("Refresh enabled: Dropping local changes.")
                # Logic handled implicitly by fetch_and_reset(ResetMode.HARD)

            # 4. Update
            self.git_ops.fetch_and_reset(REPO_BRANCH)

            # 5. Verify
            new_sha = self.git_ops.get_local_head_sha()
            self.save_config("General.current_BAAS_version", new_sha)

            if new_sha == self.remote_sha:
                logging.info("Git Update Success.")
            else:
                # Warning only, as sometimes remote SHA detection lags or differs slightly
                logging.warning("Update finished, but SHA does not match expected remote SHA.")

        except Exception as e:
            if "ownership" in str(e).lower():
                logging.error("Ownership error detected. Attempting full repair...")
                self.git_ops.repair_repo(self.data.URLs.REPO_URL_HTTP)
                self.git_ops.fetch_and_reset(REPO_BRANCH)
            else:
                logging.error(f"Git Update Failed: {e}")
                raise


# ==============================================================================
# 4. Entry Point (Backward Compatibility)
# ==============================================================================

def update_repo_to_latest(setup_data: Dict[str, Any], path: Union[str, Path]) -> None:
    """
    Main entry point for the update process.
    """
    config_path = Path(path)

    manager = UpdateManager(setup_data, config_path)

    # 1. Determine what needs to be done
    manager.determine_update_status()

    # 2. Execute
    manager.execute_update()

    # 3. Restart
    logging.info("Update Success! Now restarting ...")

    os.execv(sys.executable, ['python'] + sys.argv)


__all__ = ["update_repo_to_latest"]
