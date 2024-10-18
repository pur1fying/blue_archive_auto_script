import os
import shutil
import logging
import os.path
import zipfile
import platform
import argparse
import requests
import threading
import traceback
import subprocess
from tqdm import tqdm
from dulwich import porcelain
from dulwich.repo import Repo

# gitee的下载地址需要把blob改成raw
TMP_PATH = '../../deploy/installer/tmp'
GET_PYTHON_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip'
REPO_URL_HTTP = 'https://gitee.com/pur1fy/blue_archive_auto_script.git'
GET_PIP_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py'
GET_ATX_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/ATX.apk'
LOCAL_PATH = '../../deploy/installer/blue_archive_auto_script'

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

    # 获取文件大小（以字节为单位）
    total_size = int(response.headers.get('Content-Length', 0))

    # 使用tqdm创建进度条
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
        # 尝试运行 'python' 命令以获取版本信息
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Python is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    try:
        # 尝试运行 'python3' 命令以获取版本信息
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Python 3 is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    # 如果两次检测都失败，表示系统没有安装 Python
    print("Python is not installed on this system.")
    return False


def install_package():
    try:
        # 检测操作系统，并选择合适的 Python 可执行文件和路径
        system = platform.system()

        # If Linux, don't create a virtual environment
        if system == 'Linux':
            env_python_exec = './env/bin/python3'
            subprocess.run(['./env/bin/python3', '-m', 'pip', 'install', '-r', './requirements-linux.txt', '-i',
                            'https://pypi.tuna.tsinghua.edu.cn/simple', '--no-warn-script-location'], check=True)
            return

        if system == 'Windows':
            python_exec_file = './lib/python.exe'
            env_python_exec = './env/Scripts/python'
        else:
            raise Exception("Unsupported OS")

        # 安装 virtualenv 包
        subprocess.run(
            [python_exec_file, '-m', 'pip', 'install', 'virtualenv', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
             '--no-warn-script-location'], check=True)

        # 创建虚拟环境
        subprocess.run([python_exec_file, '-m', 'virtualenv', 'env'], check=True)

        # 在虚拟环境中安装 requirements.txt 中的包
        subprocess.run([env_python_exec, '-m', 'pip', 'install', '-r', './requirements.txt', '-i',
                        'https://pypi.tuna.tsinghua.edu.cn/simple', '--no-warn-script-location'], check=True)

        print("Packages installed successfully")

    except Exception as e:
        raise Exception(f"Install requirements failed: {e}")


def unzip_file(zip_dir, out_dir):
    with zipfile.ZipFile(zip_dir, 'r') as zip_ref:
        # 解压缩所有文件到当前目录
        zip_ref.extractall(path=out_dir)
        logger.info(f"{zip_dir} unzip success, output files in {out_dir}")


def check_pth():
    if platform.system() == 'Linux': return
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
            if line.count('self._create_inference_session(providers, provider_options, disabled_optimizers)'):
                line = line.replace('self._create_inference_session(providers, provider_options, disabled_optimizers)',
                                    'self._create_inference_session([\'AzureExecutionProvider\','
                                    ' \'CPUExecutionProvider\'], provider_options, disabled_optimizers)')
            read_file.append(line)
    with open('./lib/Lib/site-packages/onnxruntime/capi/onnxruntime_inference_collection.py', 'w',
              encoding='utf-8') as f:
        f.writelines(read_file)


def start_app():
    _path = './lib/Scripts/pythonw.exe' if platform.system() == 'Windows' else './lib/bin/python3'
    threading.Thread(target=subprocess.Popen, args=([_path, './window.py'],)).start()


def run_app():
    logger.info("Start to run the app...")
    try:
        start_app()
        print("Start app success")
    except Exception as e:
        raise Exception("Run app failed")


def check_requirements():
    logger.info("Check package Installation...")
    install_package()
    logger.info("Install requirements success")


def check_path():
    logger.info("Checking tmp path...")
    if not os.path.exists(TMP_PATH):
        os.mkdir(TMP_PATH)


def check_pip():
    logger.info("Checking pip installation...")
    if platform.system() == 'Linux': return
    if not os.path.exists('./lib/Scripts/pip.exe'):
        logger.info("Pip is not installed, trying to install pip...")
        filepath = download_file(GET_PIP_URL)
        subprocess.run(['./lib/python.exe', filepath])


def check_python():
    logger.info("Checking python installation...")
    # Platform-specific Python installation check
    if platform.system() == 'Windows':
        _path = './lib/python.exe'
    elif platform.system() == 'Linux':
        _path = '../../deploy/installer/env/bin/python3'
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
    if not os.path.exists('../../src/atx_app/ATX.apk'):
        logger.info("Downloading atx-agent...")
        download_file(GET_ATX_URL)


def check_git(opt):
    if opt.dev: return
    logger.info("Checking git installation...")
    if not os.path.exists('./.git'):
        logger.info("+--------------------------------+")
        logger.info("|         INSTALL BAAS           |")
        logger.info("+--------------------------------+")
        porcelain.clone(REPO_URL_HTTP, './')
        mv_repo(LOCAL_PATH)
        logger.info("Install success")
    elif not os.path.exists('./no_update'):
        logger.info("+--------------------------------+")
        logger.info("|          UPDATE BAAS           |")
        logger.info("+--------------------------------+")
        repo = Repo('.')

        # 获取本地 SHA
        local_sha = repo.head().decode('ascii')

        # 获取远程 SHA
        remote_refs = porcelain.ls_remote(REPO_URL_HTTP)
        remote_sha = remote_refs.get(b'refs/heads/master').decode('ascii')

        logger.info(f"remote_sha: {remote_sha}")
        logger.info(f"local_sha: {local_sha}")

        # Check if there are any changes
        status = porcelain.status(repo)
        has_changes = status.unstaged or status.staged

        if local_sha == remote_sha and not has_changes:
            logger.info("No updates available")
        else:
            logger.info("Pulling updates from the remote repository...")
            # Reset the local repository to the state of the remote repository
            porcelain.reset(repo, mode='hard')
            # Pull the latest changes from the remote repository
            porcelain.pull(repo, REPO_URL_HTTP, 'master')
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


def check_install(opt):
    try:
        clear_tmp()
        create_tmp()
        check_python()
        check_pip()
        check_git(opt)
        check_pth()
        check_atx()
        check_requirements()
        # check_onnxruntime()
        run_app()
    except Exception as e:
        traceback.print_exc()
        clear_tmp()
        os.system('pause')


if __name__ == '__main__':
    # Options
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev', dest='dev', action='store_true', help='Development mode')
    option = parser.parse_args()
    check_install(option)
