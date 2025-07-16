# -*- coding: utf-8 -*-
import stat
import time

import pygit2

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

import os
import gc
import re
import sys
import shutil
import zipfile
import tempfile
import platform
import subprocess
from enum import Enum, auto
from pathlib import Path

import psutil
import getpass
import requests
import tomli_w
from copy import deepcopy
from alive_progress import alive_bar
# from dulwich import porcelain
# from dulwich.repo import Repo
from easydict import EasyDict as eDict
from halo import Halo
from loguru import logger

from pygit2 import clone_repository, Repository, RemoteCallbacks, GIT_RESET_HARD, GitError

from toml_config import TOML_Config
from mirrorc_update.mirrorc_updater import MirrorC_Updater
from const import GetShaMethod, get_remote_sha_methods

__system__ = platform.system()
__env__ = os.environ.copy()
if __system__ == "Windows":
    __env__["PYTHONPATH"] = '.env;.venv/Lib;.venv/Scripts;.venv;.;.venv/Lib/site-packages'

os.environ["PDM_IGNORE_ACTIVE_VENV"] = "1"

# ==================== Default Settings =====================

DEFAULT_SETTINGS = {
    "General": {
        "mirrorc_cdk": "",
        "current_BAAS_version": "",
        "current_BAAS_Cpp_version": "",
        "get_remote_sha_method": "",
        "dev": False,
        "refresh": False,
        "launch": False,
        "force_launch": False,
        "internal_launch": False,
        "no_build": True,
        "debug": False,
        "use_dynamic_update": False,
        "source_list": [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.ustc.edu.cn/pypi/web/simple",
            "https://mirrors.aliyun.com/pypi/simple",
            "https://pypi.doubanio.com/simple",
            "https://mirrors.huaweicloud.com/repository/pypi/simple",
            "https://mirrors.cloud.tencent.com/pypi/simple",
            "https://mirrors.163.com/pypi/simple",
            "https://pypi.python.org/simple",
            "https://pypi.org/simple",
        ],
        "package_manager": "pip",
        "runtime_path": "default",
        "linux_pwd": "",
    },
    "URLs": {
        "REPO_URL_HTTP": "https://gitee.com/pur1fy/blue_archive_auto_script.git",
        "GET_PIP_URL": "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py",
        "GET_UPX_URL": "https://ghp.ci/https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip",
        "GET_ENV_PATCH_URL": "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/env_patch.zip",
        "GET_PYTHON_URL": "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip",
    },
    "Paths": {
        "BAAS_ROOT_PATH": "",
        "TMP_PATH": "tmp",
        "TOOL_KIT_PATH": "toolkit",
    },
}


repo = None
# local version
local_sha = None
# latest version
remote_sha = None
update_type = None
mirrorc_cdk = None
latest_mirrorc_return = None
mirrorc_inst = MirrorC_Updater(app="BAAS_repo", current_version="")


