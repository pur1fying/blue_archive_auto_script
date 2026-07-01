import sys
import io
import shutil
import os
import platform
import subprocess
import time
import tempfile
import zipfile
from typing import Optional

import pygit2
import requests
from pygit2 import Commit
from pygit2.enums import ResetMode

# ================================
# Check the std::in and std::out Status before
# Git library calls may touch stdio while the packaged window app
# leaves the streams unset.
# by the built window app.

if sys.stdin is None:
    sys.stdin = io.TextIOWrapper(io.BytesIO())
    sys.stdout = io.TextIOWrapper(io.BytesIO())
# ================================

from core.exception import OcrInternalError

if sys.platform not in ["win32", "linux", "darwin"]:
    raise Exception("Ocr Unsupported platform " + sys.platform)

OCR_SERVER_PREBUILD_URL = "https://gitee.com/pur1fy/baas_-cpp_prebuild.git"
OCR_SERVER_PREBUILD_ARCHIVE_URLS = [
    "https://baas-cdn.kiramei.workers.dev/https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://codeload.github.com/pur1fying/BAAS_Cpp_prebuild/zip/refs/heads/{branch}",
    "https://v4.gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://v6.gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://cdn.gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://gh.sevencdn.com/https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://githubfast.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
    "https://github.com/pur1fying/BAAS_Cpp_prebuild/archive/refs/heads/{branch}.zip",
]
OCR_SERVER_PREBUILD_API_URL = "https://api.github.com/repos/pur1fying/BAAS_Cpp_prebuild/branches/{branch}"

SERVER_INSTALLER_DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def _android_ocr_branch() -> Optional[str]:
    if os.getenv("BAAS_ANDROID", "").lower() not in {"1", "true", "yes", "on"}:
        return None
    arch = platform.machine().lower()
    if arch in {"aarch64", "arm64"}:
        return "android-arm64-v8a"
    if arch in {"x86_64", "amd64"}:
        return "android-x86_64"
    raise Exception("Unsupported Android machine architecture " + arch)


branch_map = {
    "win32": {"amd64": "windows-x64"},
    "linux": {"x86_64": "linux-x64"},
    "darwin": {"arm64": "macos-arm64"},
}
TARGET_BRANCH = _android_ocr_branch()
if TARGET_BRANCH is None:
    arch_map = branch_map[sys.platform]
    arch = platform.machine().lower()
    if arch not in arch_map:
        raise Exception("Unsupported machine architecture " + arch)
    TARGET_BRANCH = arch_map[arch]
SERVER_BIN_DIR = os.path.join(SERVER_INSTALLER_DIR_PATH, "bin-android", TARGET_BRANCH) if TARGET_BRANCH.startswith(
    "android-"
) else os.path.join(SERVER_INSTALLER_DIR_PATH, "bin")
ANDROID_VERSION_FILE = os.path.join(SERVER_BIN_DIR, ".baas-ocr-prebuild-sha")


def _is_android_runtime() -> bool:
    return os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}


def _android_library_abi_dir() -> str:
    if TARGET_BRANCH == "android-arm64-v8a":
        return "arm64-v8a"
    if TARGET_BRANCH == "android-x86_64":
        return "x86_64"
    raise OcrInternalError(f"Unsupported Android OCR branch: {TARGET_BRANCH}")


def _server_binary_path() -> str:
    if TARGET_BRANCH.startswith("android-"):
        return os.path.join(SERVER_BIN_DIR, "lib", _android_library_abi_dir(), "libBAAS_ocr_server.so")
    return os.path.join(SERVER_BIN_DIR, "BAAS_ocr_server.exe" if sys.platform == "win32" else "BAAS_ocr_server")


def _android_internal_runtime_root() -> str:
    internal_root = os.getenv("BAAS_ANDROID_INTERNAL_FILES_DIR", "").strip()
    if not internal_root:
        return ""
    return os.path.join(internal_root, "ocr-runtime", TARGET_BRANCH)


