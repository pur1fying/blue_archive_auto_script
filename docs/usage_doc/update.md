# 更新(Update)

## 如何查询当前版本

### 方法1
- GUI界面, 点击更新设置 --> BAAS更新设置
![query_version_1.png](/assets/update/query_version_1.png)

### 方法2
- 点击GUI右上角时钟按钮, 如果最新记录与github版本一致, 则表示你当前版本是最新的
![query_version_2.png](/assets/update/query_version_2.png)
![query_version_3.png](/assets/update/query_version_3.png)

## 自动更新
1. 当你点击**BlueArchiveAutoScript可执行程序**并成功启动UI后, 恭喜你, 你的BAAS版本已经是最新的了,因为BAAS在每次启动时都会从远程仓库拉取最新的源码
2. 可执行程序由pyinstaller打包**installer.py**而来

所以运行可执行程序等效于以下shell命令

```shell
"env/Script/python.exe" installer.py
```
**related issue:** [#217](https://github.com/pur1fying/blue_archive_auto_script/issues/217)

## 如何跳过更新直接启动BAAS
在BAAS目录下, 打开cmd, 输入以下命令
```shell
"env/Script/python.exe" window.py
```
