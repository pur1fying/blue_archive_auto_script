## 在安卓真机运行游戏+电脑运行BAAS
1. 使用 USB 线连接安卓机和电脑。
2. 在手机内的 开发者模式，打开 ADB调试。
3. 查询手机的 serial
```shell
C:\Users\username>adb devices
List of devices attached
xxxxxxxx        device
```

更改分辨率
```shell
adb -s <serial> shell wm size 720x1280
```
修改[端口号](/develop_doc/script/config#adbport)

运行 **BAAS**

恢复分辨率
```shell
adb -s <serial> shell wm size reset
```
