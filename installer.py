import logging
import os.path
import shutil
import subprocess
import threading
import traceback
import zipfile

import requests
from tqdm import tqdm

# gitee的下载地址需要把blob改成raw
TMP_PATH = './tmp'
GET_PYTHON_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script/raw/file/python-3.9.13-embed-amd64.zip'
REPO_URL_HTTP = 'https://gitee.com/pur1fy/blue_archive_auto_script.git'
GIT_HOME = './tookit/Git/bin/git.exe'
GET_PIP_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script/raw/file/get-pip.py'
GET_ATX_URL = 'https://gitee.com/pur1fy/blue_archive_auto_script/raw/file/ATX.apk'
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
    threading.Thread(target=subprocess.Popen, args=(['./env/Scripts/pythonw', './window.py'],)).start()


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
    if not os.path.exists('./ATX.apk'):
        logger.info("Downloading atx-agent...")
        download_file(GET_ATX_URL)


def check_git():
    logger.info("Checking git installation...")
    if not os.path.exists('./.git'):
        logger.info("You seem to have no files for baas, trying to clone the project...")
        subprocess.run([GIT_HOME, 'clone', '--depth', '1', REPO_URL_HTTP])
        mv_repo(LOCAL_PATH)
        logger.info("Clone success")
    elif not os.path.exists('./no_update'):
        logger.info("You seem to have files for baas, trying to pull the project...")
        subprocess.run([GIT_HOME, 'pull', REPO_URL_HTTP])
        logger.info("Pull success")


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
        run_app()
    except Exception as e:
        traceback.print_exc()
        clear_tmp()
        os.system('pause')


if __name__ == '__main__':
    check_install()
