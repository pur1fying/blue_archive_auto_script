import  uiautomator2
import subprocess

# 模拟器的端口号
simulator_port = 7555  # 替换为你想要连接的模拟器的端口号

# 构建 ADB 连接命令
adb_command = f"adb connect 127.0.0.1:{simulator_port}"

try:
    # 执行 ADB 连接命令
    subprocess.run(adb_command, shell=True, check=True)
    print(f"成功连接到模拟器端口 {simulator_port}")
except subprocess.CalledProcessError:
    print(f"无法连接到模拟器端口 {simulator_port}")
