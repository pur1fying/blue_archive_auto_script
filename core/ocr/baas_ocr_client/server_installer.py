import sys
import io
import shutil
import os
import platform
import subprocess
import time
from typing import Optional

import pygit2
from pygit2 import Commit
from pygit2.enums import ResetMode

# ================================
# Check the std::in and std::out Status before
# dulwich-related crashes, for dulwich will
# connect to the io, while the io is unset
# by the built window app.

if sys.stdin is None:
    sys.stdin = io.TextIOWrapper(io.BytesIO())
    sys.stdout = io.TextIOWrapper(io.BytesIO())
# ================================

from core.exception import OcrInternalError

if sys.platform not in ["win32", "linux", "darwin"]:
    raise Exception("Ocr Unsupported platform " + sys.platform)

OCR_SERVER_PREBUILD_URL = "https://gitee.com/pur1fy/baas_-cpp_prebuild.git"

SERVER_INSTALLER_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_BIN_DIR = os.path.join(SERVER_INSTALLER_DIR_PATH, "bin")

branch_map = {
    "win32": {"amd64": "windows-x64"},
    "linux": {"x86_64": "linux-x64"},
    "darwin": {"arm64": "macos-arm64"},
}
arch_map = branch_map[sys.platform]
arch = platform.machine().lower()
if arch not in arch_map:
    raise Exception("Unsupported machine architecture " + arch)
TARGET_BRANCH = arch_map[arch]


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
            repo = pygit2.Repository()
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
    manager = OcrRepoManager(SERVER_BIN_DIR, OCR_SERVER_PREBUILD_URL, TARGET_BRANCH, logger)
    manager.clone()
