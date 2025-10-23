import sys, io

# ================================
# Check the std::in and std::out Status before
# dulwich-related crashes, for dulwich will
# connect to the io, while the io is unset
# by the built window app.

if sys.stdin is None:
    sys.stdin = io.TextIOWrapper(io.BytesIO())
    sys.stdout = io.TextIOWrapper(io.BytesIO())
# ================================

import shutil
import os
from core.exception import OcrInternalError
from dulwich import porcelain
from dulwich.repo import Repo
import platform
from core.utils import is_android

if not is_android():
    if sys.platform not in ['win32', 'linux', 'darwin']:
        raise Exception("Ocr Unsupported platform " + sys.platform)

    OCR_SERVER_PREBUILD_URL = "https://gitee.com/pur1fy/baas_-cpp_prebuild.git"

    SERVER_INSTALLER_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
    SERVER_BIN_DIR = os.path.join(SERVER_INSTALLER_DIR_PATH, 'bin')

    branch = {
        'win32': {
            'amd64': 'windows-x64',
        },
        'linux': {
            'x86_64': 'linux-x64',
        },
        'darwin': {
            'arm64': 'macos-arm64',
        },
    }
    branch = branch[sys.platform]
    arch = platform.machine().lower()
    if arch not in branch:
        raise Exception("Unsupported machine architecture " + arch)
    branch = branch[arch]


def check_git(logger):
    if is_android():
        logger.info("Skip git check on Android")
        return
    if not os.path.exists(SERVER_BIN_DIR + '/.git'):
        clone_repo(logger)
    else:
        logger.info("Ocr Server Update check.")
        try:
            repo = Repo(SERVER_BIN_DIR)
            # Get local SHA
            local_sha = repo.head().decode('ascii')
        except Exception:
            logger.warning("Git Repo corrupted, remove .git folder and reinstall.")
            shutil.rmtree(SERVER_BIN_DIR + '/.git')
            clone_repo(logger)
            return
        # Get remote SHA
        remote_refs = porcelain.ls_remote(OCR_SERVER_PREBUILD_URL)
        remote_sha = remote_refs.get(b'refs/heads/' + branch.encode('ascii')).decode('ascii')

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
                    porcelain.pull(repo, OCR_SERVER_PREBUILD_URL, branch, protocol_version=0)
                    break
                except Exception as e:
                    if i == 3:
                        raise OcrInternalError("Failed to update the BAAS_ocr_server. Please check your network")
                    logger.error(f"Failed to update BAAS_ocr_server, retrying... {i}")
                    logger.error(e)
            updated_local_sha = repo.head().decode('ascii')
            if updated_local_sha == remote_sha:
                logger.info("Ocr Server Update success.")
            else:
                logger.warning("Failed to update the BAAS_ocr_server, please check your network.")


def clone_repo(logger):
    if is_android():
        logger.info("Skip git clone on Android")
        return
    logger.info("Installing Ocr Server, please hang on...")
    for i in range(1, 4):
        try:
            porcelain.clone(OCR_SERVER_PREBUILD_URL, SERVER_BIN_DIR, branch=branch)
            break
        except Exception as e:
            if i == 3:
                raise OcrInternalError("Failed to install the BAAS_ocr_server. Please check your network")
            logger.error(f"Failed to install BAAS_ocr_server, retrying... {i}")
            logger.error(e.__str__())
    logger.info("Ocr Server Install success.")
