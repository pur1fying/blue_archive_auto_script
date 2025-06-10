# 开发环境
如果你已经安装了Python环境，可以跳过这一步。

## 在Windows下搭建开发环境

### 1.安装[Anaconda](https://www.anaconda.com/products/distribution)
### 2.创建3.9.18版本的python环境: 
```shell
conda create -n baas_env python==3.9.18
```
### 3.激活环境:
```shell
conda activate baas_env
```
### 4.安装依赖:
```shell
pip install -r requirements-linux.txt
```
