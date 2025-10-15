import shutil
import sys
import os
import platform
import pygit2
from pygit2 import Commit

from core.exception import OcrInternalError
from pygit2.enums import ResetMode

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
branch = arch_map[arch]


def check_git(logger):
    """
    检查并更新 OCR Server 的本地 git 仓库
    """
    git_dir = os.path.join(SERVER_BIN_DIR, ".git")
    if not os.path.exists(git_dir):
        clone_repo(logger)
        return

    logger.info("Ocr Server Update check.")
    try:
        repo = pygit2.Repository(SERVER_BIN_DIR)
        local_sha = str(repo.head.target)
    except Exception:
        logger.warning("Git Repo corrupted, remove .git folder and reinstall.")
        shutil.rmtree(git_dir, ignore_errors=True)
        clone_repo(logger)
        return

    try:
        git = pygit2.Repository()
        remote = git.remotes.create_anonymous(OCR_SERVER_PREBUILD_URL)
        refs = {head.get("name"): head.get("oid") for head in remote.ls_remotes()}
        remote_sha = str(refs.get(f"refs/heads/{branch}", None))
    except Exception as e:
        raise OcrInternalError(f"Failed to fetch remote info: {e}")

    if not remote_sha:
        logger.warning(f"Remote branch '{branch}' not found.")
        return

    logger.info(f"remote_sha: {remote_sha}")
    logger.info(f"local_sha : {local_sha}")

    if local_sha == remote_sha:
        logger.info("Ocr Server No updates available.")
        return

    logger.info("Pulling updates from the remote repository...")

    try:
        remote_obj = (
            repo.remotes["origin"]
            if "origin" in list(repo.remotes.names())
            else repo.remotes.create("origin", OCR_SERVER_PREBUILD_URL)
        )
        refspec = f"refs/heads/{branch}:refs/remotes/origin/{branch}"
        remote_obj.fetch(refspecs=[refspec])
        remote_commit = repo.revparse_single(f"refs/remotes/origin/{branch}")
        if not isinstance(remote_commit, Commit):
            remote_commit = repo[remote_commit.target]
        repo.reset(remote_commit.id, ResetMode.HARD)
        repo.checkout_tree(remote_commit.tree)
        updated_sha = str(repo.head.target)

    except KeyError as ke:
        logger.error(f"Branch {branch} not found in remote repository.")
        raise OcrInternalError(f"Remote branch '{branch}' does not exist: {ke}")

    except Exception as e:
        logger.error("Failed to update the BAAS_ocr_server.")
        raise OcrInternalError(f"Update failed: {e}")

    if updated_sha == remote_sha:
        logger.info("Ocr Server Update success.")
    else:
        logger.warning("Failed to update the BAAS_ocr_server, please check your network.")


def clone_repo(logger):
    logger.info("Installing Ocr Server, please hang on...")

    if os.path.exists(SERVER_BIN_DIR) and os.listdir(SERVER_BIN_DIR):
        logger.warning("Target directory not empty, removing old files...")
        shutil.rmtree(SERVER_BIN_DIR)

    for i in range(1, 4):
        try:
            pygit2.clone_repository(
                OCR_SERVER_PREBUILD_URL,
                SERVER_BIN_DIR,
                checkout_branch=branch,
            )
            break
        except Exception as e:
            if i == 3:
                raise OcrInternalError("Failed to install the BAAS_ocr_server. Please check your network")
            logger.error(f"Failed to install BAAS_ocr_server, retrying... {i}")
            logger.error(str(e))

    logger.info("Ocr Server Install success.")
