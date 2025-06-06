# 安装配置
::: info
阅读前你可能需要知道
1. `BlueArchiveAutoScript.exe` 由 `installer.py` 生成, 每次更新时不会被覆盖, 但是`installer.py`如果有更新, 会被覆盖
:::
## 总览 (General)
自 [Ver 1.2.0](https://github.com/pur1fying/blue_archive_auto_script/releases/tag/v1.2.0)版本后, **BAAS**新增了安装配置 `setup.toml` , 你可以修改参数来自定义**BAAS**的安和运行

## 安装步骤
installer.py的运行步骤:
1. 检查`python`安装
2. 安装`pip`
3. 克隆 / 更新`BAAS`的源码
4. 安装`requirements.txt`中的依赖
5. 启动

## 参数说明
### dev
- **type**: `bool`
- **description** : 如果为 `true`, 则不会从远程更新代码

### refresh
- **type**: `bool`
- **description** : 如果为 `true`, **git会覆盖本地所有修改**

### launch
- **type**: `bool`
- **description** : 如果为 `true`, 则跳过[安装步骤](#安装步骤)中的1-4步

### force_launch
- **type**: `bool`
- **description** : 如果为 `false`, 则会关闭上一个已经启动的`BAAS`

### internal_launch
- **type**: `bool`
- **description** : 一般不需修改, 如果为 `true`, 则会使用不同操作系统对应的特殊命令启动

### no_build
- **type**: `bool`
- **description** : 如果为 `false`, 则会重新编译installer.py生成对应`BlueArchiveAutoScript.exe`

### debug
- **type**: `bool`
- **description** : 如果为 `true`, 则更新完成后不会关闭终端窗口

### use_dynamic_update
- **type**: `bool`
- **description** : 如果为 `true`, 则会使用`deploy/installer/installer.py`进行更新

### source_list
- **type**: `list`
- **description** : 下载源的列表, 如果下载失败, 则会根据列表中的顺序进行重试

### package_manager
- **type**: `str`
- **description** : 用于安装python包的工具
- **note**: 目前只支持`pip`

### runtime_path
- **type**: `str`
- **description** : 自定义运行时python路径

### linux_pwd
- **type**: `str`
- **description** : 你的linux系统的密码
::: warning
**仅用于安装, 不会用于其他任何用途**
:::
### REPO_URL_HTTP
- **type**: `str`
- **description** : 获取/更新`BAAS`源码的地址, 可选项如下
   1. `github`原始仓库, 可直连`github`用户可选
       ```shell
       https://github.com/pur1fying/blue_archive_auto_script.git
       ```
   2. `gitee`镜像仓库, 默认地址 ,国内用户推荐
       ```shell
       https://gitee.com/pur1fy/blue_archive_auto_script.git
       ```
   3. `gitcode`镜像仓库, 国内用户备用地址
       ```shell
       https://gitcode.com/m0_74686738/blue_archive_auto_script.git
       ```
### GET_PIP_URL 
- **type**: `str`
- **description** : `get-pip.py`的下载地址

### GET_UPX_URL
- **type**: `str`
- **description** : UPX的下载地址

### GET_ENV_PATCH_URL
- **type**: `str`
- **description** : 环境补丁文件的地址

### GET_PYTHON_URL
- **type**: `str`
- **description** : Python的下载地址

### BAAS_ROOT_PATH
**type**: `str`
**description**: 安装根目录, 一般不需要修改。 如需修改, 切记填写绝对路径

### TMP_PATH
**type**: `str`
**description**: 临时文件夹, 一般不需要修改

### TOOL_KIT_PATH
**type**: `str`
**description**: 一般不需要修改



## 默认配置
```toml
[General]
dev = false
refresh = false
launch = false
force_launch = false
internal_launch = false
no_build = true
debug = false
use_dynamic_update = false
source_list = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.ustc.edu.cn/pypi/web/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.doubanio.com/simple",
    "https://mirrors.huaweicloud.com/repository/pypi/simple",
    "https://mirrors.cloud.tencent.com/pypi/simple",
    "https://mirrors.163.com/pypi/simple",
    "https://pypi.python.org/simple",
    "https://pypi.org/simple",
]
package_manager = "pip"
runtime_path = "default"
linux_pwd = ""

[URLs]
REPO_URL_HTTP = "https://gitee.com/pur1fy/blue_archive_auto_script.git"
GET_PIP_URL = "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/get-pip.py"
GET_UPX_URL = "https://ghp.ci/https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip"
GET_ENV_PATCH_URL = "https://gitee.com/kiramei/blue_archive_auto_script_assets/raw/master/env_patch.zip"
GET_PYTHON_URL = "https://gitee.com/pur1fy/blue_archive_auto_script_assets/raw/master/python-3.9.13-embed-amd64.zip"

[Paths]
BAAS_ROOT_PATH = ""
TMP_PATH = "tmp"
TOOL_KIT_PATH = "toolkit"
```
