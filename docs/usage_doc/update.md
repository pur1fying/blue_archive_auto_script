# 更新(Update)

## 自动更新
1. 当你点击**BlueArchiveAutoScript可执行程序**并成功启动UI后, 恭喜你, 你的BAAS版本已经是最新的了,因为BAAS在每次启动时都会从gitee拉取最新的源码
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