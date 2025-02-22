import argparse
import configparser
import logging
import os
import platform
import shutil
import subprocess
import sys
import traceback
import zipfile

import psutil
import requests
from dulwich import porcelain
from dulwich.repo import Repo
from tqdm import tqdm

# For Gitee download links, replace 'blob' with 'raw'
TMP_PATH = 'tmp'
GET_PYTHON_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip'
REPO_URL_HTTP = 'https://gitee.com/pur1fy/blue_archive_auto_script.git'
GET_PIP_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py'
GET_ATX_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/ATX.apk'
GET_ENV_PATCH_URL = 'https://gitee.com/kiramei/blue_archive_auto_script_assets/raw/master/env_patch.zip'
LOCAL_PATH = 'blue_archive_auto_script'
TOOL_KIT_PATH = './toolkit'
GET_UPX_URL = 'https://ghp.ci/https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip'

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

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)


def mv_repo(folder_path: str):
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        shutil.move(item_path, '../../')


def download_file(url: str):
    response = requests.get(url, stream=True)
    filename = url.split('/')[-1]
    file_path = TMP_PATH + '/' + filename

    # Get file size (in bytes)
    total_size = int(response.headers.get('Content-Length', 0))

    # Create a progress bar using tqdm
    progress_bar = tqdm(total=total_size, unit='B',
                        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                        unit_scale=True,
                        desc=filename)

    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                progress_bar.update(len(chunk))

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

G = eDict(config["General"])
U = eDict(config["URLs"])
P = eDict(config["Paths"])

BAAS_ROOT_PATH = Path(P.BAAS_ROOT_PATH).resolve() if P.BAAS_ROOT_PATH else "" or BASE_PATH
G.runtime_path = G.runtime_path.replace("\\", "/")
P.TMP_PATH = BAAS_ROOT_PATH / Path(P.TMP_PATH)
P.TOOL_KIT_PATH = BAAS_ROOT_PATH / Path(P.TOOL_KIT_PATH)
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
            print(f"Python is installed: {result.stdout.strip()}")
            return "python"
    except FileNotFoundError:
        pass

    try:
        # Try to run the 'python3' command to get version information
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Python 3 is installed: {result.stdout.strip()}")
            return "python3"
    except FileNotFoundError:
        pass

    # If both checks fail, Python is not installed
    print("Python is not installed on this system.")
    return None


def install_package():
    try:
        env_pip_exec = None

        # Detect the OS and select the appropriate Python executable and path
        def try_sources(pkg_mgr_path, followed_cmd=None):
            for _source in G.source_list:
                try:
                    if G.package_manager == "pdm":
                        subprocess.run(
                            [pkg_mgr_path, "config", "--local", "pypi.url", _source],
                            check=True,
                        )
                    else:
                        followed_cmd.extend(["-i", _source])
                    if followed_cmd:
                        if not type(pkg_mgr_path) == list:
                            cmds = [pkg_mgr_path, *followed_cmd]
                        else:
                            cmds = pkg_mgr_path
                            cmds.extend(followed_cmd)
                        subprocess.run(cmds, check=True)
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
            if system == 'Linux':
                env_python_exec = './env/bin/python3'
                subprocess.run([env_python_exec, '-m', 'pip', 'install', '-r', './requirements-linux.txt', '-i',
                                args.source, '--no-warn-script-location'], check=True)
                return

            python_exec_file = BAAS_ROOT_PATH / ".env/python.exe"
            env_pip_exec = [str(python_exec_file), '-m', 'pip']

            if not os.path.exists('./env/Scripts/python.exe'):
                # Install virtualenv package
                cmd_list = ["install", "virtualenv", "--no-warn-script-location"]

                try_sources(
                    env_pip_exec,
                    cmd_list,
                )
                subprocess.run(
                    [python_exec_file, '-m', 'pip', 'install', 'virtualenv', '-i',
                     args.source,
                     '--no-warn-script-location'], check=True)

                # Create the virtual environment
                subprocess.run([python_exec_file, '-m', 'virtualenv', 'env'], check=True)

                # Remove the Build Environment -> Remaining Problem for `ModuleNotFoundError: No module named '_socket'`
                # shutil.rmtree('./lib')
        else:
            env_python_exec = check_python_installation()

        if not env_python_exec:
            env_python_exec = args.runtime_path

        # Install packages in requirements.txt within the virtual environment
        subprocess.run([env_python_exec, '-m', 'pip', 'install', '-r', './requirements.txt', '-i',
                        args.source, '--no-warn-script-location'], check=True)

        print("Packages installed successfully")

    except Exception as e:
        raise Exception(f"Install requirements failed: {e}")


