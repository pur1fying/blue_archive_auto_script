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

import getpass
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from copy import deepcopy
from pathlib import Path

import psutil
import requests
import tomli_w
from alive_progress import alive_bar
from dulwich import porcelain
from dulwich.repo import Repo
from easydict import EasyDict as eDict
from halo import Halo
from loguru import logger

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

__system__ = platform.system()
__env__ = os.environ.copy()
if __system__ == "Windows":
    __env__["PYTHONPATH"] = '.env;.venv/Lib;.venv/Scripts;.venv;.;.venv/Lib/site-packages'

os.environ["PDM_IGNORE_ACTIVE_VENV"] = "1"

# ==================== Default Settings =====================

DEFAULT_SETTINGS = {
    "General": {
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
        "REPO_URL_HTTP": "",
        "GET_PIP_URL": "",
        "GET_UPX_URL": "",
        "GET_ENV_PATCH_URL": "",
        "GET_PYTHON_URL": "",
    },
    "Paths": {
        "BAAS_ROOT_PATH": "",
        "TMP_PATH": "tmp",
        "TOOL_KIT_PATH": "toolkit",
    },
}

REPO_MIRRORS = [
    "https://gitee.com/pur1fy/blue_archive_auto_script.git",
    "https://github.com/pur1fying/blue_archive_auto_script.git",
    "https://gitcode.com/m0_74686738/blue_archive_auto_script.git",
    "https://e.coding.net/g-jbio0266/baas/blue_archive_auto_script.git",
    "https://hub.fastgit.xyz/pur1fying/blue_archive_auto_script.git"
]

GET_PIP_MIRRORS = [
    "https://bootstrap.pypa.io/get-pip.py",
    "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py",
    "https://github.com/Nanboom233/blue_archive_auto_script_assets/raw/master/get-pip.py",
    "https://hub.fastgit.xyz/Nanboom233/blue_archive_auto_script_assets/raw/master/get-pip.py"
]

GET_UPX_MIRRORS = [
    "https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip",
    "https://github.com/Nanboom233/blue_archive_auto_script_assets/blob/master/upx-4.2.4-win64.zip",
    "https://hub.fastgit.xyz/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip"
]

GET_ENV_PATCH_MIRRORS = [
    "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/env_patch.zip",
    "https://github.com/Nanboom233/blue_archive_auto_script_assets/blob/master/env_patch.zip",
    "https://hub.fastgit.xyz/Nanboom233/blue_archive_auto_script_assets/blob/master/env_patch.zip"
]

GET_PYTHON_MIRRORS = [
    "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip",
    "https://github.com/Nanboom233/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip",
    "https://hub.fastgit.xyz/Nanboom233/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip",
]


class Utils:
    @staticmethod
    def get_fastest_mirror(mirrors: list[str], test_unless_unavailable: int) -> str:
        """
        Finds the fastest mirror from a list of URLs by measuring latency.

        Args:
            mirrors (list[str]): A list of mirror URLs to test.
            test_unless_unavailable (int): the number of mirrors to test unless none of which is unavailable.

        Returns:
            str: The URL of the fastest mirror.

        Raises:
            ConnectionError: If no available mirrors are found.
        """
        results = {}
        for i in range(len(mirrors)):
            mirror = mirrors[i]
            start = time.time()
            response = requests.get(mirror, stream=True, timeout=10)
            latency = (time.time() - start) * 1000  # ms

            if response.status_code >= 400:
                results[mirror] = float('inf')
                continue
            results[mirror] = latency
            if i >= test_unless_unavailable and min(results) != float('inf'):
                break

        fastest_mirror = min(results, key=results.get)
        if results[fastest_mirror] == float('inf'):
            raise ConnectionError("No available mirrors found.Please check your network connection or mirror URLs.")
        else:
            logger.info(f"Choosing {fastest_mirror} with latency {results[fastest_mirror]:.2f} ms")
        return fastest_mirror

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
            logger.success(f"{zip_dir} unzip success, output files in {out_dir}")

    @staticmethod
    def sudo(cmd, pwd):
        os.system(f"echo {pwd} | sudo -S {cmd}")


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
    config = DEFAULT_SETTINGS
else:
    # Load the configuration file
    with open(config_file, "rb") as file:
        config = tomllib.load(file)

GENERAL_CONFIG = eDict(config["General"])
URLS_CONFIG = eDict(config["URLs"])
PATHS_CONFIG = eDict(config["Paths"])

