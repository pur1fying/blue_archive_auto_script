@echo off

set VENV_NAME=myenv
set TEMP_FOLDER=temp_build
set TEMP_BUILD=build
set TEMP_GENERATION=dist

REM Create the temporary folder
mkdir %TEMP_FOLDER%

REM Create the virtual environment
python -m venv %TEMP_FOLDER%\%VENV_NAME%

REM Activate the virtual environment
call %TEMP_FOLDER%\%VENV_NAME%\Scripts\activate

REM Install required packages
pip install -r requirements.installer.txt

REM Build the executable file using PyInstaller
pyinstaller -i ./logo.ico --name BlueArchiveAutoScript -F installer.py

REM Move the generated file out of the temporary directory
move .\dist\* .\

REM Remove the temporary directory and build files
rmdir /s /q %TEMP_FOLDER%
rmdir /s /q %TEMP_BUILD%
rmdir /s /q %TEMP_GENERATION%
del BlueArchiveAutoScript.spec
