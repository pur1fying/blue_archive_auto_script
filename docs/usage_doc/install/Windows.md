# 在Windows操作系统安装BAAS
::: tip
还没下载？来[这里](../downloads)
:::

## 选择合适的安装包
BAAS提供以下三种安装包
### .exe安装包
   - ![exe_installer.png](/assets/install/exe_installer.png)
    - **description**: `deploy/installer/installer.py` 打包出的安装包, 体积最小, 需要安装python环境, clone仓库
    - **operation**: 下载后双击运行即可

### fulL_env的安装包 (**最为推荐下载**)
   - ![full_env_installer.png](/assets/install/full_env_installer.png)
   - **description**: .exe安装包全部运行完毕后压缩后的安装包, 不需要安装环境, 自带四份配置(国服, 国际服, 日服, Steam国际服), 
   - **operation**: 下载后解压, 双击运行`BlueArchiveAutoScript.exe`即可
   
### with_config安装包 (**mirror酱用户可选**)
   - ![with_config_installer.png](/assets/install/with_config_installer.png)
   - **description**: .exe安装包 与 setup.toml (安装配置) 一起压缩的安装包 
   - **description**: .exe安装包 , setup.toml (安装配置) , 和四份运行配置(国服, 国际服, 日服, Steam国际服)一起压缩的安装包 
   - **operation**: 下载后解压, 用记事本打开`setup.toml`文件修改`mirrorc_cdk`为你的cdk, 双击运行`BlueArchiveAutoScript.exe`即可

## 简易安装教程

- 解压Release或[qq交流群](/usage_doc/qq_group_regulation)中的安装包，双击`BlueArchiveAutoScript.exe`安装环境，请耐心等待。
安装完成后, BAAS的UI界面将自动启动。
- [视频教程](https://www.acfun.cn/v/ac47360708_2)

## Mirror酱CDK
为了改善更新体验，从[v1.4.0](https://github.com/pur1fying/blue_archive_auto_script/releases/tag/v1.4.0)版本开始, **BAAS**正式接入Mirror酱更新服务

### 什么是Mirror酱？
- **description**: Mirror酱是一个第三方应用分发平台, 开源应用提供更新辅助服务, Mirror酱将为BAAS用户提供免费的更新检查服务以及**付费**的稳定更新服务. 
- **note**:
  1. 你完全可以选择不使用Mirror酱更新, 新版本的BAAS仍然适配原来的更新方式，但是下载过程可能不稳定。你可能会遇到 [#278](https://github.com/pur1fying/blue_archive_auto_script/issues/278)  [#294](https://github.com/pur1fying/blue_archive_auto_script/issues/294)  [#314](https://github.com/pur1fying/blue_archive_auto_script/issues/314) 中发生的问题
  2. 如果你购买并填写Mirror酱CDK, BAAS将从Mirror酱下载站获取更新文件, 下载速度更稳定. 另外CDK不仅可以用于BAAS的更新, 还可以用于一系列其他开源脚本的更新, 详见[Mirror酱官网](https://mirrorchyan.com/zh/projects?rid=BAAS_repo&source=BAAS_WIKI)
  3. 无论是国内外用户, 都可以使用Mirror酱

### 如何使用CDK?
- **description**: 下载[with_config安装包](#with-config安装包-mirror酱用户可选) 或 [full_env安装包](#full-env的安装包-最为推荐下载), 在`setup.toml`中填写如下字段
```toml
[General]
mirrorc_cdk = "你的CDK"
```
填写完毕后保存再次运行, **BAAS**安装器出现如下日志表示成功
- 成功使用Mirror酱安装
![mirrorc_install_success.png](/assets/install/mirrorc_install_success.png)
- 成功使用Mirror酱更新
![mirrorc_update_success.png](/assets/install/mirrorc_update_success.png)

::: warning
请勿将setup.toml分享给陌生人, 否则你的cdk会被泄漏
:::

- **related config**: [mirrorc_cdk](/usage_doc/install/setup_config#mirrorc-cdk)

## 问题解答
### 确保安装路径没有中文
- **报错截图** 
![中文路径无法启动ui](/assets/install/problem_fail_to_start_ui_for_path_with_chinese.png)

- **原因:** 
  - UI使用QT框架的限制
- **解决方法**
  - 方法1. 将BAAS安装路径更改为不含中文的路径
  - 方法2. 将本应该在安装时添加的环境变量添加回去就好了
     - **具体操作环节为** `windows设置→系统→关于→高级系统设置→高级→环境变量→新建→填写变量名与变量值→点两下确定关闭窗口`
     ![solve2](/assets/install/add_QT_plugins_into_PATH.png)
     - **变量名:** `QT_QPA_PLATFORM_PLUGIN_PATH`
     - **变量值:** 填写已知兼容的Qt路径 ↓
        1. Baas的Qt目录： `（Baas的安装路径）\BlueArchiveAutoSctipt\env\Lib\site-packages\PyQt5\Qt5\plugins`
        2. MuMu模拟器的Qt目录： `（MuMu模拟器安装路径）\MuMu Player 12\shell\plugins`
        3. 自己装的Qt： 自己研究，在py的安装目录下或者在AppData\Local的py软件配置文件夹里

  **note:** 变量值填写非MuMu模拟器的Qt目录时可能会与MuMu模拟器所需的Qt发生冲突，导致MuMu模拟器无法打开，已知MUMU模拟器与最新的Qt5.15.11不兼容，非必要不建议填写自己安装的Qt（要用到时自己改）。
  **因为MUMU模拟器的Qt与Baas兼容，所以在发生冲突无法打开MuMu模拟器时建议在变量值处填写** `MuMu模拟器的Qt目录` 删除变量也可以正常打开MuMu模拟器。

### 双击BlueArchiveAutoScript.exe后命令行界面全黑无反应
- **解决方法** 
1. 打开windows设置
2. 搜索并进入```病毒和威胁防护```
3. 点击```"病毒和威胁防护"设置```栏下的```管理设置```
4. 关闭```实时保护```

- **原因:** 未知, 可能windows误识为病毒


### 安装命令行出现如下报错

![install_request400.png](/assets/install/install_request400.png)

- **解决方法** 
1. 打开**BAAS**安装目录下的setup.toml, 尝试修改[REPO_URL_HTTP](/usage_doc/install/setup_config#repo-url-http)为其他地址 (gitcode / github)
![setup_toml_REPO_URL_HTTP.png](/assets/install/setup_toml_REPO_URL_HTTP.png)
2. 使用[Mirror酱更新](#mirror酱cdk) (需要购买CDK)

- **原因:** 你可能被gitee拒绝服务
