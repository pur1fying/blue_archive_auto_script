import subprocess
import tkinter as tk
from tkinter import filedialog


# def start_external_program(program_path):
#     try:
#         # 启动模拟器程序
#         process = subprocess.Popen(program_path)
#         # 设置最长等待时间为3分钟
#         process.wait(timeout=180)
        
#         # 如果程序启动成功（returncode为None），输出成功消息
#         if process.returncode is None:
#             print(f"启动外部程序成功: {program_path}")
#         else:
#             print(f"启动外部程序失败: {program_path}")
#     except subprocess.TimeoutExpired:
#         print(f"启动外部程序超时: {program_path}")
#     except Exception as e:
#         print(f"启动外部程序失败: {e}")
def start_emulator(config):
    program_address = self.config.get("program_address")
    if program_address:
        try:
            subprocess.Popen(program_address)
            print("程序已成功启动")
        except Exception as e:
            print(f"启动程序时出错：{e}")
    else:
        print("未指定程序地址")