class Utils:

    @staticmethod
    def on_rm_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWUSR)
            func(path)
        except Exception as e:
            pass

    @staticmethod
    def mirrorc_api_get_latest_sha():
        global mirrorc_inst
        global mirrorc_cdk
        global latest_mirrorc_return
        try:
            latest_mirrorc_return = mirrorc_inst.get_latest_version(cdk=mirrorc_cdk)
            if latest_mirrorc_return.has_data:
                return latest_mirrorc_return.latest_version_name
            else:
                logger.error(f"[MirrorC Api] get SHA error: {latest_mirrorc_return.message}")
        except Exception as e:
            logger.error(f"[MirrorC Api] get SHA error: {e}")
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
    def pygit2_get_latest_sha(data):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = pygit2.init_repository(tmp_dir, bare=True)

        url = data["url"]
        branch = data["branch"]
        remote = repo.remotes.create_anonymous(url)
        try:
            remote_refs = remote.ls_remotes()
        except pygit2.GitError as e:
            logger.warning(f"[PyGit2] get SHA error: {e}")
            return None
        target_ref = f"refs/heads/{branch}"
        for ref in remote_refs:
            if ref["name"] == target_ref:
                return str(ref["oid"])
        return None

    @staticmethod
    def get_remote_sha():
        logger.info("<<< Get Remote SHA >>>")
        if G.get_remote_sha_method:
            index = next(
                (i for i, item in enumerate(get_remote_sha_methods) if item.get("name") == G.get_remote_sha_method),
                None)
            if index is not None:
                sha = Utils.get_remote_sha_once(get_remote_sha_methods[index])
                if sha is not None:
                    return sha
                get_remote_sha_methods.pop(index)
        for method in get_remote_sha_methods:
            sha = Utils.get_remote_sha_once(method)
            if sha is not None:
                logger.info(f"Set get remote SHA method --> [ {method['name']} ]")
                config.set_and_save("General.get_remote_sha_method", method["name"])
                return sha
        logger.error("Failed to get remote SHA from all methods.")
        raise Exception("Failed to get remote SHA.")

    @staticmethod
    def get_remote_sha_once(method):
        logger.info(f"[ {method['name']} ] get latest SHA.")
        if method["method"] == GetShaMethod.GITHUB_API:
            return Utils.github_api_get_latest_sha(method)
        elif method["method"] == GetShaMethod.PYGIT2:
            return Utils.pygit2_get_latest_sha(method)
        elif method["method"] == GetShaMethod.MIRRORC_API:
            return Utils.mirrorc_api_get_latest_sha()
        else:
            return None

    @staticmethod
    def download_file(url: str, parent_path: Path) -> Path:
        filename = url.split("/")[-1]
        logger.info(f"Prepare for downloading {filename}")
        response = requests.get(url, stream=True)
        file_path = parent_path / filename
        total_size = int(response.headers.get("Content-Length", 0))

        with alive_bar(
                total_size, unit="B", bar="smooth", title=f"Downloading {filename} "
        ) as progress_bar:
            with open(file_path, "wb") as download_f:
                for chunk in response.iter_content(chunk_size=1024):
                    if not chunk:
                        continue
                    download_f.write(chunk)
                    progress_bar(len(chunk))

        logger.success(f"Downloaded {filename} to {file_path}")

        return file_path

    @staticmethod
    def unzip_file(zip_dir, out_dir):
        with zipfile.ZipFile(zip_dir, "r") as zip_ref:
            # Unzip all files to the current directory
            zip_ref.extractall(path=out_dir)
            logger.success(f"{zip_dir} unzip success.")
            logger.success(f"output --> {out_dir}")

    @staticmethod
    def sudo(cmd, pwd):
        os.system(f"echo {pwd} | sudo -S {cmd}")

    @staticmethod
    def copy_directory_structure(source: Path, target: Path):
        target.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            relative_path = item.relative_to(source)
            target_path = target / relative_path
            if item.is_dir():
                target_path.mkdir(exist_ok=True)
                Utils.copy_directory_structure(item, target_path)
            elif item.is_file():
                shutil.copy2(item, target_path)

# ==================== System check ====================
if __system__ not in ["Windows", "Linux"]:
    raise Exception(
        f"Unsupported OS: {__system__}. Currently only Windows and Linux are supported."
    )

# ==================== Config Processing ====================
if getattr(sys, "frozen", False):
    BASE_PATH = Path(sys.argv[0]).resolve().parent
else:
    BASE_PATH = Path(__file__).resolve().parent

if __system__ == "Linux":
    BASE_PATH = Path("~").expanduser() / ".baas"

if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)

# Find the configuration file in the current directory
config_file = BASE_PATH / "setup.toml"
if not config_file.exists():

    # If not found, create a default configuration file
    with open(config_file, "wb") as file:
        if __system__ == "Linux":
            print(
                "Since it's your first time running the script, we require password for installing packages."
            )
            print(
                "Don't worry, we won't use it for any other purposes. (You may check the source code)"
            )
            pwd = getpass.getpass("Please enter your password: ")
            DEFAULT_SETTINGS["General"]["linux_pwd"] = pwd
        tomli_w.dump(DEFAULT_SETTINGS, file)
# Load the configuration file
with open(config_file, "rb") as file:
    config = TOML_Config(config_file)

config_modified = False

def insert_new_config(cfg, new):
    global config_modified
    for key, value in new.items():
        if key not in cfg:
            config_modified = True
            cfg[key] = value
        if isinstance(value, dict):
            insert_new_config(cfg[key], value)

insert_new_config(config.config, DEFAULT_SETTINGS)
if config_modified:
    config.save()

G = eDict(config.get("General"))
U = eDict(config.get("URLs"))
P = eDict(config.get("Paths"))

BAAS_ROOT_PATH = Path(P.BAAS_ROOT_PATH).resolve() if P.BAAS_ROOT_PATH else "" or BASE_PATH
G.runtime_path = G.runtime_path.replace("\\", "/")
P.TMP_PATH = BAAS_ROOT_PATH / Path(P.TMP_PATH)
P.TOOL_KIT_PATH = BAAS_ROOT_PATH / Path(P.TOOL_KIT_PATH)
mirrorc_cdk = G.mirrorc_cdk

