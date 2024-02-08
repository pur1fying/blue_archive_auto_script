## 使用方法：
```
import device_operation

device_operation.api(operation,simulator_type,multi_instance) #注：部分参数注释会表明用哪几个参数
```
## 操作类型：
请查阅simulator_api.py源代码，命名非常易读，包含注释
由于可能会实时更新，故不一定在此处能完整贴出全部操作类型
```
"get_adb_address"
"get_running_simulators"
"get_adb_address_by_uuid"
"get_simulator_uuid"
"terminate_simulator_name"
"terminate_simulator_pid"
"get_simulator_commandline_name"
"get_simulator_commandline_pid"
"get_simulator_commandline_uuid"

```
## 支持的操作
结束进程 启动进程 获取模拟器adb端口 获取模拟器命令行参数 为模拟器生成唯一uuid