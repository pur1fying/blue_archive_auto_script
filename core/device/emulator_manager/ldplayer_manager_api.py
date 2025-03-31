import os
import subprocess

from core.device.emulator_manager.auto_scan_simulator import auto_scan_simulators


def mumu12_control_api_backend(multi_instance_number=0, operation="start"):
    if os.name == 'nt':
        import winreg
        # 读取注册表中的键值
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\leidian\LDPlayer9")

        InstallDir, _ = winreg.QueryValueEx(key, "DisplayIcon")
        winreg.CloseKey(key)
        adb_list = auto_scan_simulators()
        # 修改路径，使其指向ldconsole.exe
        exe_path = os.path.join(InstallDir, 'ldconsole.exe')
        if operation == "start":
            from .get_adb_address import get_simulator_port
            command = [exe_path, "launch", "--index", str(multi_instance_number)]
            subprocess.run(command)
            return get_simulator_port("leidian", multi_instance_number)
        elif operation == "stop":
            command = [exe_path, "quit", "--index", str(multi_instance_number)]
            subprocess.run(command)
        elif operation == "get_path":
            player_path = os.path.join(InstallDir, 'dnplayer.exe')
            if os.path.exists(player_path):
                return player_path
            else:
                return None
        elif operation == "get_manager_path":
            return exe_path
        elif operation == "get_launch_status":
            if get_simulator_port('leidian',multi_instance_number) in adb_list:
                return "start_finished"
            else:
                return "not_launched"
        else:
            raise ValueError("NOT_SUPPORTED_OPERATION")
