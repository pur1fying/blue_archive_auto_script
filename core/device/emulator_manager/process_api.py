import os
import psutil
import subprocess

from typing import Union


def match_lists(target_args: list[str], process_cmdline: list[str]):
    # target_args and process_cmdline have different format for their strings, so this method check if they're equals
    for string in target_args:
        cleaned_str = string.strip('"\'')
        if cleaned_str not in process_cmdline:
            return False
    return True


def extract_args(emulator_path: str) -> tuple[str, list[str]]:
    # Resolve the emulator's actual executable path from a shortcut if provided
    if emulator_path.endswith('.lnk'):
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
        except ImportError:
            return emulator_path, [""]
        shortcut = shell.CreateShortCut(emulator_path)
        emulator_path = os.path.abspath(shortcut.Targetpath)

        # Extract command line arguments from the shortcut
        arguments = shortcut.Arguments
        arguments = arguments.split(" ")
    else:
        # No .lnk file, so there are no additional arguments
        arguments = [""]

    return emulator_path, arguments


def start(emulator_path: str):
    if os.path.isfile(emulator_path):
        directory = os.path.dirname(emulator_path)
        path, args = extract_args(emulator_path)
        subprocess.Popen([path] + args, shell=True, cwd=directory)


def is_running(emulator_path) -> Union[psutil.Process, None]:
    # Initialize the COM library
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        return None

    emulator_path, target_args = extract_args(emulator_path)

    # Iterate over all running processes
    for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cmdline']):
        try:
            process_info = proc.info
            process_exe = process_info.get('exe')  # Use get to handle potential None values

            if process_exe is not None:
                process_cmdline = process_info.get('cmdline', '')
                # Compare the executable path and command line arguments
                if (os.path.normcase(process_exe) == os.path.normcase(emulator_path)):
                    if target_args is None or (process_cmdline and match_lists(target_args, process_cmdline)):
                        p = psutil.Process(process_info['pid'])
                        return p  # Emulator process is running
        except Exception as e:
            print(e)
    return None


def terminate(emulator_path: str) -> bool:
    p = is_running(emulator_path)
    try:
        if p is not None:
            p.terminate()
            return True  # Emulator process terminated successfully
    except Exception as e:
        print(e)

    return False  # Emulator process not found or termination failed
