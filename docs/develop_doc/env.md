# 配置开发环境

## 代码编辑器 (IDE)
- 推荐使用主流Python代码编辑器[Pycharm](https://www.jetbrains.com/pycharm/) 或 [VSCode](https://code.visualstudio.com/)

## 克隆仓库
1. 首先确保安装 [Git](https://git-scm.com/)

2. 克隆仓库
```sh
git clone https://github.com/pur1fying/blue_archive_auto_script.git
```

## 配置Python环境

**BAAS** 的主程序使用 Python 3.9, 推荐安装相同版本

下面将详尽叙述可选的几种配置环境的方法

## 方案一: 使用 Anaconda (推荐)

### 1. 安装 [Anaconda](https://www.anaconda.com/products/distribution)
### 2. 创建3.9.21版本的python环境
```sh
conda create -n baas_env python==3.9.21
```

### 3. 激活环境

```shell
conda activate baas_env
```

### 4. 安装依赖
- Linux / MacOS

```shell
pip install -r requirements-linux.txt
```
- Windows
```sh
pip install -r requirements.txt
```

### 5. 启用环境
#### 在Pycharm中使用conda环境

按照以下步骤启用刚刚创建的`baas_env`环境

![use_conda_env_in_pycharm_1](/assets/develop_env/use_baas_env_in_pycharm_1.png) 

![use_conda_env_in_pycharm_2](/assets/develop_env/use_baas_env_in_pycharm_2.png) 

![use_conda_env_in_pycharm_3](/assets/develop_env/use_baas_env_in_pycharm_3.png) 


## 方案二: 使用 python venv + pip

### 1. 创建虚拟环境
```sh
python -m venv .venv
```

### 2. 激活环境
```sh
.\.venv\Scripts\activate
```

### 3. 安装依赖
```sh
pip install -r requirements.tx
```

## 方案三: 使用 uv

### 1. 安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)
### 2. 创建虚拟环境
```sh
uv venv --python 3.9
```
### 3. 激活环境
```sh
.\.venv\Scripts\activate
```
### 安装依赖
```sh
uv sync
```


