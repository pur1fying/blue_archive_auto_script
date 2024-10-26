#!/bin/bash

# For Debug
# export QT_DEBUG_PLUGINS=1

# Check the version
GIT_HOME="/usr/bin/git"  # 修改为你的 git 可执行文件路径
REPO_URL_HTTP="https://gitee.com/pur1fy/blue_archive_auto_script.git"  # 修改为你的仓库地址

# 设置虚拟环境的名称
VENV_NAME="env"

# 检查虚拟环境是否已经存在
if [ -d "$VENV_NAME" ]; then
    echo "[INFO] Virtual environment '$VENV_NAME' already exists."
else
    # 创建虚拟环境
    echo "[INFO] Creating virtual environment '$VENV_NAME'..."
    python3.9 -m venv "$VENV_NAME"

    # 检查虚拟环境是否成功创建
    if [ ! -d "$VENV_NAME" ]; then
        echo "[ERROR] Failed to create the virtual environment."
        exit 1
    fi
fi

# 激活虚拟环境
echo "[INFO] Activating virtual environment '$VENV_NAME'..."
source "$VENV_NAME/bin/activate"

# 确认虚拟环境已激活
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "[INFO] Virtual environment '$VENV_NAME' activated successfully."
else
    echo "[ERROR] Failed to activate the virtual environment."
    exit 1
fi


echo "+--------------------------------+"
echo "|          UPDATE BAAS           |"
echo "+--------------------------------+"

remote_sha=$($GIT_HOME ls-remote --heads origin refs/heads/master | awk '{print $1}')
local_sha=$($GIT_HOME rev-parse HEAD)

echo "[INFO] Remote SHA: $remote_sha"
echo "[INFO] Local SHA: $local_sha"

if [ "$local_sha" = "$remote_sha" ] && [ -z "$($GIT_HOME diff)" ]; then
    echo "[INFO] No updates available"
else
    echo "[INFO] Pulling updates from the remote repository..."
    $GIT_HOME reset --hard HEAD
    $GIT_HOME pull "$REPO_URL_HTTP"

    updated_local_sha=$($GIT_HOME rev-parse HEAD)

    echo "[INFO] Updated SHA: $updated_local_sha"
    if [ "$updated_local_sha" = "$remote_sha" ]; then
        echo "[INFO] Update success"
    else
        echo "[ERROR] Failed to update the source code, please check your network or for conflicting files"
    fi
fi

ATX_APK_URL="https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/ATX.apk"

APK_PATH="/app/src/atx_app/ATX.apk"

echo "[INFO] Checking atx-agent..."

# Check if ATX.apk exists
if [ ! -f "$APK_PATH" ]; then
    echo "[INFO] Downloading atx-agent..."
    # Download ATX.apk
    wget -O "$APK_PATH" "$ATX_APK_URL"
else
    echo "[INFO] Atx-agent already downloaded"
fi


# Install the env
echo "[INFO] Check and Update the runtime environment..."
pip3.9 install -r requirements-linux.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Start the app
echo "[INFO] Starting the app..."

# If you have display, it's ok to comment the first block
# and uncomment the second block.

#########################################################
apt-get install -y xvfb x11vnc procps
xvfb-run python3.9 window.py &

# Wait until the xvfb is started
sleep 5

xvfb_info=$(ps -aux | grep '[X]vfb')
# Get Xvfb Info From proc


# Abstract ":99" and "-auth xxxxx"
display=$(echo "$xvfb_info" | grep -o ' :[0-9][0-9]')
auth=$(echo "$xvfb_info" | grep -oP '(?<=-auth )[^ ]+')

# Check the abstract status
if [ -n "$display" ] && [ -n "$auth" ]; then
    # build and run x11vnc command
    x11vnc_cmd="x11vnc -display $display -auth $auth"
    echo "Running command: $x11vnc_cmd"
    $x11vnc_cmd
else
    echo "Failed to extract display or auth information."
fi
#########################################################
# xvfb-run python3.9 window.py                          #
#########################################################