def unzip_file(zip_dir, out_dir):
    with zipfile.ZipFile(zip_dir, 'r') as zip_ref:
        # Unzip all files to the current directory
        zip_ref.extractall(path=out_dir)
        logger.info(f"{zip_dir} unzip success, output files in {out_dir}")


def check_pth():
    if platform.system() == 'Linux': return
    if os.path.exists('./env/Scripts/python.exe'): return
    logger.info("Checking pth file...")
    read_file = []
    with open('./lib/python39._pth', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('#import site'):
                line = line.replace('#', '')
            read_file.append(line)
    with open('./lib/python39._pth', 'w', encoding='utf-8') as f:
        f.writelines(read_file)


def check_onnxruntime():
    logger.info("Checking onnxruntime.InferenceSession Bug solution...")
    with open('./lib/Lib/site-packages/onnxruntime/capi/onnxruntime_inference_collection.py', 'r',
              encoding='utf-8') as f:
        lines = f.readlines()
        read_file = []
        for line in lines:
            if line.count('self._create_inference_session(providers, provider_argsions, disabled_argsimizers)'):
                line = line.replace(
                    'self._create_inference_session(providers, provider_argsions, disabled_argsimizers)',
                    'self._create_inference_session([\'AzureExecutionProvider\','
                    ' \'CPUExecutionProvider\'], provider_argsions, disabled_argsimizers)')
            read_file.append(line)
    with open('./lib/Lib/site-packages/onnxruntime/capi/onnxruntime_inference_collection.py', 'w',
              encoding='utf-8') as f:
        f.writelines(read_file)


def start_app():
    _path = './env/Scripts/pythonw.exe' if platform.system() == 'Windows' else './lib/bin/python3'
    _path = './env/Scripts/python' if args.debug and platform.system() == 'Windows' else _path
    proc = subprocess.Popen([_path, './window.py'], )
    return proc.pid


def run_app():
    logger.info("Start to run the app...")
    try:  # 记录启动时的pythonw的pid
        with open("pid", "a+") as f:
            f.seek(0)
            try:
                last_pid = int(f.read())
            except:
                last_pid = 2147483647
            if psutil.pid_exists(last_pid):
                if not args.force_launch:
                    logger.info('App already started. Killing.')  # 如果上一次的BAAS已经启动，就关闭
                    p = psutil.Process(last_pid)
                    try:
                        p.terminate()
                    except:
                        os.system(f'taskkill /f /pid {last_pid}')
                else:
                    with open("pid", "w+") as _f:
                        _f.write(str(start_app()))
                    logger.info("Start app success.")
            f.close()
            with open("pid", "w+") as _f:
                _f.write(str(start_app()))
                logger.info("Start app success.")
                _f.close()

    except Exception:
        raise Exception("Run app failed")

    if platform.system() == "Windows" and args.no_build == False:
        try:
            import PyInstaller.__main__
            check_upx()

            def create_executable():
                PyInstaller.__main__.run([
                    './installer.py',
                    '--name=BlueArchiveAutoScript',
                    '--onefile',
                    '--icon=gui/assets/logo.ico',
                    '--noconfirm',
                    '--upx-dir',
                    './toolkit/upx-4.2.4-win64'
                ])

            if os.path.exists("./backup.exe") and not os.path.exists("./no_build"):
                create_executable()
                logger.info('try to remove the backup executable file.')
                try:
                    os.remove('./backup.exe')
                except:
                    logger.info('remove backup.exe failed.')
                else:
                    logger.info('remove finished.')
                os.rename("BlueArchiveAutoScript.exe", "backup.exe")
                shutil.copy("dist/BlueArchiveAutoScript.exe", ".")
        except:
            logger.warning('Build new BAAS launcher failed, Please check the Python Environment')
            logger.info('''
                        Now you can turn off this command line window safely or report this issue to developers.
                        现在您可以安全地关闭此命令行窗口或向开发者上报问题。
                        您現在可以安全地關閉此命令行窗口或向開發人員報告此問題。
                        今、このコマンドラインウィンドウを安全に閉じるか、この問題を開発者に報告することができます。
                        이제 이 명령줄 창을 안전하게 종료하거나 이 문제를 개발자에게 보고할 수 있습니다.''')
            os.system('pause')


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
    if platform.system() == 'Linux': return
    if os.path.exists('./env/Scripts/python.exe'): return
    logger.info("Checking pip installation...")
    if not os.path.exists('./lib/Scripts/pip.exe'):
        logger.info("Pip is not installed, trying to install pip...")
        filepath = download_file(GET_PIP_URL)
        subprocess.run(['./lib/python.exe', filepath])


def check_python():
    logger.info("Checking python installation...")
    # Platform-specific Python installation check
    if platform.system() == 'Windows':
        if os.path.exists('./env/Scripts/python.exe'): return
        _path = './lib/python.exe'
    elif platform.system() == 'Linux':
        _path = './env/bin/python3'
    else:
        raise Exception("Unsupported OS")

    if not os.path.exists(_path):
        logger.info("Python environment is not installed, trying to install python...")
        if platform.system() == 'Windows':
            filepath = download_file(GET_PYTHON_URL)
            unzip_file(filepath, './lib')
            os.remove(filepath)
        elif platform.system() == 'Linux':
            # For Ubuntu, other Linux distributions may need to be modified
            subprocess.run(['sudo', 'add-apt-repository', 'ppa:deadsnakes/ppa'], check=True)
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', 'python3.9-venv', '-y'], check=True)
            subprocess.run(['sudo', 'python3.9', '-m', 'venv', 'env'], check=True)
        else:
            raise Exception("Unsupported OS")


def check_atx():
    logger.info("Checking atx-agent...")
    if not os.path.exists('src/atx_app/ATX.apk'):
        logger.info("Downloading atx-agent...")
        download_file(GET_ATX_URL)


def check_upx():
    logger.info("Checking UPX installation.")
    if not os.path.exists('toolkit/upx-4.2.4-win64/upx.exe'):
        filepath = download_file(GET_UPX_URL)
        unzip_file(filepath, TOOL_KIT_PATH)
        os.remove(filepath)


def check_env_patch():
    if platform.system() == 'Linux': return
    if os.path.exists('./env/Lib/site-packages/Polygon'): return
    logger.info("Downloading env patch...")
    filepath = download_file(GET_ENV_PATCH_URL)
    unzip_file(filepath, './env')


def check_git():
    if args.dev: return
    logger.info("Checking git installation...")
    if not os.path.exists('./.git'):
        logger.info("+--------------------------------+")
        logger.info("|         INSTALL BAAS           |")
        logger.info("+--------------------------------+")
        porcelain.clone(REPO_URL_HTTP, './')
        mv_repo(LOCAL_PATH)
        shutil.rmtree(LOCAL_PATH)
        logger.info("Install success")
    elif not os.path.exists('./no_update'):
        logger.info("+--------------------------------+")
        logger.info("|          UPDATE BAAS           |")
        logger.info("+--------------------------------+")
        repo = Repo('.')

        # Get local SHA
        local_sha = repo.head().decode('ascii')

        # Get remote SHA
        remote_refs = porcelain.ls_remote(REPO_URL_HTTP)
        remote_sha = remote_refs.get(b'refs/heads/master').decode('ascii')

        logger.info(f"remote_sha: {remote_sha}")
        logger.info(f"local_sha: {local_sha}")

        refresh_required = args.refresh
        if local_sha == remote_sha and not refresh_required:
            logger.info("No updates available")
        else:
            if refresh_required:
                logger.info("You've selected dropping all changes for the project file.")
            logger.info("Pulling updates from the remote repository...")
            # Reset the local repository to the state of the remote repository
            porcelain.reset(repo, mode='hard')
            # Pull the latest changes from the remote repository
            porcelain.pull(repo, REPO_URL_HTTP, 'master', protocol_version=0)
            updated_local_sha = repo.head().decode('ascii')
            if updated_local_sha == remote_sha:
                logger.info("Update success")
            else:
                logger.warning("Failed to update the source code, please check your network or for conflicting files")


def create_tmp():
    if not os.path.exists(TMP_PATH):
        os.mkdir(TMP_PATH)
    if not os.path.exists(LOCAL_PATH):
        os.mkdir(LOCAL_PATH)


def clear_tmp():
    if os.path.exists(TMP_PATH):
        shutil.rmtree(TMP_PATH)
    if os.path.exists(LOCAL_PATH):
        shutil.rmtree(LOCAL_PATH)


def check_frozen_installer():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return True
    else:
        return False


def dynamic_update_installer():
    # Define paths for the installer and Python interpreter
    installer_path = "./deploy/installer/installer.py"

    # Use platform-independent way to determine Python executable
    if platform.system() == "Windows":
        python_path = "./env/Scripts/python.exe"
    else:  # Linux/Unix
        python_path = "./env/bin/python"

    # Prepare the command arguments
    launch_exec_args = sys.argv.copy()
    launch_exec_args[0] = os.path.abspath(python_path)
    launch_exec_args.insert(1, os.path.abspath(installer_path))

    # Check if paths exist and arguments are provided
    if os.path.exists(installer_path) and os.path.exists(python_path) and len(sys.argv) > 1:
        try:
            subprocess.run(launch_exec_args)
        except Exception as e:
            print(f"Error running installer: {e}")
            run_app()
    elif args.internal_launch:  # Internal launch fallback
        run_app()
    else:
        if not os.path.exists(installer_path):
            print("Installer not found. Launching app directly.")
            run_app()
            sys.exit()

        # Use platform-specific commands to start the installer
        if platform.system() == "Windows":
            os.system(f"START \" \" \"{python_path}\" \"{installer_path}\" --launch")
        else:  # Linux/Unix
            subprocess.run([python_path, installer_path, "--launch"])

    sys.exit()


def check_install():
    try:
        clear_tmp()
        create_tmp()
        if args.runtime_path == 'default' and not args.use_local_python:
            check_python()
            check_pip()
            check_pth()
            check_env_patch()
        check_git()
        check_atx()
        check_requirements()
        clear_tmp()
        # check_onnxruntime()
        # run_app()
    except Exception:
        traceback.print_exc()
        clear_tmp()
        os.system('pause')


def parse_args_and_config():
    # Default configuration file path
    default_config_path = "setup.ini"

    # Initialize argparse for command-line arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Blue Archive Auto Script Launcher & Installer\n"
            "GitHub Repo: https://github.com/pur1fying/blue_archive_auto_script\n"
            "Official QQ Group: 658302636"
        )
    )

    # Define command-line arguments
    parser.add_argument('--config', type=str, default=default_config_path, help='Path to the INI configuration file')
    parser.add_argument('--dev', action='store_true', help='Development mode')
    parser.add_argument('--refresh', action='store_true', help='Drop all changes')
    parser.add_argument('--launch', action='store_true', help='Directly launch BAAS')
    parser.add_argument('--force-launch', action='store_true', help='Ignore multi BAAS instance check')
    parser.add_argument('--internal-launch', action='store_true', help='Use launcher inside pre-build executable files')
    parser.add_argument('--no-build', action='store_true', help='Disable Internal BAAS Installer builder')
    parser.add_argument('--debug', action='store_true', help='Enable Console Output')
    parser.add_argument('--source', type=str, help='Specify the source of the package')
    parser.add_argument('--runtime_path', type=str, help='Specify the runtime path of the package')
    parser.add_argument('--use_local_python', action='store_true',
                        help='Whether to use local python instead of embedded python')

    global args, unknown_args
    # Parse command-line arguments
    args, unknown_args = parser.parse_known_args()

    # Load configuration from INI file
    config = configparser.ConfigParser()
    if os.path.exists(args.config):
        config.read(args.config)
    else:
        print(f"Warning: Configuration file '{args.config}' not found. Using default settings.")
        # Create a default configuration file if it doesn't exist
        with open(args.config, 'w') as config_file:
            config.write(config_file)

    # Helper function to retrieve values from the configuration file
    def get_config_option(section, option, fallback=None, value_type=any):
        """
        Retrieve a configuration option from the INI file.

        :param section: The section name in the INI file.
        :param option: The option name within the section.
        :param fallback: The default value to use if the option is missing.
        :param value_type: The expected type of the value (str, bool, int).
        :return: The retrieved value or the fallback value.
        """
        try:
            if value_type == bool:
                return config.getboolean(section, option, fallback=fallback)
            elif value_type == int:
                return config.getint(section, option, fallback=fallback)
            else:
                return config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    # Override configuration values with command-line arguments if provided
    args.dev = args.dev or get_config_option('General', 'dev', fallback=False, value_type=bool)
    args.refresh = args.refresh or get_config_option('General', 'refresh', fallback=False, value_type=bool)
    args.launch = args.launch or get_config_option('General', 'launch', fallback=False, value_type=bool)
    args.force_launch = args.force_launch or get_config_option('General', 'force_launch', fallback=False,
                                                               value_type=bool)
    args.internal_launch = args.internal_launch or get_config_option('General', 'internal_launch', fallback=False,
                                                                     value_type=bool)
    args.no_build = args.no_build or get_config_option('General', 'no_build', fallback=False, value_type=bool)
    args.debug = args.debug or get_config_option('General', 'debug', fallback=False, value_type=bool)
    args.source = args.source or get_config_option('General', 'source',
                                                   fallback='https://pypi.tuna.tsinghua.edu.cn/simple')
    args.runtime_path = args.runtime_path or get_config_option('General', 'runtime_path', fallback='default')
    args.use_local_python = args.use_local_python or get_config_option('General', 'use_local_python', fallback=False,
                                                                       value_type=bool)

    return args, unknown_args


if __name__ == '__main__':
    # Parse command-line arguments and configuration
    args, unknown_args = parse_args_and_config()

    # Check the whole installation
    if not args.launch:
        check_install()

    # Check if the installer is frozen
    if not check_frozen_installer():
        run_app()  # Run the app if not frozen
    else:
        dynamic_update_installer()  # Update the installer if frozen