BAAS_ROOT_PATH = Path(PATHS_CONFIG.BAAS_ROOT_PATH).resolve() if PATHS_CONFIG.BAAS_ROOT_PATH else "" or BASE_PATH
GENERAL_CONFIG.runtime_path = GENERAL_CONFIG.runtime_path.replace("\\", "/")
PATHS_CONFIG.TMP_PATH = BAAS_ROOT_PATH / Path(PATHS_CONFIG.TMP_PATH)
PATHS_CONFIG.TOOL_KIT_PATH = BAAS_ROOT_PATH / Path(PATHS_CONFIG.TOOL_KIT_PATH)
if PATHS_CONFIG.BAAS_ROOT_PATH and not os.path.exists(PATHS_CONFIG.BAAS_ROOT_PATH):
    os.makedirs(PATHS_CONFIG.BAAS_ROOT_PATH)
if not os.path.exists(PATHS_CONFIG.TMP_PATH):
    os.makedirs(PATHS_CONFIG.TMP_PATH)
if not os.path.exists(PATHS_CONFIG.TOOL_KIT_PATH):
    os.makedirs(PATHS_CONFIG.TOOL_KIT_PATH)

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


# ==================== Environment Check ====================
def check_python_installation():
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
            url = URLS_CONFIG.GET_PYTHON_URL if URLS_CONFIG.GET_PYTHON_URL != "" \
                else (Utils.get_fastest_mirror(GET_PYTHON_MIRRORS, 2))
            filepath = Utils.download_file(url, PATHS_CONFIG.TMP_PATH)
            Utils.unzip_file(filepath, BAAS_ROOT_PATH / ".env")
            os.remove(filepath)
        elif __system__ == "Linux":
            # For Ubuntu, other Linux distributions may need to be modified
            Utils.sudo("add-apt-repository ppa:deadsnakes/ppa", GENERAL_CONFIG.linux_pwd)
            Utils.sudo("apt update", GENERAL_CONFIG.linux_pwd)
            Utils.sudo("apt-get install python3.9-venv -y", GENERAL_CONFIG.linux_pwd)
            Utils.sudo(f"python3.9 -m venv {BAAS_ROOT_PATH / '.env'}", GENERAL_CONFIG.linux_pwd)


def check_pip_installation():
    logger.info("Checking pip installation...")
    if __system__ == "Linux":
        return

    assert __system__ == "Windows"
    if not os.path.exists(BAAS_ROOT_PATH / ".env/Scripts/pip.exe"):
        logger.warning("Pip is not installed, trying to install pip...")
        url = URLS_CONFIG.GET_PIP_URL if URLS_CONFIG.GET_PIP_URL != "" \
            else (Utils.get_fastest_mirror(GET_PIP_MIRRORS, 3))
        filepath = Utils.download_file(url, PATHS_CONFIG.TMP_PATH)
        subprocess.run([BAAS_ROOT_PATH / ".env/python.exe", filepath])


def check_pdm_installation():
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


def check_git_installation():
    if GENERAL_CONFIG.dev:
        return
    logger.info("Checking git installation...")

    repo_url = URLS_CONFIG.REPO_URL_HTTP if URLS_CONFIG.REPO_URL_HTTP != "" \
        else (Utils.get_fastest_mirror(REPO_MIRRORS, 3))

    if not os.path.exists(BAAS_ROOT_PATH / ".git"):
        logger.info("+--------------------------------+")
        logger.info("|         INSTALL BAAS           |")
        logger.info("+--------------------------------+")
        spinner.start("Cloning the repository...")

        porcelain.clone(repo_url, BAAS_ROOT_PATH)
        spinner.succeed("Clone completed.")
        logger.success("Install success!")
    else:
        logger.info("+--------------------------------+")
        logger.info("|          UPDATE BAAS           |")
        logger.info("+--------------------------------+")
        repo = Repo(str(BAAS_ROOT_PATH))

        # Get local SHA
        try:
            local_sha = repo.head().decode("ascii")
        except:
            logger.error("Incorrect Key. Trying to reinstall...")
            shutil.rmtree(BAAS_ROOT_PATH / ".git")
            check_git_installation()
            return

        # Get remote SHA
        remote_refs = porcelain.ls_remote(repo_url)
        remote_sha = remote_refs.get(b"refs/heads/master").decode("ascii")

        logger.info(f"remote_sha: {remote_sha}")
        logger.info(f"local_sha: {local_sha}")

        refresh_required = GENERAL_CONFIG.refresh
        if local_sha == remote_sha and not refresh_required:
            logger.info("No updates available")
        else:
            if refresh_required:
                logger.info(
                    "You've selected dropping all changes for the project file."
                )
            spinner.start("Pulling updates from the remote repository...")
            # Reset the local repository to the state of the remote repository
            porcelain.reset(repo, mode="hard")
            # Pull the latest changes from the remote repository
            porcelain.pull(repo, repo_url, "master", protocol_version=0)
            updated_local_sha = repo.head().decode("ascii")
            if updated_local_sha == remote_sha:
                spinner.succeed("Update completed.")
                logger.success("Update success")
            else:
                spinner.fail("Update failed.")
                logger.warning(
                    "Failed to update the source code, please check your network or for conflicting files"
                )


