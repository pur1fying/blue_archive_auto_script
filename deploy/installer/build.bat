@echo off

set VENV_NAME=myenv
set TEMP_FOLDER=temp_build
set TEMP_BUILD=build
set TEMP_GENERATION=dist

:: Create the temp folder
mkdir %TEMP_FOLDER%

:: Create the virtual build environment
python -m venv %TEMP_FOLDER%\%VENV_NAME%

:: Activate the virtual environment
call %TEMP_FOLDER%\%VENV_NAME%\Scripts\activate.bat

:: Install the required packages
pip install -r requirements.installer.txt

:: Pyinstaller build the executable file
pyinstaller -i gui\assets\logo.ico --name BlueArchiveAutoScript -F installer.py

:: Move the Generated file out of the temp generation dir
move /Y .\dist\* .\

:: Remove the temporary Directory
rmdir /S /Q %TEMP_FOLDER%
rmdir /S /Q %TEMP_BUILD%
rmdir /S /Q %TEMP_GENERATION%
del BlueArchiveAutoScript.spec
