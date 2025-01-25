# 在Windows操作系统安装BAAS
::: tip
还没下载？来[这里](../downloads)
:::

## 安装步骤
- 解压Release或qq交流群中的下载包，双击`BlueArchiveAutoScript.exe`安装环境，请耐心等待。
安装完成后，BAAS 的ui界面将自动启动。
- [视频教程](https://www.bilibili.com/video/BV19y421e7XF/?spm_id_from=333.337.search-card.all.click)

## 问题解答
### 1.确保安装路径没有中文
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

### 2.双击BlueArchiveAutoScript.exe后命令行界面全黑无反应
- **解决方法** 
1. 打开windows设置
2. 搜索并进入```病毒和威胁防护```
3. 点击```"病毒和威胁防护"设置```栏下的```管理设置```
4. 关闭```实时保护```

- **原因:** 未知, 可能windows误识为病毒
