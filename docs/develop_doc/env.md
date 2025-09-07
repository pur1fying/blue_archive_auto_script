# 配置开发环境

通常，专业的IDE会自动配置开发环境，如果您了解开发环境的配置，则可以不用参照下面的步骤。

**BAAS 的主程序使用 Python 3.9，因此建议安装Python 3.9 或手动设置检查兼容性（若使用Pycharm 进行开发）**

下面将详尽叙述可选的几种配置环境的方法

## 方案一: 使用 python venv + pip

1.  ### 创建虚拟环境

    ```sh
    python -m venv .venv
    ```
2.  ### 激活环境

    ```sh
    .\.venv\Scripts\activate
    ```
3.  ### 安装依赖

    ```sh
    pip install -r requirements.tx
    ```

## 方案二: 使用 uv

1. ### 安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)
2.  ### 创建虚拟环境

    ```sh
    uv venv --python 3.9
    ```
3.  ### 激活环境

    ```sh
    .\.venv\Scripts\activate
    ```
4.  ### 安装依赖

    ```sh
    uv sync
    ```

## 方案三: 使用 Anaconda

1. ### 安装 [Anaconda](https://www.anaconda.com/products/distribution)
2.  ### 创建3.9.21版本的python环境

    ```sh
    conda create -n baas_env python==3.9.21
    ```
3.  ### 激活环境

    ```shell
    conda activate baas_env
    ```
4.  ### 安装依赖

    *   Linux

        ```shell
        pip install -r requirements-linux.txt
        ```
    *   Windows

        ```sh
        pip install -r requirements.txt
        ```
