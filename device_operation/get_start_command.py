import subprocess
import sys

import psutil


def get_start_cmd(executable_name):
    result = []
    for proc in psutil.process_iter(['name', 'exe']):
        if proc.info['name'] == executable_name:
            path = proc.info['exe']
            try:
                args = proc.cmdline()
            except Exception:
                # Use wmic if psutil fails to get cmdline
                try:
                    output = subprocess.check_output(
                        ['wmic', 'process', 'where', f'ProcessId={proc.pid}', 'get', 'Commandline', '/value'])
                    output = output.decode(
                        sys.getdefaultencoding())  # decode the output using system's default encoding
                    args = output.strip().split('=')[1:]
                    args = [arg.strip() for arg in args if arg.strip() != '']
                except Exception as e:
                    continue
            if args is not None and len(args) > 0:
                args[0] = path
                if args not in result:
                    result.append(args)
    return result


def get_executable_path_and_args(executable_name):
    result = []
    for proc in psutil.process_iter(['name', 'exe']):
        if proc.info['name'] == executable_name:
            path = proc.info['exe']
            try:
                args = proc.cmdline()
            except Exception:
                # Use wmic if psutil fails to get cmdline
                try:
                    output = subprocess.check_output(
                        ['wmic', 'process', 'where', f'ProcessId={proc.pid}', 'get', 'Commandline', '/value'])
                    output = {
                        output.decode(sys.getdefaultencoding())}  # decode the output using system's default encoding
                    args = output.strip().split('=')[1:]
                    args = [arg.strip() for arg in args if arg.strip() != '']
                except Exception as e:
                    continue
            if args is not None and len(args) > 0:
                args[0] = path
                result.append(' '.join(args))
    return result