def check_upx_installation():
    logger.info("Checking UPX installation.")
    if not os.path.exists("toolkit/upx-4.2.4-win64/upx.exe"):
        url = URLS_CONFIG.GET_UPX_URL if URLS_CONFIG.GET_UPX_URL != "" \
            else (Utils.get_fastest_mirror(GET_UPX_MIRRORS, 2))
        filepath = Utils.download_file(url, PATHS_CONFIG.TMP_PATH)
        Utils.unzip_file(filepath, PATHS_CONFIG.TOOL_KIT_PATH)
        os.remove(filepath)


def install_package():
    logger.info("Check package Installation...")
    try:
        env_pip_exec = None

        # Detect the OS and select the appropriate Python executable and path
        def try_sources(pkg_mgr_path, followed_cmd=None):
            for _source in GENERAL_CONFIG.source_list:
                try:
                    _followed_cmd = deepcopy(followed_cmd)
                    if GENERAL_CONFIG.package_manager == "pdm":
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

        if GENERAL_CONFIG.runtime_path == "default":

            # If Linux, don't create a virtual environment
            if __system__ == "Linux":
                mgr_path = BAAS_ROOT_PATH / ".env/bin/pdm"
                if GENERAL_CONFIG.package_manager == "pip":
                    mgr_path = BAAS_ROOT_PATH / ".env/bin/pip"
                    Utils.sudo(f"chown -R $(whoami) {BAAS_ROOT_PATH}", GENERAL_CONFIG.linux_pwd)
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
                and GENERAL_CONFIG.package_manager == "pip"
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
            env_python_exec = GENERAL_CONFIG.runtime_path
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


def check_env_patch():
    if __system__ == "Linux":
        return
    if os.path.exists(BAAS_ROOT_PATH / ".env/Lib/site-packages/Polygon"):
        return
    logger.info("Downloading env patch...")
    url = URLS_CONFIG.GET_ENV_PATCH_URL if URLS_CONFIG.GET_ENV_PATCH_URL != "" \
        else (Utils.get_fastest_mirror(GET_ENV_PATCH_MIRRORS, 2))
    filepath = Utils.download_file(url, PATHS_CONFIG.TMP_PATH)
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


# ==================== Installer Related ====================

def start_app():
    if GENERAL_CONFIG.runtime_path == "default":
        _path = (
            BAAS_ROOT_PATH / ".venv/Scripts/pythonw.exe"
            if __system__ == "Windows"
            else (
                BAAS_ROOT_PATH / ".venv/bin/python3"
                if GENERAL_CONFIG.package_manager == "pdm"
                else BAAS_ROOT_PATH / ".env/bin/python3"
            )
        )
        _path = (
            BAAS_ROOT_PATH / ".venv/Scripts/python"
            if GENERAL_CONFIG.debug and __system__ == "Windows"
            else _path
        )
    else:
        _path = GENERAL_CONFIG.runtime_path

    if __system__ == "Linux":
        if GENERAL_CONFIG.runtime_path == "default":
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
    try:  # 记录启动时的pythonw的pid
        with open(BAAS_ROOT_PATH / "pid", "a+") as f:
            f.seek(0)
            try:
                last_pid = int(f.read())
            except:
                last_pid = 2147483647
            if psutil.pid_exists(last_pid):
                if not GENERAL_CONFIG.force_launch:
                    logger.info(
                        "App already started. Killing."
                    )  # 如果上一次的BAAS已经启动，就关闭
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

    if __system__ == "Windows" and not GENERAL_CONFIG.no_build:
        try:
            import PyInstaller.__main__

            check_upx_installation()

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
    elif GENERAL_CONFIG.internal_launch:  # Internal launch fallback
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
    if os.path.exists(PATHS_CONFIG.TMP_PATH):
        shutil.rmtree(PATHS_CONFIG.TMP_PATH)


def pre_check():
    if GENERAL_CONFIG.runtime_path == "default":
        check_python_installation()
        if GENERAL_CONFIG.package_manager == "pdm":
            check_pdm_installation()
        elif GENERAL_CONFIG.package_manager == "pip":
            check_pip_installation()
        check_pth()
        check_env_patch()
    check_git_installation()
    install_package()
    if __system__ == "Windows":
        fix_exe_shebangs()


if __name__ == "__main__":
    try:
        # Check the whole installation
        if not GENERAL_CONFIG.launch:
            pre_check()
        clean_up()
        # Check if the installer is frozen
        if not GENERAL_CONFIG.use_dynamic_update:
            run_app()  # Run the app if not frozen
        else:
            dynamic_update_installer()  # Update the installer if frozen
    except Exception as e:
        logger.exception("Error occurred during setup...")
        error_tackle()

    # Parse command-line arguments and configuration
