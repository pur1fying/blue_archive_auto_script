from ctypes import util
import logging
import os.path
import shutil
import subprocess
import sys
import argparse
import traceback
import zipfile

import psutil
import requests
from tqdm import tqdm

# gitee的下载地址需要把blob改成raw
TMP_PATH = './tmp'
GET_PYTHON_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip'
REPO_URL_HTTP = 'https://gitee.com/pur1fy/blue_archive_auto_script.git'
GIT_HOME = './toolkit/Git/bin/git.exe'
GET_PIP_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py'
GET_ATX_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/ATX.apk'
LOCAL_PATH = './blue_archive_auto_script'

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
        shutil.move(item_path, './')


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


def install_package():
    try:
        subprocess.run(
            ["./lib/python.exe", '-m', 'pip', 'install', 'virtualenv', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
             '--no-warn-script-location'])
        subprocess.run(["./lib/python.exe", '-m', 'virtualenv', 'env'])
        subprocess.run(["./env/Scripts/python", '-m', 'pip', 'install', '-r', './requirements.txt', '-i',
                        'https://pypi.tuna.tsinghua.edu.cn/simple', '--no-warn-script-location'])
    except Exception as e:
        raise Exception("Install requirements failed")


def unzip_file(zip_dir, out_dir):
    with zipfile.ZipFile(zip_dir, 'r') as zip_ref:
        # 解压缩所有文件到当前目录
        zip_ref.extractall(path=out_dir)
        logger.info(f"{zip_dir} unzip success, output files in {out_dir}")


def check_pth():
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
    proc = subprocess.Popen(['./env/Scripts/pythonw', './window.py'],)
    return proc.pid


def run_app():
    logger.info("Start to run the app...")
    try:
        with open("pid","a+") as f:
            f.seek(0)
            try:
                last_pid = int(f.read())
            except:
                last_pid =  2147483647
            if psutil.pid_exists(last_pid) == False:
                f.close()
                with open("pid","w+") as f:
                    f.write(str(start_app()))
                    print("Start app success.")
                    f.close()
            else:
                if not args.force_launch:
                    print('app already started.')
                else:
                    with open("pid","w+") as f:
                        f.write(str(start_app()))
                    print("Start app success.")
                    
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
    if not os.path.exists('./lib/Scripts/pip.exe'):
        logger.info("Pip is not installed, trying to install pip...")
        filepath = download_file(GET_PIP_URL)
        proc = subprocess.run(['./lib/python.exe', filepath])


def check_python():
    logger.info("Checking python installation...")
    if not os.path.exists('./lib/python.exe'):
        logger.info("Python environment is not installed, trying to install python...")
        filepath = download_file(GET_PYTHON_URL)
        unzip_file(filepath, './lib')
        os.remove(filepath)


def check_atx():
    logger.info("Checking atx-agent...")
    if not os.path.exists('src/atx_app/ATX.apk'):
        logger.info("Downloading atx-agent...")
        download_file(GET_ATX_URL)


def check_git():
    logger.info("Checking git installation...")
    if not os.path.exists('./.git'):
        logger.info("+--------------------------------+")
        logger.info("|         INSTALL BAAS           |")
        logger.info("+--------------------------------+")
        subprocess.run([GIT_HOME, 'clone', '--depth', '1', REPO_URL_HTTP])
        mv_repo(LOCAL_PATH)
        logger.info("Install success")
    elif not os.path.exists('./no_update'):
        logger.info("+--------------------------------+")
        logger.info("|          UPDATE BAAS           |")
        logger.info("+--------------------------------+")
        remote_sha = (subprocess.check_output([GIT_HOME, 'ls-remote', '--heads', 'origin', 'refs/heads/master'])
                      .decode('utf-8')).split('\t')[0]
        local_sha = (subprocess.check_output([GIT_HOME, 'rev-parse', 'HEAD'])
                     .decode('utf-8')).split('\n')[0]
        logger.info(f"remote_sha:{remote_sha}")
        logger.info(f"local_sha:{local_sha}")
        if local_sha == remote_sha and subprocess.check_output([GIT_HOME, 'diff']) == b'':
            logger.info("No updates available")
        else:
            logger.info("Pulling updates from the remote repository...")
            subprocess.run([GIT_HOME, 'reset', '--hard', 'HEAD'])
            subprocess.run([GIT_HOME, 'pull', REPO_URL_HTTP])

            updated_local_sha = (subprocess.check_output([GIT_HOME, 'rev-parse', 'HEAD'])
                                 .decode('utf-8')).split('\n')[0]
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
    launch_exec_args.insert(1,os.path.abspath("./installer.py"))
    if os.path.exists('./installer.py') and os.path.exists('./env/Scripts/python.exe') and len(sys.argv)>1:
        # print(launch_exec_args)
        subprocess.run(launch_exec_args)
    else:
        os.system(f"{os.path.abspath('./env/Scripts/python.exe')} {os.path.abspath('./installer.py')} --launch")
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
        check_requirements()
        # check_onnxruntime()
        # run_app()
    except Exception as e:
        traceback.print_exc()
        clear_tmp()
        os.system('pause')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blue Archive Auto Script Launcher&Installer")
    parser.add_argument('--launch', action='store_true', help='Directly launch BAAS')
    parser.add_argument('--force-launch', action='store_true', help='ignore multi instance check')

    args = parser.parse_args()

    if not args.launch:
        check_install()
    if not check_frozen_installer():
        run_app()
    else:
        dynamic_update_installer()