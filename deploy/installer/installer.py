# -*- coding: utf-8 -*-

# ==================== Welcome Message ====================
print(
    """
     ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
     █                                                           █
     █              ██████╗  █████╗  █████╗ ███████╗             █
     █              ██╔══██╗██╔══██╗██╔══██╗██╔════╝             █
     █              ██████╔╝███████║███████║███████╗             █
     █              ██╔══██╗██╔══██║██╔══██║╚════██║             █
     █              ██████╔╝██║  ██║██║  ██║███████║             █
     █              ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝             █
     █                                                           █
     █===========================================================█
     █                                                           █
     █            Welcome to BlueArchive Auto Script!            █
     █                欢迎使用蔚蓝档案自动脚本！                 █
     █           　   ブルアカオートへようこそ！               　█
     █          블루 아카이브 자동 스크립트 환영합니다!          █
     █                                                           █
     █                                   Developed by pur1fying  █
     █                                         LICENSE: GPL-3.0  █
     █    https://github.com/pur1fying/blue_archive_auto_script  █
     █                                                           █
     ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    """
)

# ==================== Import Statements ====================
import gc
import time
import getpass
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, List, Any, Union

import psutil
import pygit2
import requests
import tomli_w
from alive_progress import alive_bar
from easydict import EasyDict as eDict
from halo import Halo
from loguru import logger
from pygit2 import Repository
from pygit2.enums import ResetMode
from pygit2.callbacks import RemoteCallbacks

# Internal imports
from toml_config import TOML_Config, DEFAULT_SETTINGS
from mirrorc_update.mirrorc_updater import MirrorC_Updater
from const import GetShaMethod, get_remote_sha_methods, REPO_BRANCH

# ==================== Global Constants & System Checks ====================

__system__ = platform.system()
if __system__ not in ["Windows", "Linux"]:
    raise OSError(f"Unsupported OS: {__system__}. Only Windows and Linux are supported.")

# Environment setup
__env__ = os.environ.copy()
if __system__ == "Windows":
    __env__["PYTHONPATH"] = '.env;.venv/Lib;.venv/Scripts;.venv;.;.venv/Lib/site-packages'

os.environ["PDM_IGNORE_ACTIVE_VENV"] = "1"

# ==================== Logging Configuration ====================

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO",
)

