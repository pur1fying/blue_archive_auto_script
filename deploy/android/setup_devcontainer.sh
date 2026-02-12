#!/bin/bash

set -e
set -u
set -o pipefail

# ########## Download SDK ##########
# # check if android-sdk installed
# if [ -d .sdk/android-sdk/cmdline-tools ]; then
#     echo "Android SDK already installed."
# else
#     # download sdk
#     echo "Downloading Android SDK..."
#     mkdir -p .sdk/android-sdk
#     cd .sdk/android-sdk
#     wget https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
#     unzip commandlinetools-linux-13114758_latest.zip
#     rm commandlinetools-linux-13114758_latest.zip
#     cd ../..
#     # accept sdk license
#     yes | .sdk/android-sdk/cmdline-tools/bin/sdkmanager --licenses
# fi

# ########## Download NDK ##########
# # check if ndk installed
# if [ -d .sdk/android-ndk ]; then
#     echo "Android NDK already installed."
# else
#     # download ndk
#     echo "Downloading Android NDK..."
#     mkdir -p .sdk/android-ndk
#     cd .sdk/android-ndk
#     wget https://dl.google.com/android/repository/android-ndk-r25c-linux.zip
#     unzip android-ndk-r25c-linux.zip
#     rm android-ndk-r25c-linux.zip
#     cd ../..
# fi

########## Setup PATH ##########
export ANDROIDSDK="$(pwd)/.sdk/android-sdk/cmdline-tools/bin"
export ANDROIDNDK="$(pwd)/.sdk/android-ndk/android-ndk-r25b"
# Link cache directory to workspace to avoid re-downloading
mkdir -p .pyside6_android_deploy
ln -sfn "$(pwd)/.pyside6_android_deploy" ~/.pyside6_android_deploy

########## Create Python virtual environment ##########

echo "Creating Python virtual environment..."
python -m venv .venv
echo "Activating virtual environment..."
. .venv/bin/activate
echo "Upgrading pip..."
python -m pip install --upgrade pip

if [ -f requirements-android.txt ]; then
    echo "Installing dependencies from requirements-android.txt..."
    pip install -r requirements-android.txt
    echo "Dependencies installed."
else
    echo "requirements-android.txt not found, skipping dependency installation."
fi

########## Setup pyside6-android-deploy ##########
# if [ -d ~/.pyside6-android-deploy ]; then
#     echo "pyside6-android-deploy already installed."
# else
#     git clone https://code.qt.io/pyside/pyside-setup
#     cd pyside-setup
#     git checkout 6.7
#     pip install -r requirements.txt
#     pip install -r tools/cross_compile_android/requirements.txt
#     python tools/cross_compile_android/main.py --download-only --skip-update --auto-accept-license
#     cd ..
# fi

# check pyside wheels
cd .pyside6_android_deploy
if [ ! -f pyside6-*.whl ]; then
    echo "pyside wheels not found, downloading..."
    wget https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl
fi
if [ ! -f shiboken6-*.whl ]; then
    echo "shiboken6 wheels not found, downloading..."
    wget https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl
fi
cd ..

########## Setup RapidOCR ##########
echo Downloading RapidOCR aar library...
mkdir -p build
cd build
wget -O rapidocr.aar https://github.com/RapidAI/RapidOcrAndroidOnnx/releases/download/1.3.0/OcrLibrary-1.3.0-release.aar
cd ..

echo "Environment setup complete."

########## Setup ADB ##########
# Prioritize IPv4 over IPv6 for ADB connection
sudo sed -i 's/#precedence ::ffff:0:0\/96  100/precedence ::ffff:0:0\/96  100/' /etc/gai.conf
