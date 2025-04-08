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
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

4. 启动
   ```bash
    python window.py
    ```
