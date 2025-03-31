from .device_config import load_data


def get_display_name(uuid):
    # 调用load_data函数获取设备配置
    device_data = load_data(uuid)

    if device_data:
        # 创建变量并根据设备配置进行修改
        simulator_type = device_data['simulator_type']
        multi_instance = device_data['multi_instance']

        # 修改设备类型为模拟器类型
        if simulator_type == "bluestacks_nxt":
            simulator_type = "BlueStacks 5"
        if simulator_type == "bluestacks_nxt_cn":
            simulator_type = "蓝叠模拟器 5 中国版"
        if simulator_type == "mumu12":
            simulator_type = "MuMu 12"
        if simulator_type == "leidian":
            simulator_type = "雷电模拟器"
        if simulator_type == "xiaoyao_nat":
            simulator_type = "雷电模拟器"
        if simulator_type == "wsa":
            simulator_type = "适用于 Android™️ 的 Windows 子系统"
        # 修改多开序号为显示序号
        if simulator_type == "mumu12" or simulator_type == "leidian" or simulator_type == "xiaoyao_nat":
            multi_instance = f"多开 {multi_instance}"
        # 返回修改后的值
        return simulator_type, multi_instance

    # 如果没有找到对应的设备配置，返回None
    raise FileNotFoundError("DEVICE_NOT_FOUND")


def convert_display_name(simulator_type, multi_instance=None):
    # 修改多开序号为显示序号

    if simulator_type == "mumu12" or simulator_type == "leidian" or simulator_type == "xiaoyao_nat":
        if multi_instance == None:
            multi_instance = 0
        multi_instance = f"多开 {multi_instance}"
    # 修改显示类型

    if simulator_type == "bluestacks_nxt":
        simulator_type = "BlueStacks 5"
    if simulator_type == "bluestacks_nxt_cn":
        simulator_type = "蓝叠模拟器 5 中国版"
    if simulator_type == "mumu12":
        simulator_type = "MuMu 12"
    if simulator_type == "leidian":
        simulator_type = "雷电模拟器"
    if simulator_type == "xiaoyao_nat":
        simulator_type = "雷电模拟器"
    if simulator_type == "wsa":
        simulator_type = "适用于 Android™️ 的 Windows 子系统"

    # 返回修改后的值
    return simulator_type, multi_instance
