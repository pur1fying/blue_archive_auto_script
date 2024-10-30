import os
import sys
import shutil
import logging
import zipfile
import platform
import psutil
import argparse
import requests
import threading
import traceback
import subprocess
from tqdm import tqdm
from dulwich import porcelain
from dulwich.repo import Repo

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

    progress_bar.close()
    return file_path


def check_python_installation():
    try:
        # Try to run the 'python' command to get version information
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Python is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    try:
        # Try to run the 'python3' command to get version information
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Python 3 is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    # If both checks fail, Python is not installed
    print("Python is not installed on this system.")
    return False


def install_package():
    try:
        # Detect the OS and select the appropriate Python executable and path
        system = platform.system()

        # If Linux, don't create a virtual environment
        if system == 'Linux':
            env_python_exec = './env/bin/python3'
            subprocess.run([env_python_exec, '-m', 'pip', 'install', '-r', './requirements-linux.txt', '-i',
                            'https://pypi.tuna.tsinghua.edu.cn/simple', '--no-warn-script-location'], check=True)
            return

        if system == 'Windows':
            python_exec_file = './lib/python.exe'
            env_python_exec = './env/Scripts/python'
        else:
            raise Exception("Unsupported OS")

        if not os.path.exists('./env/Scripts/python.exe'):
            # Install virtualenv package
            subprocess.run(
                [python_exec_file, '-m', 'pip', 'install', 'virtualenv', '-i',
                 'https://pypi.tuna.tsinghua.edu.cn/simple',
                 '--no-warn-script-location'], check=True)

            # Create the virtual environment
            subprocess.run([python_exec_file, '-m', 'virtualenv', 'env'], check=True)

            # Remove the Build Environment -> Remaining Problem for `ModuleNotFoundError: No module named '_socket'`
            # shutil.rmtree('./lib')

        # Install packages in requirements.txt within the virtual environment
        subprocess.run([env_python_exec, '-m', 'pip', 'install', '-r', './requirements.txt', '-i',
                        'https://pypi.tuna.tsinghua.edu.cn/simple', '--no-warn-script-location'], check=True)

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
                    with open("pid", "w+") as f:
                        f.write(str(start_app()))
                    logger.info("Start app success.")
            f.close()
            with open("pid", "w+") as f:
                f.write(str(start_app()))
                logger.info("Start app success.")
                f.close()

    except Exception as e:
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
    logger.info("Install requirements success")


def check_path():
    logger.info("Checking tmp path...")
    if not os.path.exists(TMP_PATH):
        os.mkdir(TMP_PATH)


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

        # Check if there are any changes
        status = porcelain.status(repo)
        has_changes = status.unstaged or status.staged
        refresh_required = args.refresh and has_changes
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
    launch_exec_args = sys.argv.copy()
    launch_exec_args[0] = os.path.abspath("./env/Scripts/python.exe")
    launch_exec_args.insert(1, os.path.abspath("./installer.py"))
    if os.path.exists('./installer.py') and os.path.exists('./env/Scripts/python.exe') and len(sys.argv) > 1:
        # print(launch_exec_args)
        try:
            subprocess.run(launch_exec_args)
        except:
            run_app()
    elif args.internal_launch == True:
        run_app()
    else:
        if not os.path.exists('./installer.py'):
            run_app()
            sys.exit()
        os.system("START \" \" ./env/Scripts/python.exe ./installer.py --launch")
    sys.exit()


def check_install():
    try:
        clear_tmp()
        create_tmp()
        check_python()
        check_pip()
        check_git()
        check_pth()
        check_atx()
        check_env_patch()
        check_requirements()
        # check_onnxruntime()
        # run_app()
    except Exception as e:
        traceback.print_exc()
        clear_tmp()
        os.system('pause')


if __name__ == '__main__':
    # argsions
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description="Blue Archive Auto Script Launcher & Installer\nGitHub Repo: https://github.com/pur1fying/blue_archive_auto_script\nOfficial QQ Group: 658302636")
    parser.add_argument('--dev', dest='dev', action='store_true', help='Development mode')
    parser.add_argument('--refresh', dest='refresh', action='store_true', help='Drop all changes')
    parser.add_argument('--launch', action='store_true', help='Directly launch BAAS')
    parser.add_argument('--force-launch', action='store_true', help='ignore multi BAAS instance check')
    parser.add_argument('--internal-launch', action='store_true', help='Use launcher inside pre-build executable files')
    parser.add_argument('--no-build', action='store_true', help='Disable Internal BAAS Installer builder')
    args = parser.parse_args()

    if not args.launch:
        check_install()

    if not check_frozen_installer():
        run_app()
    else:
        dynamic_update_installer()
