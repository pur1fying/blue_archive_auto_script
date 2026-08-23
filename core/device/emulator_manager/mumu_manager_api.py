import json
import os
import subprocess
import re

ANDROID_PATH = {
    "android12": "12.0",
    "android15": "15.0"
}
NEMU_CLIENT_PATH = ["shell", "sdk", "external_renderer_ipc.dll"]


def mumu_control_api_backend(simulator_type, multi_instance_number=0, operation="start"):
    if os.name == 'nt':
        try:
            import winreg
        # 读取注册表中的键值
            if simulator_type == "mumu":
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer-12.0")
                except:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayer")
            else:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal-12.0")#predict of mumu5.0 global

                except:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuMuPlayerGlobal")
        except:
            return None
        nx_main_path = str
        mumu_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
        def detect_major_version():
            match = re.match(r'^(\d+)\.', mumu_version)
            if match:
                return int(match.group(1))
        major_version_number = detect_major_version() #type: ignore
        if major_version_number:
            if major_version_number == 5 or major_version_number == 6:
                try:
                    install_path = os.path.abspath(winreg.QueryValueEx(key, "InstallLocation")[0]).strip('"')
                    nx_main_path = os.path.join(install_path, "nx_main")
                    exe_path = os.path.join(os.path.abspath(install_path), "nx_main", "MuMuManager.exe")
                except:
                    nx_main_path = os.path.dirname(winreg.QueryValueEx(key, "DisplayIcon")[0]).strip('"')
                    install_path = os.path.dirname(nx_main_path)
                    exe_path = exe_path = os.path.join(os.path.abspath(install_path), "nx_main", "MuMuManager.exe")
            else:
                install_path = os.path.dirname(winreg.QueryValueEx(key, "DisplayIcon")[0]).strip('"')
                exe_path = os.path.join(install_path, "MuMu" ,"MuMuManager.exe")
        else:
            return None
        winreg.CloseKey(key)
        # 修改路径，使其指向MuMuManager.exe
        def fetch_info(target_key: str) -> str:
            cmd = [exe_path, "info", "-v", str(multi_instance_number)]
            proc = subprocess.run(cmd, universal_newlines=True, capture_output=True, encoding="utf-8")
            info = json.loads(proc.stdout)
            try:
                return info[target_key]
            except FileNotFoundError:
                raise FileNotFoundError
            except:
                return f"{info['errcode']}, {info['errmsg']}"

        if operation == "start":
            # 使用mumumanager控制模拟器开启与关闭
            from .get_adb_address import get_simulator_port
            command = [exe_path, "control", "-v", str(multi_instance_number), "launch"]
            subprocess.run(command)
            return get_simulator_port("mumu", str(multi_instance_number))
        elif operation == "stop":
            command = [exe_path, "control", "-v", str(multi_instance_number), "shutdown"]
            subprocess.run(command)
        elif operation == "get_path":# 获取MuMuManager所在目录
            if nx_main_path != "":
                return nx_main_path
            else:
                return install_path
        elif operation == "get_device_path":# 获取MuMuNxDevice.exe所在的目录
            if int(major_version_number) == 5 or int(major_version_number) == 6:  # type: ignore
                return os.path.join(os.path.abspath(install_path), "nx_device", fetch_info("android_version"), "shell")
            else:
                return install_path
        elif operation == "get_manager_path": # 获取MuMuManager.exe所在的路径
            return exe_path
        elif operation == "get_nemu_client_path":# 获取external_renderer_ipc.dll所在的路径
            if int(major_version_number) == 5 or int(major_version_number) == 6: #type: ignore
                path =  os.path.join(os.path.abspath(install_path), "nx_device", fetch_info("android_version"), "shell", "sdk", "external_renderer_ipc.dll")
            else:
                path =  os.path.join(os.path.abspath(install_path), "sdk", "external_renderer_ipc.dll")
            if os.path.exists(path):
                return path
            else: # fallback with nx_main included nemu_client dll
                return os.path.join(os.path.dirname(exe_path), "sdk", "external_renderer_ipc.dll")
        elif operation == "disable_app_keptlive": # 关闭后台保活
            command = f""" "{exe_path}" setting -v {multi_instance_number} -k app_keptlive -val false"""
            subprocess.run(command, universal_newlines=True, capture_output=True)
        elif operation == "enable_app_keptlive": # 开启保活
            command = f""" "{exe_path}" setting -v {multi_instance_number} -k app_keptlive -val true"""
            subprocess.run(command, universal_newlines=True, capture_output=True)
        elif operation == "get_launch_status": #获取启动状态
            try:
                return fetch_info("player_state")
            except:
                return "not_launched"
        elif operation == "get_android_version":
            return str(fetch_info("android_version"))
        else:
            return None
if __name__ == "__main__":
    simulator_type = "mumu"
    test_results = []
    test_results.append(mumu_control_api_backend(simulator_type, multi_instance_number=0, operation="get_android_version"))
    test_results.append(mumu_control_api_backend(simulator_type, multi_instance_number=0, operation="get_nemu_client_path"))
    test_results.append(mumu_control_api_backend(simulator_type, multi_instance_number=0, operation="get_manager_path"))
    test_results.append(mumu_control_api_backend(simulator_type, multi_instance_number=0, operation="get_path"))
    test_results.append(mumu_control_api_backend(simulator_type, multi_instance_number=0, operation="get_launch_status"))
    print(test_results)