logger.add(
    Path() / "log" / "installer.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)

spinner = Halo()

# ==================== Welcome Message ====================
logger.info("Blue Archive Auto Script Launcher & Installer")
logger.info("GitHub Repo: https://github.com/pur1fying/blue_archive_auto_script")
logger.info("Official QQ Group: 658302636")


# ==================== Class Definitions ====================

class GlobalConfig:
    """
    Manages configuration loading, saving, and global path definitions.
    """

    def __init__(self):
        if getattr(sys, "frozen", False):
            self.base_path = Path(sys.argv[0]).resolve().parent
        else:
            self.base_path = Path(__file__).resolve().parent

        if __system__ == "Linux":
            self.base_path = Path("~").expanduser() / ".baas"

        self.base_path.mkdir(parents=True, exist_ok=True)
        self.config_file = self.base_path / "setup.toml"
        self.config_obj = None
        self.data = None  # Holds the EasyDict representation

        self._load_or_create_config()
        self._parse_settings()

    def _load_or_create_config(self):
        """Loads setup.toml or creates it with defaults."""
        if not self.config_file.exists():
            # Initial setup for Linux requires password for sudo ops
            if __system__ == "Linux":
                print("First time setup: Password required for package installation (sudo).")
                pwd = getpass.getpass("Please enter your password: ")
                DEFAULT_SETTINGS["General"]["linux_pwd"] = pwd

            with open(self.config_file, "wb") as f:
                tomli_w.dump(DEFAULT_SETTINGS, f)

        self.config_obj = TOML_Config(self.config_file)

        # Merge defaults into current config to handle version upgrades
        modified = False

        def recursive_merge(cfg, defaults):
            nonlocal modified
            for k, v in defaults.items():
                if k not in cfg:
                    modified = True
                    cfg[k] = v
                if isinstance(v, dict):
                    recursive_merge(cfg[k], v)

        recursive_merge(self.config_obj.config, DEFAULT_SETTINGS)
        if modified:
            self.config_obj.save()

    def _parse_settings(self):
        """Parses config sections into easy-to-access attributes."""
        self.General = eDict(self.config_obj.get("General"))
        self.URLs = eDict(self.config_obj.get("URLs"))
        self.Paths = eDict(self.config_obj.get("Paths"))

        # Path resolution
        self.baas_root = Path(self.Paths.BAAS_ROOT_PATH).resolve() if self.Paths.BAAS_ROOT_PATH else self.base_path
        self.toolkit_path = self.baas_root / self.Paths.TOOL_KIT_PATH

        # Ensure directories exist
        for p in [self.baas_root, self.toolkit_path]:
            p.mkdir(parents=True, exist_ok=True)

        # Normalize Windows paths in runtime config
        if self.General.runtime_path:
            self.General.runtime_path = self.General.runtime_path.replace("\\", "/")

    def save_value(self, key_path: str, value: Any):
        """Saves a specific value to the TOML file."""
        self.config_obj.set_and_save(key_path, value)


class FileSystemUtils:
    """
    Utilities for file system operations, downloading, and extraction.
    """

    @staticmethod
    def on_rm_error(func, path, _exc_info):
        """Error handler for shutil.rmtree to handle read-only files."""
        try:
            os.chmod(path, stat.S_IWUSR)
            func(path)
        except Exception:
            pass

    @staticmethod
    def download_file(url: str, parent_path: Union[str, Path]) -> Path:
        """Downloads a file with a progress bar."""
        filename = url.split("/")[-1]
        logger.info(f"Downloading {filename}...")
        if type(parent_path) == str:
            parent_path = Path(parent_path)
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Download failed for {url}: {e}")

        file_path = parent_path / filename
        total_size = int(response.headers.get("Content-Length", 0))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with alive_bar(total_size, unit="B", bar="smooth", title=f"Downloading {filename}") as bar:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
                        bar(len(chunk))

        logger.success(f"Downloaded to {file_path}")
        return file_path

    @staticmethod
    def unzip_file(zip_path: Union[str, Path], out_dir: Path):
        """Extracts a zip file."""
        if type(zip_path) == str:
            zip_path = Path(zip_path)
        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"Invalid zip file: {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(path=out_dir)
        logger.success(f"Extracted {zip_path} to {out_dir}")

    @staticmethod
    def copy_directory_structure(source: Union[str, Path], target: Path):
        """Recursively copies files and directories."""
        if type(source) == str:
            source = Path(source)
        target.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            target_path = target / item.relative_to(source)
            if item.is_dir():
                FileSystemUtils.copy_directory_structure(item, target_path)
            elif item.is_file():
                shutil.copy2(item, target_path)

    @staticmethod
    def sudo(cmd: str, pwd: str):
        """Executes a command with sudo on Linux."""
        os.system(f"echo {pwd} | sudo -S {cmd}")


class GitOperationHandler:
    """
    Handles Git operations with a priority strategy:
    1. System Git (subprocess) - Preferred for speed and robustness.
    2. PyGit2 - Fallback if System Git is missing.
    3. PyGit2 (Strict) - Mandatory for rollback operations.
    """

    def __init__(self, repo_path: Path, remote_url: str):
        self.repo_path = repo_path
        self.remote_url = remote_url
        self.git_executable = shutil.which("git")
        self.git_dir = repo_path / ".git"

    def _run_git_cmd(self, args: List[str], cwd: Optional[Path] = None) -> str:
        """Executes a system git command."""
        if not self.git_executable:
            raise RuntimeError("System git not found.")

        target_cwd = cwd or self.repo_path
        if not target_cwd.exists():
            raise FileNotFoundError(f"Target directory {target_cwd} does not exist.")

        # Disable interactive prompts
        env = __env__.copy()
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
            raise RuntimeError(f"Git command failed: {e.stderr}")

    def is_valid_repo(self) -> bool:
        """Checks if the directory is a valid git repository."""
        if not self.git_dir.exists():
            return False
        try:
            if self.git_executable:
                self._run_git_cmd(["rev-parse", "--is-inside-work-tree"])
            else:
                Repository(str(self.repo_path))
            return True
        except Exception:
            return False

    def get_local_sha(self) -> str:
        """Gets the current HEAD SHA."""
        if self.git_executable:
            try:
                return self._run_git_cmd(["rev-parse", "HEAD"])
            except Exception:
                pass

        repo = Repository(str(self.repo_path))
        return str(repo.head.target)

    def get_remote_sha(self, cfg, mirrorc):
        logger.info("<<< Get Remote SHA >>>")
        if cfg.General.get_remote_sha_method:
            index = next(
                (i for i, item in enumerate(get_remote_sha_methods) \
                 if item.get("name") == cfg.General.get_remote_sha_method), None)
            if index is not None:
                sha = self.get_remote_sha_once(get_remote_sha_methods[index], mirrorc)
                if sha is not None:
                    return sha
                get_remote_sha_methods.pop(index)
        for method in get_remote_sha_methods:
            sha = self.get_remote_sha_once(method, mirrorc={
                "inst": mirrorc,
                "cdk": cfg.General.mirrorc_cdk,
            })
            if sha is not None:
                logger.info(f"Set get remote SHA method --> [ {method['name']} ]")
                cfg.save_value("General.get_remote_sha_method", method["name"])
                return sha
        logger.error("Failed to get remote SHA from all methods.")
        raise Exception("Failed to get remote SHA.")

    def get_remote_sha_once(self, method, mirrorc):
        logger.info(f"[ {method['name']} ] get latest SHA.")
        if method["method"] == GetShaMethod.GITHUB_API:
            return self.github_api_get_latest_sha(method)
        elif method["method"] == GetShaMethod.PYGIT2:
            return self.git_get_remote_sha()
        elif method["method"] == GetShaMethod.MIRRORC_API:
            return self.mirrorc_api_get_latest_sha(mirrorc)
        else:
            return None

    @staticmethod
    def github_api_get_latest_sha(data):
        owner = data["owner"]
        repo = data["repo"]
        branch = data["branch"]
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
        try:
            response = requests.get(url, timeout=3.0)
            if response.status_code != 200:
                return None
            response_json = response.json()
            return response_json.get("commit", {}).get("sha")
        except requests.RequestException as e:
            logger.warning(f"[Github Api] get SHA error: {e}")
            return None

    @staticmethod
    def mirrorc_api_get_latest_sha(mirrorc):
        inst = mirrorc["inst"]
        cdk = mirrorc["cdk"]
        try:
            latest_mirrorc_return = inst.get_latest_version(cdk=cdk)
            if latest_mirrorc_return.has_data:
                return latest_mirrorc_return.latest_version_name
            else:
                logger.error(f"[MirrorC Api] get SHA error: {latest_mirrorc_return.message}")
        except Exception as e:
            logger.error(f"[MirrorC Api] get SHA error: {e}")
            return None

    def git_get_remote_sha(self, branch: str = REPO_BRANCH) -> Optional[str]:
        """Gets the latest SHA from the remote using ls-remote."""
        # 1. Try System Git
        if self.git_executable:
            try:
                ref = f"refs/heads/{branch}"
                out = self._run_git_cmd(["ls-remote", self.remote_url, ref], cwd=Path.cwd())
                if out:
                    return out.split()[0]
            except Exception as e:
                logger.warning(f"[System Git] ls-remote failed: {e}")

        # 2. Fallback to PyGit2 (Anonymous)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = pygit2.init_repository(tmp, bare=True)
                remote = repo.remotes.create_anonymous(self.remote_url)
                target_ref = f"refs/heads/{branch}"
                for head in remote.list_heads():
                    if head.name == target_ref:
                        return str(head.oid)
        except Exception as e:
            logger.error(f"[PyGit2] ls-remote failed: {e}")

        return None

    def clone(self, branch: str = REPO_BRANCH):
        """Clones the repository."""
        logger.info(f"Cloning {self.remote_url}...")

        # Create the target directory if it doesn't exist
        self.repo_path.mkdir(parents=True, exist_ok=True)

        # Create a temporary directory to clone the repo
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_repo_path = Path(temp_dir)

            if self.git_executable:
                # Use System Git to clone into the temporary directory
                self._run_git_cmd(["clone", "-b", branch, self.remote_url, "."], cwd=temp_repo_path)
                logger.success("Clone successful (System Git).")
            else:
                # Use PyGit2 to clone into the temporary directory with progress
                bar_ref = {"bar": None}
                callbacks = BAASGitCallbacks(bar_ref)
                pygit2.clone_repository(self.remote_url, str(temp_repo_path), checkout_branch=branch,
                                        callbacks=callbacks)
                callbacks.spinner.stop()
                logger.success("Clone successful (PyGit2).")

            # Move the content from the temp directory to the actual target directory
            for item in temp_repo_path.iterdir():
                # Move each item from temp directory to the actual target directory
                shutil.move(str(item), str(self.repo_path / item.name))

    def update(self, branch: str = REPO_BRANCH):
        """Updates the repository to the latest remote state."""
        logger.info("Updating repository...")

        self.ensure_remote_url()

        if self.git_executable:
            try:
                self._run_git_cmd(["fetch", "origin"])
                self._run_git_cmd(["reset", "--hard", f"origin/{branch}"])
                self._run_git_cmd(["checkout", branch])
                logger.success("Update successful (System Git).")
                return
            except Exception as e:
                logger.error(f"System Git update failed: {e}. Falling back to PyGit2.")

        # Fallback to PyGit2
        try:
            repo = Repository(str(self.repo_path))
            remote = repo.remotes["origin"]
            remote.fetch()
            remote_master_ref = repo.lookup_reference(f"refs/remotes/origin/{branch}")
            repo.reset(remote_master_ref.target, ResetMode.HARD)
            repo.checkout(f"refs/heads/{branch}")
            logger.success("Update successful (PyGit2).")
        except Exception as e:
            raise RuntimeError(f"Update failed: {e}")

    def ensure_remote_url(self):
        """Ensures the remote 'origin' matches the configuration."""
        target_url = self.remote_url
        if self.git_executable:
            try:
                current = self._run_git_cmd(["remote", "get-url", "origin"])
                if current.strip() != target_url:
                    logger.info(f"Switching remote URL: {current} -> {target_url}")
                    self._run_git_cmd(["remote", "set-url", "origin", target_url])
                return
            except Exception:
                pass  # Fallback to pygit2 logic

        try:
            repo = Repository(str(self.repo_path))
            origin = repo.remotes["origin"]
            if origin.url != target_url:
                logger.info(f"Switching remote URL (PyGit2) -> {target_url}")
                repo.remotes.delete("origin")
                repo.remotes.create("origin", target_url)
                repo.remotes["origin"].fetch()
        except Exception as e:
            logger.warning(f"Failed to check/switch remote URL: {e}")

    def repair_repo(self):
        """Destructive repair: Re-clones the repo."""
        logger.warning("Repository is corrupted. Initiating repair...")

        # Use a temp directory for safe cloning
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir) / "temp_repo"
            temp_path.mkdir()

            # Helper to clone into temp
            temp_handler = GitOperationHandler(temp_path, self.remote_url)
            temp_handler.clone()

            # Clean original
            if self.git_dir.exists():
                shutil.rmtree(self.git_dir, onerror=FileSystemUtils.on_rm_error)

            # Restore files
            logger.info("Restoring files...")
            FileSystemUtils.copy_directory_structure(temp_path, self.repo_path)

        logger.success("Repository repaired.")

    def rollback(self, target_sha: str):
        """
        Rollback to a specific SHA.
        REQUIREMENT: Strictly use PyGit2.
        """
        logger.info(f"Rolling back to {target_sha} using PyGit2...")
        repo = Repository(str(self.repo_path))
        commit = repo.revparse_single(target_sha)
        repo.reset(commit.id, ResetMode.HARD)
        repo.checkout_tree(commit.tree)
        logger.success("Rollback successful.")