def _android_internal_binary_path() -> str:
    runtime_root = _android_internal_runtime_root()
    if not runtime_root:
        return ""
    return os.path.join(runtime_root, "lib", _android_library_abi_dir(), "libBAAS_ocr_server.so")


def _android_internal_version_file() -> str:
    runtime_root = _android_internal_runtime_root()
    if not runtime_root:
        return ""
    return os.path.join(runtime_root, ".baas-ocr-prebuild-sha")


def _read_android_installed_sha() -> str:
    try:
        with open(ANDROID_VERSION_FILE, "r", encoding="utf-8") as fp:
            return fp.read().strip()
    except OSError:
        return ""


def _read_android_internal_sha() -> str:
    version_file = _android_internal_version_file()
    if not version_file:
        return ""
    try:
        with open(version_file, "r", encoding="utf-8") as fp:
            return fp.read().strip()
    except OSError:
        return ""


def _get_android_remote_sha(branch: str) -> Optional[str]:
    try:
        response = requests.get(OCR_SERVER_PREBUILD_API_URL.format(branch=branch), timeout=15)
        response.raise_for_status()
        data = response.json()
        sha = data.get("commit", {}).get("sha")
        return str(sha) if sha else None
    except Exception:
        return None


def _download_android_archive(branch: str, archive_path: str, logger=None) -> str:
    last_error: Optional[Exception] = None
    for template in OCR_SERVER_PREBUILD_ARCHIVE_URLS:
        url = template.format(branch=branch)
        try:
            with requests.get(url, stream=True, timeout=(8, 90)) as response:
                response.raise_for_status()
                with open(archive_path, "wb") as fp:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            fp.write(chunk)
            return url
        except Exception as exc:
            last_error = exc
            if logger is not None:
                logger.warning(f"Failed to download Android OCR prebuild from {url}: {exc}")
    raise OcrInternalError(f"Failed to download Android OCR prebuild archive: {last_error}")


def _find_android_archive_root(extract_root: str) -> str:
    library_name = "libBAAS_ocr_server.so"
    for current_root, _dirs, files in os.walk(extract_root):
        if library_name in files and os.path.basename(current_root) == _android_library_abi_dir():
            return os.path.dirname(os.path.dirname(current_root))
    candidates = [
        os.path.join(extract_root, name)
        for name in os.listdir(extract_root)
        if os.path.isdir(os.path.join(extract_root, name))
    ]
    if len(candidates) == 1:
        return candidates[0]
    raise OcrInternalError("Android OCR prebuild archive does not contain libBAAS_ocr_server.so")


def _install_android_prebuild(logger) -> None:
    if not TARGET_BRANCH.startswith("android-"):
        raise OcrInternalError(f"Invalid Android OCR branch: {TARGET_BRANCH}")

    remote_sha = _get_android_remote_sha(TARGET_BRANCH)
    local_sha = _read_android_installed_sha()
    server_binary_path = _server_binary_path()
    internal_sha = _read_android_internal_sha()
    internal_binary_path = _android_internal_binary_path()
    if remote_sha and internal_sha == remote_sha and os.path.exists(internal_binary_path):
        logger.info("Android Ocr Server runtime already available.")
        return
    if not remote_sha and internal_sha and os.path.exists(internal_binary_path):
        logger.warning("Android OCR remote SHA unavailable; using internal runtime prebuild.")
        return
    if remote_sha and local_sha == remote_sha and os.path.exists(server_binary_path):
        logger.info("Ocr Server No updates available.")
        return
    if not remote_sha and local_sha and os.path.exists(server_binary_path):
        logger.warning("Android OCR remote SHA unavailable; using installed prebuild.")
        return

    logger.info(f"Installing Android Ocr Server prebuild for {TARGET_BRANCH}.")
    with tempfile.TemporaryDirectory(prefix="baas-ocr-android-") as tmp:
        archive_path = os.path.join(tmp, "ocr-prebuild.zip")
        source_url = _download_android_archive(TARGET_BRANCH, archive_path, logger)
        extract_root = os.path.join(tmp, "extract")
        os.makedirs(extract_root, exist_ok=True)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_root)
        source_root = _find_android_archive_root(extract_root)
        if os.path.exists(SERVER_BIN_DIR):
            shutil.rmtree(SERVER_BIN_DIR, ignore_errors=True)
        shutil.copytree(source_root, SERVER_BIN_DIR)

    if os.path.exists(server_binary_path):
        os.chmod(server_binary_path, os.stat(server_binary_path).st_mode | 0o755)
    else:
        raise OcrInternalError("Android OCR prebuild did not install libBAAS_ocr_server.so")

    with open(ANDROID_VERSION_FILE, "w", encoding="utf-8") as fp:
        fp.write(remote_sha or source_url)
    logger.info("Ocr Server Install success.")


