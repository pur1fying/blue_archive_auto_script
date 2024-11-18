import json

from .mumu_manager_api import mumu12_control_api_backend
### adb_port_scanner ###
from .bluestacks_module import get_bluestacks_nxt_adb_port


def get_simulator_port(simulator_type : str, multi_instance : str):
    if simulator_type == "bluestacks_nxt":
        if multi_instance == None or multi_instance == "":
            multi_instance = "BlueStacks App Player"
        bluestacks_adb_port_return = get_bluestacks_nxt_adb_port(multi_instance, "")
        if bluestacks_adb_port_return:
            return f"127.0.0.1:{bluestacks_adb_port_return}"
        else:
            raise FileNotFoundError('simulators not founded')

    elif simulator_type == "bluestacks_nxt_cn":
        if multi_instance == None or multi_instance == "":
            multi_instance = "BlueStacks"
        bluestacks_adb_port_return = get_bluestacks_nxt_adb_port(multi_instance, "cn")
        if bluestacks_adb_port_return:
            return f"127.0.0.1:{bluestacks_adb_port_return}"
        else:
            raise FileNotFoundError('simulators not founded')

    elif simulator_type == "mumu" or simulator_type == "mumu_global":
        def get_mumu_adb_info(multi_instance):
            import subprocess
            cmd = f'{mumu12_control_api_backend(simulator_type,0,"get_manager_path")} adb -v {multi_instance}'
            proc = subprocess.run(cmd, universal_newlines=True, capture_output=True, encoding="utf-8")
            adb_info = json.loads(proc.stdout)
            try:
                return f"{adb_info['adb_host']}:{adb_info['adb_port']}"
            except:
                return f"127.0.0.1:{int(multi_instance)*32+16384}"
        if multi_instance == None:
            multi_instance = 0
        if int(multi_instance) <= 1536:
            return get_mumu_adb_info(multi_instance)
        else:
            raise ValueError('INVALID_INPUT')

    elif simulator_type == "yeshen":
        multi_instance = int(multi_instance)
        if multi_instance != None and multi_instance != 1:
            ys_port = 62023 + multi_instance
        else:
            ys_port = 62001

        if ys_port <= 65535 and ys_port >= 0:
            return f"127.0.0.1:{ys_port}"
        else:
            raise ValueError('INVALID_INPUT')

    elif simulator_type == "xiaoyao_nat":
        if multi_instance != None:
            if int(multi_instance) <= 4404 and int(multi_instance) >= 0:
                return f"127.0.0.1:{int(multi_instance) * 10 + 21503}"
            else:
                raise ValueError('INVALID_INPUT')
        return f"127.0.0.1:21503"

    elif simulator_type == "leidian":
        if multi_instance == None or multi_instance == 0:
            multi_instance = 0
            return f"127.0.0.1:5555"
        else:
            return f"127.0.0.1:{int(multi_instance) * 2 + 5555}"

    elif simulator_type == "wsa":
        if multi_instance != None and multi_instance != "":
            return f"{multi_instance}:58526"
        else:
            return f"127.0.0.1:58526"
    raise ValueError('not supported operation or missing parameter')

### end adb_port_scanner ###
