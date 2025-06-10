# 在 MacOS / Linux 操作系统安装BAAS
::: warning
1. 请先检查你的操作系统架构 / 版本, 检查是否适配[预编译的BAAS_ocr_server](/develop_doc/script/ocr#预编译版本-prebuild-version)
2. 我们默认你会使使用一些基本的命令行指令
:::


## 安装步骤

1. 安装miniconda / conda
2. 创建python虚拟环境
    ```bash
    conda create -n baas_env python=3.9.21
    conda activate baas_env
    ```
3. 安装依赖
   ```bash
    pip install -r requirements.txt
    ```
   国内用户使用清华源加速

   ```bash
    pip install -r requirements-linux.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

4. 启动
   ```bash
    python window.py
    ```

## Mac 用户须知

1. 首次启动gui可能会无法启动ocr报错, 你需要将 安装目录/core/ocr/baas_ocr_client/bin/config/global_setting.json中 "/ocr/server/host" 改为 "localhost"
2. 将adb可执行程序放置于python的adbutils包, 路径如下, 可执行程序可在q群群文件下载
![Mac_adb_path.png](/assets/install/Mac_adb_path.png)
