import sys
import os
from dulwich import porcelain
from dulwich.repo import Repo

REPO_URL_HTTP = None
if sys.platform == 'win32':
    REPO_URL_HTTP = "https://gitee.com/pur1fy/windows-compiled_baas_ocr_server.git"

SERVER_INSTALLER_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_BIN_DIR = os.path.join(SERVER_INSTALLER_DIR_PATH, 'bin')


def check_git(logger):
    if not os.path.exists(SERVER_BIN_DIR + '/.git'):
        logger.info("Installing Ocr Server, please wait...")
        porcelain.clone(REPO_URL_HTTP, SERVER_BIN_DIR)
        logger.info("Install success")
    else:
        logger.info("Ocr Server Update check")
        repo = Repo(SERVER_BIN_DIR)
        # Get local SHA
        local_sha = repo.head().decode('ascii')

        # Get remote SHA
        remote_refs = porcelain.ls_remote(REPO_URL_HTTP)
        remote_sha = remote_refs.get(b'refs/heads/main').decode('ascii')

        logger.info(f"remote_sha: {remote_sha}")
        logger.info(f"local_sha: {local_sha}")

        if local_sha == remote_sha:
            logger.info("No updates available")
        else:
            logger.info("Pulling updates from the remote repository...")
            # Reset the local repository to the state of the remote repository
            porcelain.reset(repo, mode='hard')
            # Pull the latest changes from the remote repository
            porcelain.pull(repo, REPO_URL_HTTP, 'master', protocol_version=0)
            updated_local_sha = repo.head().decode('ascii')
            if updated_local_sha == remote_sha:
                logger.info("Update success")
            else:
                logger.warning(
                    "Failed to update the source code, please check your network or for conflicting files")
