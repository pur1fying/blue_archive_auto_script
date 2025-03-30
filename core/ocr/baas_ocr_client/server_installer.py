import sys
import os
from core.exception import OcrInternalError
from dulwich import porcelain
from dulwich.repo import Repo


if sys.platform not in ['win32', 'linux', 'darwin']:
    raise Exception("Ocr Unsupported platform " + sys.platform)

REPO_URL_HTTP = {
    'win32': "https://gitee.com/pur1fy/windows-compiled_baas_ocr_server.git",
    'linux': "https://gitee.com/pur1fy/linux-compiled_baas_ocr_server.git",
    'darwin': "https://gitee.com/pur1fy/mac-os_baas_ocr_server.git",
}

REPO_URL_HTTP = REPO_URL_HTTP[sys.platform]

SERVER_INSTALLER_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_BIN_DIR = os.path.join(SERVER_INSTALLER_DIR_PATH, 'bin')


def check_git(logger):
    if not os.path.exists(SERVER_BIN_DIR + '/.git'):
        logger.info("Installing Ocr Server, please wait...")
        for i in range(1, 4):
            try:
                porcelain.clone(REPO_URL_HTTP, SERVER_BIN_DIR)
                break
            except Exception as e:
                if i == 3:
                    raise OcrInternalError("Failed to install the BAAS_ocr_server. Please check your network")
                logger.error(f"Failed to install BAAS_ocr_server, retrying... {i}")
                logger.error(e.__str__())
        logger.info("Ocr Server Install success.")
    else:
        logger.info("Ocr Server Update check.")
        repo = Repo(SERVER_BIN_DIR)
        # Get local SHA
        local_sha = repo.head().decode('ascii')

        # Get remote SHA
        remote_refs = porcelain.ls_remote(REPO_URL_HTTP)
        remote_sha = remote_refs.get(b'refs/heads/main').decode('ascii')

        logger.info(f"remote_sha: {remote_sha}")
        logger.info(f"local_sha : {local_sha}")

        if local_sha == remote_sha:
            logger.info("Ocr Server No updates available.")
        else:
            logger.info("Pulling updates from the remote repository...")
            # Reset the local repository to the state of the remote repository
            porcelain.reset(repo, mode='hard')
            # Pull the latest changes from the remote repository
            for i in range(1, 4):
                try:
                    porcelain.pull(repo, REPO_URL_HTTP, 'main', protocol_version=0)
                    break
                except Exception as e:
                    if i == 3:
                        raise OcrInternalError("Failed to install the BAAS_ocr_server. Please check your network")
                    logger.error(f"Failed to update BAAS_ocr_server, retrying... {i}")
                    logger.error(e)
            updated_local_sha = repo.head().decode('ascii')
            if updated_local_sha == remote_sha:
                logger.info("Ocr Server Update success.")
            else:
                logger.warning(
                    "Failed to update the source code, please check your network or for conflicting files")
