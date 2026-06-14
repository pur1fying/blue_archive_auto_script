from __future__ import annotations

import json
import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union

import pygit2
import requests
import tomli_w
from pygit2.enums import ResetMode

# External dependencies (assumed to exist based on context)
from deploy.installer.const import GetShaMethod, get_remote_sha_methods, REPO_BRANCH
from deploy.installer.mirrorc_update.mirrorc_updater import MirrorC_Updater
from deploy.installer.toml_config import DEFAULT_SETTINGS


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
# 2. Git Operation Handler (System Git > Pygit2)
# ==============================================================================

class GitOperationHandler:
    """
    Encapsulates all Git operations.

    Priority Rule:
    1. System Git (subprocess): Used for Read/Write/Update if available.
    2. Pygit2: Used as fallback if System Git is missing.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.git_executable = shutil.which("git")
        self.git_dir = repo_path / ".git"

    def _run_git_cmd(self, args: List[str], cwd: Optional[Path] = None) -> str:
        """
        Helper to execute system git commands.
        """
        if not self.git_executable:
            raise RuntimeError("System git executable not found.")

        target_cwd = cwd or self.repo_path
        if not target_cwd.exists():
            raise FileNotFoundError(f"Directory {target_cwd} does not exist.")

        # Suppress password prompts
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        try:
            result = subprocess.run(
                [self.git_executable, *args],
                cwd=target_cwd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # Pass the stderr up for debugging
            raise RuntimeError(f"Git command failed: {' '.join(args)}\nStderr: {e.stderr.strip()}")

    def is_valid_repo(self) -> bool:
        """Check if the directory is a valid git repository."""
        if not self.git_dir.exists():
            return False
        try:
            if self.git_executable:
                self._run_git_cmd(["rev-parse", "--is-inside-work-tree"])
                return True
            else:
                pygit2.Repository(str(self.repo_path))
                return True
        except Exception:
            return False

    def get_local_head_sha(self) -> str:
        """Retrieve the current HEAD SHA."""
        if self.git_executable:
            try:
                return self._run_git_cmd(["rev-parse", "HEAD"])
            except Exception as e:
                logging.warning(f"[System Git] Failed to get local SHA: {e}")

        # Fallback
        repo = pygit2.Repository(str(self.repo_path))
        return str(repo.head.target)

    def get_remote_head_sha(self, url: str, branch: str) -> Optional[str]:
        """
        Retrieve the latest SHA from the remote.
        Uses ls-remote.
        """
        if self.git_executable:
            try:
                ref = f"refs/heads/{branch}"
                output = self._run_git_cmd(["ls-remote", url, ref], cwd=Path.cwd())  # generic cwd
                if output:
                    return output.split()[0]
            except Exception as e:
                logging.warning(f"[System Git] Failed to ls-remote: {e}")

        # Fallback
        try:
            # Use a temporary bare repo context to avoid locking/config issues
            with tempfile.TemporaryDirectory() as tmp_dir:
                repo = pygit2.init_repository(tmp_dir, bare=True)
                remote = repo.remotes.create_anonymous(url)
                target_ref = f"refs/heads/{branch}"
                for head in remote.ls_remotes():
                    if head.get("name") == target_ref:
                        return str(head.get("oid"))
        except Exception as e:
            logging.error(f"[PyGit2] Failed to get remote SHA: {e}")

        return None

    def clone(self, url: str) -> None:
        """Clones the repository."""
        if self.repo_path.exists() and any(self.repo_path.iterdir()):
            logging.warning(f"Directory {self.repo_path} is not empty. Cleaning up...")
            shutil.rmtree(self.repo_path, onerror=FileSystemUtils.on_rm_error)

        self.repo_path.mkdir(parents=True, exist_ok=True)

        if self.git_executable:
            logging.info("Cloning with System Git...")
            self._run_git_cmd(["clone", url, "."], cwd=self.repo_path)
        else:
            logging.info("Cloning with PyGit2...")
            pygit2.clone_repository(url, str(self.repo_path))

    def ensure_remote_url(self, target_url: str) -> None:
        """
        Ensures the 'origin' remote matches the target URL.
        If not, it updates the remote.
        """
        if self.git_executable:
            try:
                current_url = self._run_git_cmd(["remote", "get-url", "origin"])
                if current_url.strip() != target_url:
                    logging.info(f"Switching remote URL: {current_url} -> {target_url}")
                    self._run_git_cmd(["remote", "set-url", "origin", target_url])
                return
            except Exception as e:
                logging.warning(f"[System Git] Failed to check remote URL: {e}")

        # Fallback / Pygit2 logic
        try:
            repo = pygit2.Repository(str(self.repo_path))
            origin = repo.remotes["origin"]
            if origin.url != target_url:
                logging.info(f"Switching remote URL (PyGit2): {origin.url} -> {target_url}")
                repo.remotes.delete("origin")
                repo.remotes.create("origin", target_url)
                # Note: Upstream branch tracking fixup is complex in pygit2,
                # usually a fetch + checkout handles it in the next step.
        except Exception as e:
            logging.error(f"Failed to switch remote URL: {e}")

    def fetch_and_reset(self, branch: str) -> None:
        """
        Performs a fetch and hard reset to the remote branch.
        """
        logging.info("Pulling updates from remote...")

        if self.git_executable:
            try:
                self._run_git_cmd(["fetch", "origin"])
                self._run_git_cmd(["reset", "--hard", f"origin/{branch}"])
                self._run_git_cmd(["checkout", branch])
                return
            except Exception as e:
                logging.error(f"[System Git] Update failed: {e}")
                # Fall through to fallback

        # Fallback / Pygit2
        try:
            repo = pygit2.Repository(str(self.repo_path))
            origin = repo.remotes["origin"]

            # Simple progress callback
            class Progress(pygit2.callbacks.RemoteCallbacks):
                def transfer_progress(self, stats):
                    pass  # Keep log clean or add logging if needed

            origin.fetch(callbacks=Progress())

            remote_ref_name = f"refs/remotes/origin/{branch}"
            remote_commit_oid = repo.lookup_reference(remote_ref_name).target

            repo.reset(remote_commit_oid, ResetMode.HARD)
            repo.checkout(f"refs/heads/{branch}")
        except Exception as e:
            raise RuntimeError(f"PyGit2 Update failed: {e}")

    def repair_repo(self, url: str) -> None:
        """
        Destructive repair: Deletes .git and re-clones into a temp folder, then moves files back.
        """
        logging.warning("Attempting to repair invalid/corrupted Git repo...")

        # 1. Clean existing .git
        if self.git_dir.exists():
            shutil.rmtree(self.git_dir, onerror=FileSystemUtils.on_rm_error)

        # 2. Clone to temp
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_repo_path = Path(tmp_dir) / "temp_clone"
            temp_repo_path.mkdir()

            # Use self.clone logic (supports system git)
            temp_handler = GitOperationHandler(temp_repo_path)
            temp_handler.clone(url)

            # 3. Move files
            logging.info("Restoring repository files...")
            for item in temp_repo_path.iterdir():
                dst = self.repo_path / item.name
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst, onerror=FileSystemUtils.on_rm_error)
                    else:
                        dst.unlink()
                shutil.move(str(item), str(dst))

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
        # Convert dict to SimpleNamespace for dot-access compatibility
        if isinstance(setup_data, dict):
            self.data = json.loads(json.dumps(setup_data), object_hook=lambda d: SimpleNamespace(**d))
        else:
            self.data = setup_data

        self.config_path = config_path
        self.root_path = Path(self.data.Paths.BAAS_ROOT_PATH)
        self.tmp_path = self.root_path / self.data.Paths.TMP_PATH

        self.git_ops = GitOperationHandler(self.root_path)
        self.mirrorc = MirrorC_Updater(app="BAAS_repo", current_version="")

        self.local_sha = ""
        self.remote_sha = ""
        self.update_type = "latest"  # 'latest', 'full', 'incremental'
        self.mirrorc_cdk = self.data.General.mirrorc_cdk

    def save_config(self, key_path: str, value: Any) -> None:
        """Updates a specific key in the TOML config file."""
        keys = key_path.split('.')
        # Reload raw dict to ensure we don't lose data during simpleNamespace conversion
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                import tomli as tomllib
                current_data = tomllib.load(f)
        else:
            current_data = DEFAULT_SETTINGS.copy()

        # Navigate to key
        ref = current_data
        for k in keys[:-1]:
            ref = ref.setdefault(k, {})
        ref[keys[-1]] = value

        # Write back
        with open(self.config_path, "wb") as f:
            tomli_w.dump(current_data, f)

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
            method_conf = next((m for m in get_remote_sha_methods if m["name"] == saved_method_name), None)
            if method_conf:
                sha = self._get_sha_from_method(method_conf)
                if sha: return sha

        # 2. Try all methods
        for method in get_remote_sha_methods:
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