class BAASGitCallbacks(RemoteCallbacks):
    """Callback handler for PyGit2 clone progress."""

    def __init__(self, bar_ref):
        self.__transmitted = False
        self.bar_ref = bar_ref
        self.received_count = 0
        self.current_count = 0
        self.spinner = Halo(text="Resolving Objects ...", spinner="dots")
        super().__init__()

    def transfer_progress(self, stats):
        if not self.__transmitted:
            self.__transmitted = True
            bar_gen = alive_bar(stats.total_objects, title="Cloning (PyGit2)...")
            self.bar_ref["bar_gen"] = bar_gen
            self.bar_ref["bar"] = bar_gen.__enter__()

        if self.bar_ref.get("bar"):
            self.received_count = stats.received_objects
            self.bar_ref["bar"](self.received_count - self.current_count)
            self.current_count = self.received_count

        if self.received_count == stats.total_objects:
            self.bar_ref["bar_gen"].__exit__(None, None, None)
            self.spinner.start()


class EnvironmentManager:
    """Checks and sets up Python environment, PIP, and dependencies."""

    def __init__(self, config: GlobalConfig):
        self.cfg = config
        self.baas_root = config.baas_root

    def check_pip(self):
        logger.info("Checking pip installation...")
        if __system__ == "Linux":
            return

        assert __system__ == "Windows"
        if not os.path.exists(self.baas_root / ".env/Scripts/pip.exe"):
            logger.warning("Pip is not installed, trying to install pip...")
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "temp_pip"
                filepath = FileSystemUtils.download_file(self.cfg.URLs.GET_PIP_URL, temp_path)
                subprocess.run([self.baas_root / ".env/python.exe", filepath])

    def check_pth(self):
        if __system__ == "Linux":
            return
        if os.path.exists(self.baas_root / ".venv"):
            return
        logger.info("Checking pth file...")
        read_file = []
        with open(self.baas_root / ".env/python39._pth", "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("#import site"):
                    line = line.replace("#", "")
                read_file.append(line)
        with open(self.baas_root / ".env/python39._pth", "w", encoding="utf-8") as f:
            f.writelines(read_file)

    def check_env_patch(self):
        if __system__ == "Linux":
            return
        if os.path.exists(self.baas_root / ".env/Lib/site-packages/Polygon"):
            return
        logger.info("Downloading env patch...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "temp_repo"
            filepath = FileSystemUtils.download_file(self.cfg.URLs.GET_ENV_PATCH_URL, temp_path)
            FileSystemUtils.unzip_file(filepath, self.baas_root / ".env")

    def check_python(self):
        """Checks for Python installation, installs/creates venv if missing."""
        logger.info("Checking Python environment...")

        venv_path = self.baas_root / ".venv"
        if venv_path.exists(): return

        # Path definitions
        if __system__ == "Windows":
            python_path = self.baas_root / ".env/python.exe"
            if not python_path.exists():
                logger.info("Downloading embedded Python...")
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = FileSystemUtils.download_file(self.cfg.URLs.GET_PYTHON_URL, temp_dir)
                    FileSystemUtils.unzip_file(zip_path, self.baas_root / ".env")
        elif __system__ == "Linux":
            python_path = self.baas_root / ".env/bin/python3"
            if not python_path.exists():
                logger.info("Setting up Python venv (Linux)...")
                pwd = self.cfg.General.linux_pwd
                FileSystemUtils.sudo("add-apt-repository ppa:deadsnakes/ppa -y", pwd)
                FileSystemUtils.sudo("apt update", pwd)
                FileSystemUtils.sudo("apt-get install python3.9-venv -y", pwd)
                FileSystemUtils.sudo(f"python3.9 -m venv {self.baas_root / '.env'}", pwd)

    def install_requirements(self):
        """Installs PIP dependencies."""
        logger.info("Installing requirements...")
        try:
            # Determine pip executable
            if __system__ == "Windows":
                python_exc = str(self.baas_root / ".env/python.exe")
                pip_exec = [python_exc, "-m", "pip"]

                # Setup virtualenv if using default pip mode
                if self.cfg.General.package_manager == "pip" and not (self.baas_root / ".venv").exists():
                    subprocess.run([*pip_exec, "install", "virtualenv", "--no-warn-script-location"], check=True)
                    subprocess.run([python_exc, "-m", "virtualenv", str(self.baas_root / ".venv")], check=True)
                pip_exec = [str(self.baas_root / ".venv/Scripts/python.exe"), "-m", "pip"]

            else:
                # Linux logic
                pip_path = self.baas_root / ".env/bin/pip"
                FileSystemUtils.sudo(f"chown -R $(whoami) {self.baas_root}", self.cfg.General.linux_pwd)
                pip_exec = [str(pip_path)]

            # Install loop with source fallback
            req_file = "requirements-linux.txt" if __system__ == "Linux" else "requirements.txt"

            for source in self.cfg.General.source_list:
                try:
                    cmd = [*pip_exec, "install", "-r", str(self.baas_root / req_file), "-i", source,
                           "--no-warn-script-location"]
                    subprocess.run(cmd, env=__env__, check=True)
                    logger.success("Dependencies installed.")
                    return
                except Exception:
                    logger.warning(f"Failed source {source}, trying next...")

            raise RuntimeError("All pip sources failed.")

        except Exception:
            logger.exception("Failed to install packages.")
            Utils.error_tackle()

    def fix_shebangs(self):
        """Fixes Windows venv exe shebangs to allow portability."""
        if __system__ != "Windows": return

        search_dir = self.baas_root / ".venv/Scripts"
        if not search_dir.exists(): return

        logger.info("Fixing .exe shebangs for portability...")
        # (Logic from original fix_exe_shebangs - compacted)
        pattern = re.compile(rb'#!.*?\\.venv\\Scripts\\python\.exe')
        replacement = b"#!python.exe"

        for root, _, files in os.walk(search_dir):
            for filename in files:
                if filename.lower().endswith(".exe"):
                    path = Path(root) / filename
                    try:
                        data = path.read_bytes()
                        match = pattern.search(data)
                        if match:
                            matched = match.group(0)
                            padding = len(matched) - len(replacement)
                            if padding >= 0:
                                new_data = data.replace(matched, replacement + b' ' * padding, 1)
                                path.write_bytes(new_data)
                    except Exception:
                        pass
        logger.success("Shebangs patched.")


class UpdateOrchestrator:
    """Manages the update process (Git vs MirrorC)."""

    def __init__(self, config: GlobalConfig, env_mgr: EnvironmentManager):
        self.cfg = config
        self.git = GitOperationHandler(config.baas_root, config.URLs.REPO_URL_HTTP)
        self.mirrorc = MirrorC_Updater(app="BAAS_repo", current_version="")
        self.env = env_mgr

    def run(self):
        """Main update execution flow."""
        if self.cfg.General.dev:
            return

        local_sha = self._get_local_version()
        self.mirrorc.set_version(local_sha)

        # 1. Determine Update Necessity
        remote_sha = self._get_remote_version()
        if not remote_sha or local_sha == remote_sha:
            logger.info("No update available.")
            return

        logger.info(f"Update found: {local_sha[:7]} -> {remote_sha[:7]}")

        # 2. Try MirrorC (Incremental/Full)
        if self.cfg.General.mirrorc_cdk and self._try_mirrorc_update():
            return

        # 3. Fallback to Git
        self._git_update()

    def _get_local_version(self) -> str:
        """Determines the local version (SHA)."""
        # Try reading from config first
        stored_sha = self.cfg.General.current_BAAS_version

        if stored_sha and len(stored_sha) == 40:
            return stored_sha

        # Try reading from Git repo
        if self.git.is_valid_repo():
            try:
                sha = self.git.get_local_sha()
                self.cfg.save_value("General.current_BAAS_version", sha)
                return sha
            except Exception:
                pass

        # Assume fresh installation needed
        return ""

    def _get_remote_version(self) -> Optional[str]:
        """Fetches remote SHA using configured methods."""
        # This implementation simplifies the rotation logic from the original code
        # by delegating to the GitHandler or specialized API calls
        return self.git.get_remote_sha(self.cfg, self.mirrorc)

    def _try_mirrorc_update(self) -> bool:
        """Attempts to update via MirrorC."""

        update_type = self._get_mirror_update_type()

        try:
            ret = self.mirrorc.get_latest_version(cdk=self.cfg.General.mirrorc_cdk)
            if not ret.has_url: return False

            logger.info(f"MirrorC Update available ({update_type}).")

            if update_type == "incremental":
                logger.info("+--------------------------------+")
                logger.info("|      MIRRORC UPDATE BAAS       |")
                logger.info("+--------------------------------+")
                logger.info("Applying incremental patch...")
                self._mirrorc_update_baas(latest_mirrorc_return=ret)
            elif update_type == "full":
                logger.info("+--------------------------------+")
                logger.info("|     MIRRORC INSTALL BAAS       |")
                logger.info("+--------------------------------+")
                logger.info("Applying full package...")
                self._mirrorc_install_baas(latest_mirrorc_return=ret)
            else:
                raise Exception(f"Unknown update type {update_type}")

            # Cleanup .git if moving to MirrorC-only management
            if self.git.git_dir.exists():
                shutil.rmtree(self.git.git_dir, onerror=FileSystemUtils.on_rm_error)

            self.cfg.save_value("General.current_BAAS_version", ret.latest_version_name)
            return True
        except Exception as e:
            logger.error(f"MirrorC update failed: {e}")
            return False

    def _get_mirror_update_type(self) -> str:
        local_sha = self.cfg.General.current_BAAS_version
        if len(local_sha) == 0:
            if os.path.exists(self.cfg.Paths.BAAS_ROOT_PATH / ".git"):
                repo = Repository(str(self.cfg.Paths.BAAS_ROOT_PATH))
                # Get local SHA
                try:
                    local_sha = str(repo.head.target)
                except Exception as e:
                    logger.error(f"Incorrect Key or corrupted repo: {e}. Remove [ .git ] folder and reinstall.")
                    del repo
                    gc.collect()
                    shutil.rmtree(self.cfg.Paths.BAAS_ROOT_PATH / ".git")
                    return "full"
            else:
                # first install
                return "full"

        assert (len(local_sha) == 40)
        self.mirrorc.set_version(local_sha)
        remote_sha = self._get_remote_version()
        assert (len(remote_sha) == 40)
        logger.info(f"local_sha : {local_sha}")
        logger.info(f"remote_sha: {remote_sha}")
        if local_sha == remote_sha:
            return "latest"

        return "incremental"

    def _git_update(self):
        """Performs Git install or update."""
        if not self.git.is_valid_repo():
            self.git.clone()
        else:
            try:
                self.git.update()
            except Exception:
                self.git.repair_repo()
                self.git.update()

        new_sha = self.git.get_local_sha()
        self.cfg.save_value("General.current_BAAS_version", new_sha)

    def _mirrorc_install_baas(self, latest_mirrorc_return):
        logger.info("+--------------------------------+")
        logger.info("|     MIRRORC INSTALL BAAS       |")
        logger.info("+--------------------------------+")
        # Download the repository zip file
        file_length = latest_mirrorc_return.file_size / (1024 * 1024)
        logger.info("Downloading the repository zip, total = %.2f MB" % file_length)
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = FileSystemUtils.download_file(
                latest_mirrorc_return.download_url, tmp_dir
            )
            logger.info("Unzipping the repository...")
            FileSystemUtils.unzip_file(zip_path, zip_path)

            logger.info("Moving unzipped files to BAAS root path...")
            file_dir = Path(tmp_dir) / "blue_archive_auto_script"
            FileSystemUtils.copy_directory_structure(file_dir, self.cfg.Paths.BAAS_ROOT_PATH)

        logger.success("Mirrorc Install Success!")

    def _mirrorc_update_baas(self, latest_mirrorc_return):
        logger.info("+--------------------------------+")
        logger.info("|      MIRRORC UPDATE BAAS       |")
        logger.info("+--------------------------------+")

        # wait for incremental update
        if latest_mirrorc_return.update_type == "full":
            logger.info("Current package is [ full ].")
            logger.info("Waiting for [ incremental ] update package...")
            max_retry = 10
            for i in range(1, max_retry + 1):
                time.sleep(0.5)
                logger.info(f"Retry : {i}/{max_retry}")
                latest_mirrorc_return = self.mirrorc.get_latest_version(cdk=self.cfg.General.mirrorc_cdk)
                if latest_mirrorc_return.update_type == "incremental":
                    logger.success("Get Incremental Package")
                    break

        if latest_mirrorc_return.update_type == "incremental":
            logger.info("<<< Incremental Update >>>")
            file_length = latest_mirrorc_return.file_size / (1024 * 1024)
            logger.info("Downloading the incremental zip, total = %.2f MB" % file_length)

            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_path = FileSystemUtils.download_file(
                    latest_mirrorc_return.download_url, tmp_dir
                )
                logger.info("Unzipping the incremental update...")
                FileSystemUtils.unzip_file(zip_path, zip_path)

                MirrorC_Updater.apply_update(
                    tmp_dir,
                    Path(tmp_dir) / "changes.json",
                    Path(self.cfg.Paths.BAAS_ROOT_PATH),
                    logger
                )
            logger.success("Mirrorc Incremental Update Success!")

        if latest_mirrorc_return.update_type == "full":
            logger.info("<<< Full Update >>>")
            self._mirrorc_install_baas(latest_mirrorc_return)


class AppLauncher:
    """Handles launching the main application."""

    def __init__(self, config: GlobalConfig):
        self.cfg = config
        self.baas_root = config.baas_root

    def run_app(self):

        if self.cfg.General.use_dynamic_update:
            self.dynamic_update_installer()

        """Starts window.py."""
        logger.info("Launching App...")

        python_exec = self._get_python_executable()
        env = __env__.copy()

        if __system__ == "Linux":
            env["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(
                self.baas_root / ".env/lib/python3.9/site-packages/PyQt5/Qt5/plugins/platforms")

        cmd = [str(python_exec), str(self.baas_root / "window.py")]

        # Check for running instances
        self._kill_existing_process()

        try:
            if __system__ == "Windows":
                # Detached process
                subprocess.Popen(cmd, cwd=self.baas_root, env=env)
            else:
                subprocess.run(cmd, cwd=self.baas_root, env=env)

            logger.success("App started.")
            # Record PID
            # (Simplified for brevity - logic remains similar to original)

        except Exception as e:
            logger.error(f"Failed to launch app: {e}")
            Utils.error_tackle()

        if __system__ == "Windows" and not self.cfg.General.no_build:
            try:
                import PyInstaller.__main__

                logger.info("Checking UPX installation.")
                if not os.path.exists("toolkit/upx-4.2.4-win64/upx.exe"):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        temp_path = Path(tmpdir)
                        filepath = FileSystemUtils.download_file(self.cfg.URLs.GET_UPX_URL, temp_path)
                        FileSystemUtils.unzip_file(filepath, self.cfg.Paths.TOOL_KIT_PATH)

                def create_executable():
                    PyInstaller.__main__.run(
                        [
                            str(self.cfg.Paths.BAAS_ROOT_PATH / "installer.py"),
                            "--name=BlueArchiveAutoScript",
                            "--onefile",
                            "--icon=gui/assets/logo.ico",
                            "--noconfirm",
                            "--upx-dir",
                            "./toolkit/upx-4.2.4-win64",
                        ]
                    )

                if os.path.exists(self.cfg.Paths.BAAS_ROOT_PATH / "backup.exe") and not os.path.exists(
                    self.cfg.Paths.BAAS_ROOT_PATH / "no_build"
                ):
                    create_executable()
                    logger.info("try to remove the backup executable file.")
                    try:
                        os.remove(self.cfg.Paths.BAAS_ROOT_PATH / "backup.exe")
                    except:
                        logger.info("remove backup.exe failed.")
                    else:
                        logger.info("remove finished.")
                    os.rename("BlueArchiveAutoScript.exe", "backup.exe")
                    shutil.copy("dist/BlueArchiveAutoScript.exe", ".")
            except:
                logger.warning(
                    "Build new BAAS launcher failed, Please check the Python Environment"
                )
                Utils.error_tackle()

    def dynamic_update_installer(self) -> None:
        # Define paths for the installer and Python interpreter
        installer_path = Path(self.cfg.Paths.BAAS_ROOT_PATH )/ "deploy/installer/installer.py"

        # Use platform-independent way to determine Python executable
        if __system__ == "Windows":
            python_path = Path(self.cfg.Paths.BAAS_ROOT_PATH) / ".venv/Scripts/python.exe"
        else:  # Linux/Unix
            python_path = Path(self.cfg.Paths.BAAS_ROOT_PATH) / ".env/bin/python"

        # Prepare the command arguments
        launch_exec_args = sys.argv.copy()
        launch_exec_args[0] = os.path.abspath(python_path)
        launch_exec_args.insert(1, os.path.abspath(installer_path))

        # Check if paths exist and arguments are provided
        if (
            os.path.exists(installer_path)
            and os.path.exists(python_path)
            and len(sys.argv) > 1
        ):
            try:
                subprocess.run(launch_exec_args)
            except:
                logger.exception(f"Error running installer updater...")
                self.run_app()
        elif self.cfg.General.internal_launch:  # Internal launch fallback
            self.run_app()
        else:
            if not os.path.exists(installer_path):
                logger.warning("Installer not found. Launching app directly.")
                self.run_app()
                sys.exit()

            # Use platform-specific commands to start the installer
            if __system__ == "Windows":
                os.system(f'START " " "{python_path}" "{installer_path}" --launch')
            else:  # Linux/Unix
                subprocess.run([python_path, installer_path, "--launch"])
        sys.exit()

    def _get_python_executable(self) -> Path:
        """Determines the correct python executable path."""
        if self.cfg.General.runtime_path != "default":
            return Path(self.cfg.General.runtime_path)

        if __system__ == "Windows":
            return self.baas_root / ".venv/Scripts/pythonw.exe"
        else:
            return self.baas_root / ".env/bin/python3"

    def _kill_existing_process(self):
        """Checks PID file and kills existing instance if configured."""
        pid_file = self.baas_root / "pid"
        if pid_file.exists() and not self.cfg.General.force_launch:
            try:
                pid = int(pid_file.read_text())
                if psutil.pid_exists(pid):
                    logger.info("Terminating existing instance...")
                    psutil.Process(pid).terminate()
            except Exception:
                pass


class Utils:
    """Legacy/Helper static methods."""

    @staticmethod
    def error_tackle():
        logger.info(
            "Now you can turn off this command line window safely or report this issue to developers."
        )
        logger.info("您现在可以安全地关闭此命令行窗口或向开发人员报告此问题。")
        logger.info(
            "今、このコマンドラインウィンドウを安全に閉じるか、この問題を開発者に報告することができます。"
        )
        logger.info(
            "이제 이 명령줄 창을 안전하게 종료하거나 이 문제를 개발자에게 보고할 수 있습니다。"
        )
        if __system__ == "Windows":
            os.system("pause")
        sys.exit(1)


# ==================== Main Execution Flow ====================

def main():
    # 1. Initialize Configuration
    config = GlobalConfig()

    # 2. Welcome Message
    logger.info(f"Root Path: {config.baas_root}")

    # 3. Setup Logic
    try:
        if not config.General.launch:
            # Environment Setup
            env_mgr = EnvironmentManager(config)
            env_mgr.check_python()
            env_mgr.check_pip()
            env_mgr.check_pth()
            env_mgr.check_env_patch()

            # Repo Update
            updater = UpdateOrchestrator(config, env_mgr)
            updater.run()

            # Dependencies
            env_mgr.install_requirements()
            env_mgr.fix_shebangs()

        # 5. Launch
        launcher = AppLauncher(config)
        launcher.run_app()

    except Exception:
        logger.exception("Critical error during setup/launch.")
        Utils.error_tackle()


if __name__ == "__main__":
    main()
