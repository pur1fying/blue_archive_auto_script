#!/bin/bash

VENV_NAME=myenv
TEMP_FOLDER=temp_build
TEMP_BUILD=build
TEMP_GENERATION=dist
DEB_PACKAGE_NAME=blue-archive-auto-script
DEB_VERSION=1.1.0
DEB_ARCH=amd64
INSTALL_DIR=/usr/local/bin

# Create the temp folder
mkdir -p $TEMP_FOLDER

# Create the virtual build environment
python3 -m venv $TEMP_FOLDER/$VENV_NAME

# Activate the virtual environment
source $TEMP_FOLDER/$VENV_NAME/bin/activate

# Install the required packages
pip install -r requirements.installer.txt
# For Chinese Users
# pip install -r requirements.installer.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Pyinstaller build the executable file
pyinstaller -i gui/assets/logo.ico --name baas -F installer.py --hidden-import=pygit2 --hidden-import=_cffi_backend --collect-submodules=pygit2 --collect-submodules=cffi

# Move the generated file out of the temp generation dir
mv ./dist/* ./

# Remove the temporary directories
rm -rf $TEMP_FOLDER $TEMP_BUILD $TEMP_GENERATION baas.spec

# Begin creating the .deb package
DEB_TEMP_DIR=deb_build
mkdir -p $DEB_TEMP_DIR/DEBIAN
mkdir -p $DEB_TEMP_DIR/$INSTALL_DIR

# Move the executable into the installation directory
mv baas $DEB_TEMP_DIR/$INSTALL_DIR/

# Create the control file
cat <<EOL > $DEB_TEMP_DIR/DEBIAN/control
Package: $DEB_PACKAGE_NAME
Version: $DEB_VERSION
Section: utils
Priority: optional
Architecture: $DEB_ARCH
Maintainer: Your Name <your.email@example.com>
Description: Blue Archive Auto Script
 A custom tool for automating processes in Blue Archive.
EOL

# Ensure correct permissions for DEBIAN directory and its contents
chmod 0755 $DEB_TEMP_DIR/DEBIAN
chmod 0644 $DEB_TEMP_DIR/DEBIAN/control

# Build the .deb package
dpkg-deb --build $DEB_TEMP_DIR

# Rename the .deb package with a meaningful name
mv $DEB_TEMP_DIR.deb ${DEB_PACKAGE_NAME}_${DEB_VERSION}_${DEB_ARCH}.deb

# Clean up the temporary deb directory
rm -rf $DEB_TEMP_DIR

echo "Debian package ${DEB_PACKAGE_NAME}_${DEB_VERSION}_${DEB_ARCH}.deb has been created."
