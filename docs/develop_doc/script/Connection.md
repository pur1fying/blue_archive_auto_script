# 模拟器连接`class Connection`
对应文件路径 : `"core/device/connection.py"`
::: info
阅读这部分内容前你可能需要了解
1. 如何用[ADB](https://developer.android.com/tools/adb?hl=zh-cn)管理安卓设备的连接
2. 一些有关计算机网络的知识
:::
## 总览
1. **检查设备连接**
- **related configs** : [adbIP](/develop_doc/script/config#adbip), [adbPort](/develop_doc/script/config#adbiport)
- **related functions** : [self.detect_device](#detect-device) 

2. **检查游戏包**
- **related configs** : [server](/develop_doc/script/config#server)
    - Supports multiple servers (`CN`, `Global`, `JP`) for package configuration.
    - Handles package-related exceptions gracefully.

3. **检查模拟器设置**
    - Executes shell commands on connected devices.
    - Retrieves device properties using ADB.

---

## Constructor
```python
def __init__(self, Baas_instance)
```
### **Args**:
#### `Baas_instance`: Baas_thread 的实例

### **Members**:
#### `self.activity`
**type** : str
#### `self.package`
**type** : str
#### `self.server`
**type** : str
#### `self.Baas_thread`
**type** : `Baas_thread` Object
#### `self.logger`

#### `self.config_set`
#### `self.config`
#### `self.static_config`
#### `self.adbIP`
#### `self.adbPort`
---

## Key Methods

### `detect_device()`
Identifies available devices and sets the active serial.
### `adb_connect()`
Attempts to connect to the specified device serial.
### `check_serial()`
Validates and revises the device serial if needed.

### `detect_package()`
Detects the appropriate package based on the server configuration.
### `check_package_exist(server)`
Verifies if a package exists for the specified server.
### `auto_detect_package()`
Automatically selects an available package if multiple are found.

### `list_devices()`
Returns a list of connected devices.
### `adb_shell_bytes(command, stream=False)`
Executes shell commands on the connected device.
### `adb_getprop(name)`
Retrieves a property value from the device.

### `set_serial(serial)`
Updates the active device serial in the configuration.
### `get_serial()`
Retrieves the active device serial.
### `get_package_name()`
Returns the currently detected package name.
### `get_server()`
Returns the server type (`CN`, `Global`, `JP`).
### `get_activity_name()`
Returns the current activity name.

### `is_mumu_family()`
Checks if the device belongs to the MuMu family.
### `is_mumu12_family()`
Specifically checks for MuMu12 devices.
### `check_mumu_keep_alive()`
Ensures the MuMu app keep-alive feature is properly configured.

---

## Exception Handling

The class uses the `RequestHumanTakeOver` exception to signal scenarios requiring manual intervention, such as:
- No devices detected.
- Multiple devices found without a specified serial.
- Package detection failures.
- ADB connection issues.

---

## Logging
The `logger` is used extensively for:
- Informational messages about the current state.
- Warnings for potential issues.
- Errors requiring user attention.

---

## Dependencies
- **Python Modules**: `re`, `adbutils`
- **Custom Modules**: `core.exception`

---

## Notes
- Ensure the `adb` command-line tool is installed and accessible in your environment.
- Use the provided logger for debugging and monitoring operations.
- Update the static configuration (`static_config`) as needed for new servers or packages.

--- 

## Example Usage
```python
from core.exception import RequestHumanTakeOver
from module.device.connection import Connection

# Initialize BAAS instance
baas_instance = Baas()

# Create a Connection object
connection = Connection(baas_instance)

# Detect and connect to a device
connection.detect_device()

# Check for available packages
connection.detect_package()

# Execute ADB commands
device_serial = connection.get_serial()
print(f"Connected to device: {device_serial}")
```
