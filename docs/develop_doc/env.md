# 配置开发环境

## 代码编辑器 (IDE)
- 推荐使用主流Python代码编辑器 [Pycharm](https://www.jetbrains.com/pycharm/) 或 [VSCode](https://code.visualstudio.com/)

## 克隆仓库
```shell
git clone https://github.com/pur1fying/blue_archive_auto_script.git
```

## 配置Python环境

**BAAS** 的主程序使用 Python 3.9, 推荐安装相同版本

下面将详尽叙述可选的几种配置环境的方法，以下方法任选其一即可
我们推荐使用IDE自带的虚拟环境功能，快速创建和管理虚拟环境
(例如 Pycharm 的 [Virtualenv](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html) 功能)
同时，也可以使用下面的方案来手动创建和管理虚拟环境


## 方案一: 使用 python venv + pip

### 1. 创建虚拟环境
```shell
python -m venv .venv
```

### 2. 激活环境
```shell
.\.venv\Scripts\activate
```

### 3. 安装依赖
- Linux / MacOS
```shell
pip install -r requirements-linux.txt
```
- Windows
```shell
pip install -r requirements.txt
```


## 方案二: 使用 uv

### 1. 安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)
### 2. 创建虚拟环境
```shell
uv venv --python 3.9
```
### 3. 激活环境
```shell
.\.venv\Scripts\activate
```
### 安装依赖
```shell
uv sync
```

## 方案三: 使用 Anaconda

### 1. 安装 [Anaconda](https://www.anaconda.com/products/distribution)
### 2. 创建3.9.21版本的python环境
```shell
conda create -n baas_env python==3.9.21
```

### 3. 激活环境

```shell
conda activate baas_env
```

### 4. 安装依赖
- Linux / MacOS
```shell
conda install --yes --file requirements-linux.txt
```
- Windows
```shell
conda install --yes --file requirements.txt
```
