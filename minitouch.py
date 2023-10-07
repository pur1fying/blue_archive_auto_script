import os

# 假设 image_file 包含文件名，例如 "image.jpg"
image_file = "image.jpg"
directory_path = "\src\common_button"  # 目录路径

# 使用 os.path.join 合并目录路径和文件名
path = os.path.join(directory_path, image_file)

print(path)  # 输出完整的文件路径，例如 "/src/common_button/image.jpg"
