# Baas on Android
> [!NOTE]
> 本教程为手动构建教程。如果没有特殊需求，建议使用 devcontainer/docker 配置环境。

本教程假定你使用 WSL2（Debian 13） 或 Debian 13。开始前确保你网络通畅，因为接下来需要下载大量文件。

> [!NOTE]
> 对于 WSL2，务必将文件放在 WSL2 内，而不是 Windows 内。因为 WSL2 对 NTFS 文件系统支持较差，速度极慢，几乎不可用。

所有命令均在 Python venv 下执行。

## 环境配置
Python：3.9  
JDK：17

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libegl1

# JDK
JAVA_HOME="/opt/java/openjdk-17"
mkdir -p ${JAVA_HOME}
curl -L "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/adoptium"
tar -xz --strip-components=1 -C ${JAVA_HOME}

export JAVA_HOME
export PATH=$JAVA_HOME/bin:$PATH
```

## SDK 下载
<!--
### Android SDK
```bash
# pwd: {workspace}/
mkdir -p .sdk/android-sdk
cd .sdk/android-sdk
wget https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
unzip commandlinetools-linux-13114758_latest.zip
rm commandlinetools-linux-13114758_latest.zip
cd ../..

export ANDROIDSDK="$(pwd)/.sdk/android-sdk/cmdline-tools/bin"
```

### Android NDK
版本固定为 r25c。
```bash
# pwd: {workspace}/
mkdir -p .sdk/android-ndk
cd .sdk/android-ndk
wget https://dl.google.com/android/repository/android-ndk-r25c-linux.zip
unzip android-ndk-r25c-linux.zip
rm android-ndk-r25c-linux.zip
cd ../..

export ANDROIDNDK="$(pwd)/.sdk/android-ndk/android-ndk-r25c"
```
-->

### Qt
```bash
# pwd: {workspace}/
pip install aqtinstall
mkdir -p .qt-lib
aqt install-qt linux android 6.7.3 android_arm64_v8a --autodesktop
```
成功执行后目录结构如下：
```
(.venv) vscode ➜ /workspaces/baas_for_android/.qt-lib (android_main) $ tree -L 2
.
├── 6.7.3
│   ├── android_arm64_v8a
│   └── gcc_64
└── aqtinstall.log

4 directories, 1 file
```

### PySide
```bash
# pwd: {workspace}/

# 对于 Docker 用户，
# 可以将 pyside6_android_deploy 的缓存目录移动到项目内，避免每次都重复下载。
mkdir -p .pyside6_android_deploy
ln -sfn "$(pwd)/.pyside6_android_deploy" ~/.pyside6_android_deploy

git clone https://code.qt.io/pyside/pyside-setup
cd pyside-setup
git checkout 6.7
pip install -r requirements.txt
pip install -r tools/cross_compile_android/requirements.txt
python tools/cross_compile_android/main.py --download-only --skip-update --auto-accept-license
```

## 依赖构建
### PySide6
由于 PySide6 的预构建 wheel 只提供 3.11 版本，因此这里我们需要手动构建 Python 3.9 版本。

首先应用 patch：
```bash

```

然后构建：
```bash
# pwd: {workspace}/
python pyside-setup/tools/cross_compile_android/main.py \
    --sdk-path "$(pwd)/.pyside6_android_deploy/android-sdk" \
    --ndk-path "$(pwd)/.pyside6_android_deploy/android-ndk/android-ndk-r26b" \
    --qt-install-path "$(pwd)/.qt-lib/6.7.3"
```
执行后会自动构建 Python 与 PySide6。

### 其他依赖
```bash

```

# // WIP
借助 pyside6-android-deploy 创建 buildozer 项目。这条命令只需执行一次，
得到 buildozer.spec 文件后，后续只需要执行 `buildozer android debug` 即可。

```bash
# pwd: {workspace}/
pyside6-android-deploy --name "BaasOnAndroid" \
    --wheel-pyside="PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl" \
    --wheel-shiboken="shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl" \
    --extra-ignore-dirs=".buildozer,deployment,.sdk,.pyside6_android_deploy,.qt-lib" \
    --keep-deployment-files
```