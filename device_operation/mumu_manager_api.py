import json
import os
import subprocess


def mumu12_control_api_backend(simulator_type, multi_instance_number=0, operation="start"):
    if os.name == 'nt':
        import winreg
        # 读取注册表中的键值
        if simulator_type == "mumu":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0")
        else:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal-12.0")

        icon_path, _ = winreg.QueryValueEx(key, "DisplayIcon")
        icon_path = icon_path.replace('"', '')  # 去除获取到的文件位置两侧的双引号
        winreg.CloseKey(key)

        # 修改路径，使其指向MuMuManager.exe
        dir_path = os.path.dirname(icon_path)
        exe_path = os.path.join(dir_path, r"""MuMuManager.exe""")
        if operation == "start":
            # 使用mumumanager控制模拟器开启与关闭
            from .get_adb_address import get_simulator_port
            command = [exe_path, "api", "-v", str(multi_instance_number), "launch_player"]
            subprocess.run(command)
            return get_simulator_port("mumu", multi_instance_number)
        elif operation == "stop":
            command = [exe_path, "api", "-v", str(multi_instance_number), "shutdown_player"]
            subprocess.run(command)
        elif operation == "get_path":
            player_path = os.path.join(dir_path, r"""MuMuPlayer.exe""")
            if os.path.exists(player_path):
                return player_path
            else:
                return None
        elif operation == "get_manager_path":
            return exe_path
        elif operation == "disable_app_keptlive":
            command = f""" "{exe_path}" setting -v {multi_instance_number} -k app_keptlive -val false"""
            subprocess.run(command, universal_newlines=True, capture_output=True)
        elif operation == "enable_app_keptlive":
            command = f""" "{exe_path}" setting -v {multi_instance_number} -k app_keptlive -val true"""
            subprocess.run(command, universal_newlines=True, capture_output=True)
        elif operation == "get_launch_status":
            cmd = [exe_path, "info", "-v", str(multi_instance_number)]
            proc = subprocess.run(cmd, universal_newlines=True, capture_output=True, encoding="utf-8")
            info = json.loads(proc.stdout)
            try:
                return info["player_state"]
            except:
                return "not_launched"
        else:
            raise ValueError("NOT_SUPPORTED_OPERATION")
