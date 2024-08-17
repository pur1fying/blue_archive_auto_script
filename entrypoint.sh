#!/bin/bash

# 设置虚拟环境的名称和临时文件夹的名称
VENV_NAME="myenv"
TEMP_FOLDER="temp_build"

# 创建临时文件夹
mkdir -p "$TEMP_FOLDER"

# 创建虚拟环境
python3 -m venv "$TEMP_FOLDER/$VENV_NAME"

# 激活虚拟环境
source "$TEMP_FOLDER/$VENV_NAME/bin/activate"

# 安装所需的 Python 包
pip install pyinstaller
pip install requests
pip install tqdm

# 使用 PyInstaller 打包应用程序
pyinstaller -i gui/assets/logo.ico --name BlueArchiveAutoScript -F installer.py

# 删除临时文件夹
rm -rf "$TEMP_FOLDER"