if P.BAAS_ROOT_PATH and not os.path.exists(P.BAAS_ROOT_PATH):
    os.makedirs(P.BAAS_ROOT_PATH)
if not os.path.exists(P.TMP_PATH):
    os.makedirs(P.TMP_PATH)
if not os.path.exists(P.TOOL_KIT_PATH):
    os.makedirs(P.TOOL_KIT_PATH)

# ==================== Logging Configuration ====================

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO",
)

logger.add(
    BAAS_ROOT_PATH / "log" / "installer.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)

spinner = Halo()

# ==================== Welcome Message ====================
logger.info("Blue Archive Auto Script Launcher & Installer")
logger.info("GitHub Repo: https://github.com/pur1fying/blue_archive_auto_script")
logger.info("Official QQ Group: 658302636")
logger.info("Current BAAS Path: " + str(BAAS_ROOT_PATH))


def check_python_installation():
    try:
        # Try to run the 'python' command to get version information
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Python is installed: {result.stdout.strip()}")
            return "python"
    except FileNotFoundError:
        pass

    try:
        # Try to run the 'python3' command to get version information
        result = subprocess.run(
            ["python3", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info(f"Python 3 is installed: {result.stdout.strip()}")
            return "python3"
    except FileNotFoundError:
        pass

    # If both checks fail, Python is not installed
    logger.info("Python is not installed on this system.")
    return None


def install_package():
    try:
        env_pip_exec = None

        # Detect the OS and select the appropriate Python executable and path
        def try_sources(pkg_mgr_path, followed_cmd=None):
            for _source in G.source_list:
                try:
                    _followed_cmd = deepcopy(followed_cmd)
                    if G.package_manager == "pdm":
                        subprocess.run(
                            [pkg_mgr_path, "config", "--local", "pypi.url", _source],
                            check=True,
                        )
                    else:
                        _followed_cmd.extend(["-i", _source])
                    if _followed_cmd:
                        if not type(pkg_mgr_path) == list:
                            cmds = [pkg_mgr_path, *_followed_cmd]
                        else:
                            cmds = deepcopy(pkg_mgr_path)
                            cmds.extend(_followed_cmd)
                        subprocess.run(cmds,
                                       env=__env__,
                                       check=True)
                    return
                except KeyboardInterrupt:
                    logger.error("User interrupted the process.")
                    return
                except:
                    logger.exception(f"Failed to connect to {_source}, trying next source...")
            logger.error("Packages Installation failed with all sources.")
            error_tackle()

        if G.runtime_path == "default":

            # If Linux, don't create a virtual environment
            if __system__ == "Linux":
                mgr_path = BAAS_ROOT_PATH / ".env/bin/pdm"
                if G.package_manager == "pip":
                    mgr_path = BAAS_ROOT_PATH / ".env/bin/pip"
                    Utils.sudo(f"chown -R $(whoami) {BAAS_ROOT_PATH}", G.linux_pwd)
                    try_sources(
                        mgr_path,
                        [
                            "install",
                            "-r",
                            BAAS_ROOT_PATH / "requirements-linux.txt",
                            "--no-warn-script-location",
                        ],
                    )
                else:
                    try_sources(mgr_path, ["install", "-p", BAAS_ROOT_PATH])
                return

            python_exec_file = BAAS_ROOT_PATH / ".env/python.exe"
            env_pip_exec = [str(python_exec_file), '-m', 'pip']

            if (
                    not os.path.exists(BAAS_ROOT_PATH / ".venv")
                    and G.package_manager == "pip"
            ):
                # Install virtualenv package
                cmd_list = ["install", "virtualenv", "--no-warn-script-location"]

                try_sources(
                    env_pip_exec,
                    cmd_list,
                )
                subprocess.run(
                    [
                        str(python_exec_file),
                        "-m",
                        "virtualenv",
                        BAAS_ROOT_PATH / ".venv",
                    ],
                    check=True,
                )
            env_pip_exec[0] = BAAS_ROOT_PATH / ".venv/Scripts/python.exe"

        if not env_pip_exec:
            env_python_exec = G.runtime_path
            env_pip_exec = (env_python_exec + " -m pip").split(" ")

        try_sources(
            env_pip_exec,
            [
                "install",
                "-r",
                str(BAAS_ROOT_PATH / "requirements.txt"),
                "--no-warn-script-location",
            ],
        )

        logger.success("Packages installed successfully")

    except:
        logger.exception(f"Failed to install packages!")
        return False


def check_pth():
    if __system__ == "Linux":
        return
    if os.path.exists(BAAS_ROOT_PATH / ".venv"):
        return
    logger.info("Checking pth file...")
    read_file = []
    with open(BAAS_ROOT_PATH / ".env/python39._pth", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("#import site"):
                line = line.replace("#", "")
            read_file.append(line)
    with open(BAAS_ROOT_PATH / ".env/python39._pth", "w", encoding="utf-8") as f:
        f.writelines(read_file)


def start_app():
    if G.runtime_path == "default":
        _path = (
            BAAS_ROOT_PATH / ".venv/Scripts/pythonw.exe"
            if __system__ == "Windows"
            else (
                BAAS_ROOT_PATH / ".venv/bin/python3"
                if G.package_manager == "pdm"
                else BAAS_ROOT_PATH / ".env/bin/python3"
            )
        )
        _path = (
            BAAS_ROOT_PATH / ".venv/Scripts/python"
            if G.debug and __system__ == "Windows"
            else _path
        )
    else:
        _path = G.runtime_path

    if __system__ == "Linux":
        if G.runtime_path == "default":
            __env__["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(
                BAAS_ROOT_PATH
                / ".env/lib/python3.9/site-packages/PyQt5/Qt5/plugins/platforms"
            )
        proc = subprocess.run(
            [_path, str(BAAS_ROOT_PATH / "window.py")],  # 直接用列表传递命令
            cwd=BAAS_ROOT_PATH,  # 先 cd 到 BAAS_ROOT_PATH
            env=__env__  # 传递修改后的环境变量
        )
        return proc.returncode
    else:
        proc = subprocess.Popen(
            [_path, str(BAAS_ROOT_PATH / "window.py")],  # 直接用列表传递命令
            cwd=BAAS_ROOT_PATH,  # 先 cd 到 BAAS_ROOT_PATH
            env=__env__,  # 传递修改后的环境变量
        )
    logger.info(f"Started process with PID: {proc.pid}")
    return proc.pid


def run_app():
    logger.info("Start to run the app...")
    try:  # record pid
        with open(BAAS_ROOT_PATH / "pid", "a+") as f:
            f.seek(0)
            try:
                last_pid = int(f.read())
            except:
                last_pid = 2147483647
            if psutil.pid_exists(last_pid):
                if not G.force_launch:
                    logger.info(
                        "App already started. Killing."
                    )  # close existing BAAS
                    p = psutil.Process(last_pid)
                    try:
                        p.terminate()
                    except:
                        os.system(f"taskkill /f /pid {last_pid}")
                else:
                    with open(BAAS_ROOT_PATH / "pid", "w+") as _f:
                        _f.write(str(start_app()))
                    logger.success("Start app success.")
            f.close()
            with open(BAAS_ROOT_PATH / "pid", "w+") as _f:
                _f.write(str(start_app()))
                logger.success("Start app success.")
                _f.close()

    except Exception:
        logger.exception("Run app failed")
        error_tackle()

    if __system__ == "Windows" and not G.no_build:
        try:
            import PyInstaller.__main__

            check_upx()

            def create_executable():
                PyInstaller.__main__.run(
                    [
                        str(BAAS_ROOT_PATH / "installer.py"),
                        "--name=BlueArchiveAutoScript",
                        "--onefile",
                        "--icon=gui/assets/logo.ico",
                        "--noconfirm",
                        "--upx-dir",
                        "./toolkit/upx-4.2.4-win64",
                    ]
                )

            if os.path.exists(BAAS_ROOT_PATH / "backup.exe") and not os.path.exists(
                    BAAS_ROOT_PATH / "no_build"
            ):
                create_executable()
                logger.info("try to remove the backup executable file.")
                try:
                    os.remove(BAAS_ROOT_PATH / "backup.exe")
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
            error_tackle()


def error_tackle():
    logger.info(
        "Now you can turn off this command line window safely or report this issue to developers."
    )
    logger.info("现在您可以安全地关闭此命令行窗口或向开发者上报问题。")
    logger.info("您现在可以安全地关闭此命令行窗口或向开发人员报告此问题。")
    logger.info(
        "今、このコマンドラインウィンドウを安全に閉じるか、この問題を開発者に報告することができます。"
    )
    logger.info(
        "이제 이 명령줄 창을 안전하게 종료하거나 이 문제를 개발자에게 보고할 수 있습니다。"
    )
    os.system("pause")
    sys.exit()


def check_requirements():
    logger.info("Check package Installation...")
    install_package()
    logger.success("Install requirements success")


def check_pdm():
    raise NotImplementedError("PDM currently not supported.")
    # if os.path.exists(BAAS_ROOT_PATH / ".venv"):
    #     logger.info("Already installed pdm.")
    #     return
    #
    # logger.info("Checking pdm installation...")
    # if __system__ == "Linux":
    #     if os.path.exists(BAAS_ROOT_PATH / ".env/bin/pdm"):
    #         return
    #     subprocess.run([BAAS_ROOT_PATH / ".env/bin/pip3", "install", "pdm"], check=True)
    #     return
    #
    # assert __system__ == "Windows"
    # if not os.path.exists(BAAS_ROOT_PATH / ".env/Scripts/pip.exe"):
    #     logger.warning("Pip is not installed, trying to install pip...")
    #     filepath = Utils.download_file(U.GET_PIP_URL, P.TMP_PATH)
    #     subprocess.run([BAAS_ROOT_PATH / ".env/python.exe", filepath])
    #
    # if not os.path.exists(BAAS_ROOT_PATH / ".env/Scripts/pdm.exe"):
    #     logger.warning("Pdm is not installed, trying to install pdm...")
    #     subprocess.run([BAAS_ROOT_PATH / ".env/Scripts/pip.exe", "install", "pdm"])


def check_pip():
    logger.info("Checking pip installation...")
    if __system__ == "Linux":
        return

    assert __system__ == "Windows"
    if not os.path.exists(BAAS_ROOT_PATH / ".env/Scripts/pip.exe"):
        logger.warning("Pip is not installed, trying to install pip...")
        filepath = Utils.download_file(U.GET_PIP_URL, P.TMP_PATH)
        subprocess.run([BAAS_ROOT_PATH / ".env/python.exe", filepath])


def check_python():
    logger.info("Checking python installation...")
    if os.path.exists(BAAS_ROOT_PATH / ".venv"):
        return
    # Platform-specific Python installation check
    _path = ""
    if __system__ == "Windows":
        _path = BAAS_ROOT_PATH / ".env/python.exe"
    elif __system__ == "Linux":
        _path = BAAS_ROOT_PATH / ".env/bin/python3"

    if not os.path.exists(_path):
        logger.info("Python environment is not installed, trying to install python...")
        if __system__ == "Windows":
            filepath = Utils.download_file(U.GET_PYTHON_URL, P.TMP_PATH)
            Utils.unzip_file(filepath, BAAS_ROOT_PATH / ".env")
            os.remove(filepath)
        elif __system__ == "Linux":
            # For Ubuntu, other Linux distributions may need to be modified
            Utils.sudo("add-apt-repository ppa:deadsnakes/ppa", G.linux_pwd)
            Utils.sudo("apt update", G.linux_pwd)
            Utils.sudo("apt-get install python3.9-venv -y", G.linux_pwd)
            Utils.sudo(f"python3.9 -m venv {BAAS_ROOT_PATH / '.env'}", G.linux_pwd)


def check_upx():
    logger.info("Checking UPX installation.")
    if not os.path.exists("toolkit/upx-4.2.4-win64/upx.exe"):
        filepath = Utils.download_file(U.GET_UPX_URL, P.TMP_PATH)
        Utils.unzip_file(filepath, P.TOOL_KIT_PATH)
        os.remove(filepath)


def check_env_patch():
    if __system__ == "Linux":
        return
    if os.path.exists(BAAS_ROOT_PATH / ".env/Lib/site-packages/Polygon"):
        return
    logger.info("Downloading env patch...")
    filepath = Utils.download_file(U.GET_ENV_PATCH_URL, P.TMP_PATH)
    Utils.unzip_file(filepath, BAAS_ROOT_PATH / ".env")


def fix_exe_shebangs(search_dir=".venv\\Scripts"):
    """
    Scan all .exe files under the given directory and replace any shebang line
    like '#!<any_path>\\.venv\\Scripts\\python.exe' with '#!python.exe',
    while preserving the original file size by padding with spaces.
    Backup files are saved to '__exe_backups__'.
    """
    backup_dir = ".venv/__exe_backups__"
    os.makedirs(backup_dir, exist_ok=True)

    # Regex to match any shebang line ending with .venv\Scripts\python.exe
    pattern = re.compile(rb'#!.*?\\.venv\\Scripts\\python\.exe')
    replacement = b"#!python.exe"

    # Collect all .exe files under the search directory
    exe_files = []
    for root, _, files in os.walk(search_dir):
        for filename in files:
            if filename.lower().endswith(".exe"):
                exe_files.append(os.path.join(root, filename))

    modified_count = 0

    with alive_bar(len(exe_files), title="Fixing .exe shebangs") as bar:
        for full_path in exe_files:
            bar()
            try:
                with open(full_path, "rb") as f:
                    content = f.read()

                match = pattern.search(content)
                if not match:
                    continue

                matched_bytes = match.group(0)
                padding_len = len(matched_bytes) - len(replacement)
                if padding_len < 0:
                    logger.warning(f"Skipped (replacement too long): {full_path}")
                    continue

                replacement_padded = replacement + b' ' * padding_len
                new_content = content.replace(matched_bytes, replacement_padded, 1)

                # Construct backup path
                rel_path = os.path.relpath(full_path, search_dir)
                backup_path = os.path.join(backup_dir, rel_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                # Save backup
                with open(backup_path, "wb") as f:
                    f.write(content)

                # Overwrite original file
                with open(full_path, "wb") as f:
                    f.write(new_content)

                modified_count += 1

            except:
                logger.exception(f"Failed to process {full_path}: {e}")

    logger.success(f"Finished. {modified_count} .exe file(s) patched.")
    if modified_count > 0:
        logger.info(f"Backups saved to: {os.path.abspath(backup_dir)}")
    else:
        logger.info("No matching shebangs were found in .exe files.")


class BAASGitCallbacks(RemoteCallbacks):
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
            # Create the progress bar generator
            bar_gen = alive_bar(stats.total_objects, title="Cloning repository...")
            self.bar_ref["bar_gen"] = bar_gen
            self.bar_ref["bar"] = bar_gen.__enter__()  # Enter the context

        if self.bar_ref.get("bar"):
            self.received_count = stats.received_objects
            self.bar_ref["bar"](self.received_count - self.current_count)  # Advance the progress bar by one
            self.current_count = self.received_count

        if self.received_count == stats.total_objects:
            self.bar_ref["bar_gen"].__exit__(None, None, None)
            self.spinner.start()


def clone_repo(repo_url, local_path):
    bar_ref = {"bar": None}
    callbacks = BAASGitCallbacks(bar_ref)
    repo = clone_repository(repo_url, local_path, callbacks=callbacks)
    callbacks.spinner.stop()
    logger.success("Cloning completed successfully.")
    return repo


def repair_broken_git_repo():
    global repo
    del repo
    # repo = None
    gc.collect()

    # Remove the existing .git directory
    git_dir = BAAS_ROOT_PATH / ".git"
    if git_dir.exists():
        logger.info("Removing broken Git repository...")
        shutil.rmtree(git_dir, ignore_errors=True)

    logger.warning("Attempting to repair invalid Git repo...")

    temp_clone_path = BAAS_ROOT_PATH / "temp_clone"

    # Remove any existing temp_clone directory
    if temp_clone_path.exists():
        shutil.rmtree(temp_clone_path, ignore_errors=True)

    # Clone the repository to a temporary directory
    logger.info("Cloning fresh repo to temporary directory...")
    repo = clone_repo(U.REPO_URL_HTTP, str(temp_clone_path))

    # Release the occupation of the directory
    del repo
    # repo = None
    gc.collect()

    # Move the cloned repository to the desired location
    for item in temp_clone_path.iterdir():
        dst = BAAS_ROOT_PATH / item.name
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst, ignore_errors=True)
            else:
                dst.unlink()
        shutil.move(str(item), str(dst))

    shutil.rmtree(temp_clone_path, ignore_errors=True)
    logger.success("Git repository successfully repaired.")


def git_install_baas():
    logger.info("+--------------------------------+")
    logger.info("|       GIT INSTALL BAAS         |")
    logger.info("+--------------------------------+")
    logger.info("Cloning the repository...")

    temp_clone_path = BAAS_ROOT_PATH / "temp_clone"

    if temp_clone_path.exists():
        logger.info("Removing temp_clone directory...")
        shutil.rmtree(str(temp_clone_path), ignore_errors=False, onerror=Utils.on_rm_error)

    # Clone the repository using pygit2
    repo = clone_repo(
        U.REPO_URL_HTTP,
        str(temp_clone_path),
    )

    # Release the occupation of the directory
    del repo
    # repo = None
    gc.collect()

    # Move the cloned repository to the desired location
    Utils.copy_directory_structure(temp_clone_path, BAAS_ROOT_PATH)

    # Remove temporary clone directory
    shutil.rmtree(str(temp_clone_path), ignore_errors=False, onerror=Utils.on_rm_error)
    logger.success("Git Install Success!")

def check_repo_url(_repo):
    origin = _repo.remotes["origin"]
    logger.info("<<< Repo Remote URL >>>")
    logger.info(origin.url)
    if origin.url != U.REPO_URL_HTTP:
        logger.info("<<< Switch Remote Repo URL >>>")
        logger.info(U.REPO_URL_HTTP)
        _repo.remotes.delete("origin")
        new_origin = _repo.remotes.create("origin", U.REPO_URL_HTTP)
        for ref in list(_repo.references):
            if ref.startswith("refs/remotes/origin/"):
                _repo.references.delete(ref)
        new_origin.fetch()
        for branch in _repo.branches.local:
            local_branch = _repo.lookup_branch(branch)
            remote_branch_name = f"origin/{branch}"

            if remote_branch_name in _repo.branches.remote:
                remote_branch = _repo.lookup_branch(remote_branch_name, pygit2.GIT_BRANCH_REMOTE)
                local_branch.upstream = remote_branch
        logger.success("Remote repo url switched.")

def git_update_baas():
    global local_sha
    global remote_sha
    global repo
    logger.info("+--------------------------------+")
    logger.info("|        GIT UPDATE BAAS         |")
    logger.info("+--------------------------------+")
    try:
        repo = Repository(str(BAAS_ROOT_PATH))
        check_repo_url(repo)
        refresh_required = G.refresh
        if refresh_required:
            logger.info("You've selected dropping all changes for the project file.")

        spinner.start("Pulling updates from the remote repository...")

        # Reset local branch to remote
        repo.reset(repo.lookup_reference("refs/remotes/origin/master").target, GIT_RESET_HARD)

        # Checkout to master (HEAD points to refs/heads/master)
        repo.checkout("refs/heads/master")
        # str(repo.references.get("refs/remotes/origin/master").target)
        local_sha = str(repo.head.target)
        if local_sha == remote_sha:
            spinner.succeed("Update completed.")
            logger.success("Git Update Success")
        else:
            spinner.fail("Git Update Failed.")
            logger.warning(
                "Failed to update the source code, please check your network or for conflicting files"
            )
    except GitError as e:
        if "not owned by current user" in str(e):
            logger.error(f"Git repo ownership error: {e}")
            if repo: del repo
            repair_broken_git_repo()
        else:
            logger.error(f"Unhandled Git error: {e}")
            raise


def dynamic_update_installer():
    # Define paths for the installer and Python interpreter
    installer_path = BAAS_ROOT_PATH / "deploy/installer/installer.py"

    # Use platform-independent way to determine Python executable
    if __system__ == "Windows":
        python_path = BAAS_ROOT_PATH / ".venv/Scripts/python.exe"
    else:  # Linux/Unix
        python_path = BAAS_ROOT_PATH / ".env/bin/python"

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
            run_app()
    elif G.internal_launch:  # Internal launch fallback
        run_app()
    else:
        if not os.path.exists(installer_path):
            logger.warning("Installer not found. Launching app directly.")
            run_app()
            sys.exit()

        # Use platform-specific commands to start the installer
        if __system__ == "Windows":
            os.system(f'START " " "{python_path}" "{installer_path}" --launch')
        else:  # Linux/Unix
            subprocess.run([python_path, installer_path, "--launch"])

    sys.exit()


def clean_up():
    if os.path.exists(P.TMP_PATH):
        shutil.rmtree(P.TMP_PATH)


def pre_check():
    if G.runtime_path == "default":
        check_python()
        if G.package_manager == "pdm":
            check_pdm()
        elif G.package_manager == "pip":
            check_pip()
        check_pth()
        check_env_patch()

    install_or_update_BAAS_repo_to_latest()
    check_requirements()
    if __system__ == "Windows":
        fix_exe_shebangs()


def get_update_type():
    global repo
    global local_sha
    global remote_sha
    global update_type
    local_sha = G.current_BAAS_version
    if len(local_sha) == 0:
        if os.path.exists(BAAS_ROOT_PATH / ".git"):
            repo = Repository(str(BAAS_ROOT_PATH))
            # Get local SHA
            try:
                local_sha = str(repo.head.target)
            except Exception as e:
                logger.error(f"Incorrect Key or corrupted repo: {e}. Remove [ .git ] folder and reinstall.")
                del repo
                # repo = None
                update_type = "full"
                gc.collect()
                shutil.rmtree(BAAS_ROOT_PATH / ".git")
                return
        else:
            # first install
            update_type = "full"
            return

    assert (len(local_sha) == 40)
    mirrorc_inst.set_version(local_sha)
    remote_sha = Utils.get_remote_sha()
    assert (len(remote_sha) == 40)
    logger.info(f"local_sha : {local_sha}")
    logger.info(f"remote_sha: {remote_sha}")
    if local_sha == remote_sha:
        update_type = "latest"
        return
    update_type = "incremental"
    return


def install_or_update_BAAS_repo_to_latest():
    if G.dev:
        return

    get_update_type()

    global update_type
    if update_type == "latest":
        logger.info("No Update Available.")
        return

    if try_mirrorc_install_or_update():
        return
    try_git_install_or_update()

def try_git_install_or_update():
    global repo
    global local_sha
    if os.path.exists(BAAS_ROOT_PATH / ".git"):
        git_update_baas()
    else:
        git_install_baas()
        repo = Repository(str(BAAS_ROOT_PATH))
        local_sha = str(repo.head.target)
    config.set_and_save("General.current_BAAS_version", local_sha)

def try_mirrorc_install_or_update():
    if not (len(mirrorc_cdk) > 0):
        return False

    global latest_mirrorc_return
    global update_type
    if latest_mirrorc_return is None:
        latest_mirrorc_return = mirrorc_inst.get_latest_version(cdk=mirrorc_cdk)
    if not latest_mirrorc_return.has_url:
        MirrorC_Updater.log_mirrorc_error(latest_mirrorc_return, logger)
        return False
    # timestamp to datetime
    expired_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_mirrorc_return.cdk_expired_time))
    logger.success("CDK valid, expired time : " + expired_time_str)
    if latest_mirrorc_return.latest_version_name == local_sha:
        logger.info("No Update Available.")
        return True
    if update_type == "full":
        mirrorc_install_baas()
    elif update_type == "incremental":
        mirrorc_update_baas()

    if os.path.exists(BAAS_ROOT_PATH / ".git"):
        logger.info("Removing [ .git ] directory...")
        shutil.rmtree(BAAS_ROOT_PATH / ".git", ignore_errors=False, onerror=Utils.on_rm_error)

    config.set_and_save("General.current_BAAS_version", latest_mirrorc_return.latest_version_name)
    return True

def mirrorc_install_baas():
    logger.info("+--------------------------------+")
    logger.info("|     MIRRORC INSTALL BAAS       |")
    logger.info("+--------------------------------+")
    # Download the repository zip file
    global latest_mirrorc_return
    file_MB = latest_mirrorc_return.file_size / (1024 * 1024)
    logger.info("Downloading the repository zip, total = %.2f MB" % file_MB)
    zip_path = Utils.download_file(
        latest_mirrorc_return.download_url, P.TMP_PATH
    )
    logger.info("Unzipping the repository...")
    Utils.unzip_file(zip_path, P.TMP_PATH)

    logger.info("Moving unzipped files to BAAS root path...")
    file_dir = P.TMP_PATH / "blue_archive_auto_script"
    Utils.copy_directory_structure(file_dir, BAAS_ROOT_PATH)

    logger.success("Mirrorc Install Success!")

def mirrorc_update_baas():
    logger.info("+--------------------------------+")
    logger.info("|      MIRRORC UPDATE BAAS       |")
    logger.info("+--------------------------------+")

    global latest_mirrorc_return

    # wait for incremental update
    if latest_mirrorc_return.update_type == "full":
        logger.info("Current package is [ full ].")
        logger.info("Waiting for [ incremental ] update package...")
        max_retry = 10
        for i in range(1, max_retry+1):
            time.sleep(0.5)
            logger.info(f"Retry : {i}/{max_retry}")
            latest_mirrorc_return = mirrorc_inst.get_latest_version(cdk=mirrorc_cdk)
            if latest_mirrorc_return.update_type == "incremental":
                logger.success("Get Incremental Package")
                break

    if latest_mirrorc_return.update_type == "incremental":
        logger.info("<<< Incremental Update >>>")
        file_MB = latest_mirrorc_return.file_size / (1024 * 1024)
        logger.info("Downloading the incremental zip, total = %.2f MB" % file_MB)
        zip_path = Utils.download_file(
            latest_mirrorc_return.download_url, P.TMP_PATH
        )
        logger.info("Unzipping the incremental update...")
        Utils.unzip_file(zip_path, P.TMP_PATH)

        MirrorC_Updater.apply_update(
            P.TMP_PATH,
            P.TMP_PATH / "changes.json",
            BAAS_ROOT_PATH,
            logger
        )
        logger.success("Mirrorc Incremental Update Success!")

    if latest_mirrorc_return.update_type == "full":
        logger.info("<<< Full Update >>>")
        mirrorc_install_baas()

if __name__ == "__main__":
    try:
        # Check the whole installation
        if not G.launch:
            pre_check()
        clean_up()
        # Check if the installer is frozen
        if not G.use_dynamic_update:
            run_app()  # Run the app if not frozen
        else:
            dynamic_update_installer()  # Update the installer if frozen
    except Exception as e:
        logger.exception("Error occurred during setup...")
        error_tackle()

    # Parse command-line arguments and configuration
