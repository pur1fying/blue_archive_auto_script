@echo off
set VENV_NAME=myenv
set TEMP_FOLDER=temp_build

mkdir %TEMP_FOLDER%

python -m venv %TEMP_FOLDER%\%VENV_NAME%
call %TEMP_FOLDER%\%VENV_NAME%\Scripts\activate

pip install pyinstaller
pip install requests
pip install tqdm
pip install psutil
pyinstaller -i gui/assets/logo.ico --clean --name BlueArchiveAutoScript -F installer.py

rmdir /s /q %TEMP_FOLDER%
ren .\BlueArchiveAutoScript.exe backup.exe
copy .\dist\BlueArchiveAutoScript.exe .\
