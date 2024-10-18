#!/bin/bash

VENV_NAME=myenv
TEMP_FOLDER=temp_build
TEMP_BUILD=build
TEMP_GENERATION=dist

# Create the temp folder
mkdir -p $TEMP_FOLDER

# Create the virtual build environment
python3 -m venv $TEMP_FOLDER/$VENV_NAME

# Activate the virtual environment
source $TEMP_FOLDER/$VENV_NAME/bin/activate

# Install the required packages
pip install -r requirements.installer.txt

# Pyinstaller build the executable file
pyinstaller -i gui/assets/logo.ico --name BlueArchiveAutoScript -F installer.py

# Move the Generated file out of the temp generation dir
mv ./dist/* ./

# Remove the temporary Directory
rm -rf $TEMP_FOLDER $TEMP_BUILD $TEMP_GENERATION BlueArchiveAutoScript.spec