class OcrRepoManager:
    """
    Manages the OCR Server git repository.
    Priority: System 'git' > pygit2 (except for rollback).
    """

    def __init__(self, repo_path: str, remote_url: str, branch: str, logger):
        self.repo_path = repo_path
        self.remote_url = remote_url
        self.branch = branch
        self.logger = logger
        self.git_executable = shutil.which("git")
        self.git_dir = os.path.join(repo_path, ".git")

    def _run_git_cmd(self, args: list, cwd: Optional[str] = None) -> str:
        """Executes a system git command."""
        if not self.git_executable:
            raise FileNotFoundError("System git not found")

        target_cwd = cwd if cwd else self.repo_path

        # Ensure directory exists before running command if not cloning
        if cwd is None and not os.path.exists(target_cwd):
            raise FileNotFoundError(f"Repo directory {target_cwd} does not exist")

        proc = subprocess.run(
            [self.git_executable] + args,
            cwd=target_cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return proc.stdout.strip()

    def get_local_sha(self) -> str:
        """Returns the SHA of the current local HEAD."""
        if self.git_executable:
            try:
                return self._run_git_cmd(["rev-parse", "HEAD"])
            except subprocess.CalledProcessError:
                self.logger.warning("System git failed to get local SHA, falling back to pygit2.")

        # Fallback to pygit2
        repo = pygit2.Repository(self.repo_path)
        return str(repo.head.target)

    def get_remote_sha(self) -> Optional[str]:
        """Returns the SHA of the target branch on the remote."""
        if self.git_executable:
            try:
                # git ls-remote <url> refs/heads/<branch>
                # Output: <SHA>\trefs/heads/<branch>
                ref = f"refs/heads/{self.branch}"
                output = self._run_git_cmd(["ls-remote", self.remote_url, ref], cwd=os.getcwd())
                if output:
                    return output.split()[0]
            except Exception as e:
                self.logger.warning(f"System git failed to get remote SHA: {e}")

        # Fallback to pygit2
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = pygit2.init_repository(tmp, bare=True)
                remote = repo.remotes.create_anonymous(self.remote_url)
                target_ref_name = f"refs/heads/{self.branch}"
                for head in remote.ls_remotes():
                    if head.get("name") == target_ref_name:
                        return str(head.get("oid"))
        except Exception as e:
            self.logger.error(f"pygit2 failed to get remote info: {e}")
            return None
        return None

    def clone(self) -> None:
        """Clones the repository."""
        if os.path.exists(self.repo_path):
            self.logger.warning("Target directory not empty, removing old files...")
            shutil.rmtree(self.repo_path, ignore_errors=True)

        for i in range(1, 4):
            try:
                if self.git_executable:
                    self.logger.info(f"Cloning with system git (Attempt {i})...")
                    # git clone -b <branch> <url> <path>
                    self._run_git_cmd(
                        ["clone", "-b", self.branch, self.remote_url, self.repo_path],
                        cwd=os.path.dirname(self.repo_path)
                    )
                else:
                    self.logger.info(f"Cloning with pygit2 (Attempt {i})...")
                    pygit2.clone_repository(
                        self.remote_url,
                        self.repo_path,
                        checkout_branch=self.branch,
                    )
                self.logger.info("Ocr Server Install success.")
                return
            except Exception as e:
                self.logger.error(f"Failed to clone (Attempt {i}): {e}")
                if i == 3:
                    raise OcrInternalError("Failed to install the BAAS_ocr_server. Please check your network")
                time.sleep(1)

    def update(self) -> None:
        """Updates the repository to the latest remote state."""
        self.logger.info("Pulling updates from the remote repository...")

        if self.git_executable:
            try:
                # 1. Fetch
                self._run_git_cmd(["fetch", "origin", self.branch])
                # 2. Reset --hard
                # We use FETCH_HEAD to ensure we are at the exact state we just fetched
                self._run_git_cmd(["reset", "--hard", "FETCH_HEAD"])
                self.logger.info("Ocr Server Update success (System Git).")
                return
            except Exception as e:
                self.logger.error(f"System git update failed: {e}. Falling back to pygit2.")

        # Fallback to pygit2
        try:
            repo = pygit2.Repository(self.repo_path)
            # Ensure remote exists
            remote = repo.remotes["origin"] if "origin" in repo.remotes.names() else repo.remotes.create("origin",
                                                                                                         self.remote_url)

            refspec = f"refs/heads/{self.branch}:refs/remotes/origin/{self.branch}"
            remote.fetch(refspecs=[refspec])

            remote_ref = f"refs/remotes/origin/{self.branch}"
            remote_commit = repo.revparse_single(remote_ref)

            if not isinstance(remote_commit, Commit):
                remote_commit = repo[remote_commit.target]

            repo.reset(remote_commit.id, ResetMode.HARD)
            repo.checkout_tree(remote_commit.tree)
            self.logger.info("Ocr Server Update success (pygit2).")
        except Exception as e:
            self.logger.error("Failed to update the BAAS_ocr_server.")
            raise OcrInternalError(f"Update failed: {e}")



def check_git(logger):
    """
    Main entry point to check and update the OCR Server repo.
    """
    if _is_android_runtime():
        _install_android_prebuild(logger)
        return

    manager = OcrRepoManager(SERVER_BIN_DIR, OCR_SERVER_PREBUILD_URL, TARGET_BRANCH, logger)

    # 1. Ensure Repo Exists
    if not os.path.exists(manager.git_dir):
        manager.clone()
        return

    logger.info("Ocr Server Update check.")

    # 2. Validate Local Repo Integrity
    try:
        local_sha = manager.get_local_sha()
    except Exception:
        logger.warning("Git Repo corrupted, remove .git folder and reinstall.")
        shutil.rmtree(manager.git_dir, ignore_errors=True)
        manager.clone()
        return

    # 3. Check Remote
    try:
        remote_sha = manager.get_remote_sha()
    except Exception as e:
        raise OcrInternalError(f"Failed to fetch remote info: {e}")

    if not remote_sha:
        logger.warning(f"Remote branch '{TARGET_BRANCH}' not found.")
        return

    logger.info(f"remote_sha: {remote_sha}")
    logger.info(f"local_sha : {local_sha}")

    # 4. Update if necessary
    if local_sha == remote_sha:
        logger.info("Ocr Server No updates available.")
        return

    # Perform update (System git preferred, pygit2 fallback)
    manager.update()

    # Verify update
    try:
        new_local_sha = manager.get_local_sha()
        if new_local_sha != remote_sha:
            logger.warning("Failed to update the BAAS_ocr_server (SHA mismatch), please check your network.")
    except Exception:
        pass


def clone_repo(logger):
    """
    Wrapper for cloning the repo.
    """
    logger.info("Installing Ocr Server, please hang on...")
    if _is_android_runtime():
        _install_android_prebuild(logger)
        return

    manager = OcrRepoManager(SERVER_BIN_DIR, OCR_SERVER_PREBUILD_URL, TARGET_BRANCH, logger)
    manager.clone()
