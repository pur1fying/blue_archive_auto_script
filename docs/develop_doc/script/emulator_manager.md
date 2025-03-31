# 简介

模拟器进程级api，支持主流安卓模拟器。

## 使用方法

```python

from core.device import emulator_manager
```

## 包含功能&函数用法

### 函数列表

- `get_adb_address(simulator_type,multi_instance)`获取对应的adb地址
- `get_adb_address_by_uuid(uuid)`获取对应的adb地址
- `get_simulator_commandline_uuid(uuid)`获取对应的命令行参数
- `get_simulator_uuid(uuid)`获取模拟器对应的uuid
- `convert_display_name(simulator_type,multi_instance)`输入内部参数，返回用户可读的模拟器名和多开信息
- `get_display_name_uuid(uuid)`
- `auto_scan()`自动扫描正在运行的模拟器
- `autosearch()`自动扫描正在运行的模拟器对应的adb地址
- `preprocess_name(simulator_type,multi_instance)`处理可能缺少的参数
- `mumu12_api_backend(multi_instance,operation)`mumumanager包装
- `simulator_cmd()`获取启动模拟器的命令行
- `process_native_api(input_type,process_input)`
- `start_simulator_uuid(uuid)`以uuid启动对应模拟器（暂不可用）
- `start_simulator_classic(simulator_type, multi_instance)`给定参数启动模拟器，该函数会直接返回对应的adb端口号。
- `stop_simulator_classic(simulator_type, multi_instance)`给定参数关闭模拟器
- `config_write(simulator_type, multi_instance, latest_adb_address = None,latest_command_line = None)`（给定模拟器类型并写入配置文件）
- `load_dict(uuid)`读取整个uuid对应的数据
- `return_bluestacks_type(pid)`读取pid对应的蓝叠模拟器类型

### 通用参数

simulator_type:（模拟器类型）

- bluestacks_nxt：蓝叠模拟器5国际版
- bluestacks_nxt_cn：蓝叠模拟器5中国版
- mumu：MuMu12模拟器
- yeshen：夜神模拟器
- mumu_classic：MuMu 6&MuMu X
- xiaoyao_nat：逍遥模拟器（非桥接模式）
- leidian：雷电模拟器
- wsa：适用于 Android™️ 的 Windows 子系统

multi_instance：

- mumu, yeshen, xiaoyao_nat, leidian中该参数为多开**数字**，以**0**为初始值
- bluestacks_nxt，bluestacks_nxt_cn中该参数为 蓝叠多开器/BlueStacks Multi-Instance Manager内对应模拟器的显示名称，建议使用编辑-复制粘贴以避免打错。**该参数大小写敏感**。
- wsa中该参数默认为127.0.0.1/localhost，无需填写，如果为其他设备的wsa，填写对应设备的ipv4地址或主机名。
- mumu_classic不支持多开模拟器使用不同adb端口。

uuid:
来源为 get_simulator_uuid(uuid)的返回值或/config/device.json内对应模拟器的id

config_write函数的latest_adb_address和latest_command_line如不填写将会自动获取。

::: warning
非常不建议使用 process_native_api，直接使用较为危险。
:::

## 支持的操作

- 结束模拟器
- 启动模拟器
- 获取模拟器adb端口
- 获取模拟器命令行参数
- 为模拟器生成唯一uuid
