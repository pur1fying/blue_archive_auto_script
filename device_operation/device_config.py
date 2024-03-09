import json
import os
import re
import uuid

from . import DEVICE_CONFIG_PATH
from .get_adb_address import get_simulator_port
from .preprocessing_name import preprocess_name

# 定义一个字典来存储UUID和对应的输入
data = {}


def device_config(simulator_type, multi_instance, latest_adb_address=None, latest_command_line=None):
    # 从json文件中读取字典
    multi_instance = preprocess_name(simulator_type, multi_instance)

    global data
    if os.path.exists(DEVICE_CONFIG_PATH + 'device.json'):
        with open(DEVICE_CONFIG_PATH + 'device.json', 'r') as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                data = {}

    # 检查是否已经存在相同的输入
    for id, value in data.items():
        if value['simulator_type'] == simulator_type and value['multi_instance'] == multi_instance:
            return id
        elif value['latest_adb_address'] == latest_adb_address:
            return id

    # 生成一个UUID
    id = str(uuid.uuid4())

    # 检测输入是否含最近的adb端口，不含端口则自动扫描
    # 注：此处未作输入合法性校验
    if latest_adb_address == None:
        latest_adb_address = get_simulator_port(simulator_type, multi_instance)

    # 将UUID和对应的输入存储到字典中
    data[id] = {
        'simulator_type': simulator_type,
        'multi_instance': multi_instance,
        'latest_adb_address': latest_adb_address,
        'latest_command_line': latest_command_line
    }

    # 确保目录存在
    os.makedirs('./config', exist_ok=True)

    # 将字典存储到json文件中
    with open(DEVICE_CONFIG_PATH + 'device.json', 'w') as f:
        json.dump(data, f)

    return id


def load_data(id):
    # 从json文件中读取字典
    try:
        with open(DEVICE_CONFIG_PATH + 'device.json', 'r') as f:
            data = json.load(f)
    except json.decoder.JSONDecodeError:
        data = {}
        # 根据UUID获取对应的输入
        device_info = data.get(id)
        if device_info is not None:
            # 获取simulator_type和multi_instance
            simulator_type = device_info['simulator_type']
            multi_instance = device_info['multi_instance']

            # 获取最新的adb端口
            latest_adb_address = get_simulator_port(simulator_type, multi_instance)

            # 检查返回的值是否满足IP地址:端口的形式
            ipv4_pattern = r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ipv6_pattern = r'\[(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\]:[0-9]{1,5}'
            if re.match(ipv4_pattern, latest_adb_address) or re.match(ipv6_pattern, latest_adb_address):
                # 将最新的adb端口写入到字典中
                device_info['latest_adb_address'] = latest_adb_address

                # 将字典存储到json文件中
                with open(DEVICE_CONFIG_PATH + 'device.json', 'w') as f:
                    json.dump(data, f)

        # 返回整个字典
        return data
    except:
        raise FileNotFoundError("ERROR_ON_READING_JSON")
