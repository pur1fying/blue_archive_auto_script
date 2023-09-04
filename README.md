# Thank you for down loading blue archive auto script

## 1.使用指南

### 1.1如何使用baas
下载安卓模拟器，下载蔚蓝档案，**模拟器的尺寸一定要设置为1280x720，确定电脑连接到模拟器，并且游戏在主页面**后，运行main函数即可
>baas 后续会有交互的ui界面，可以实时调整运行时参数

main函数中一些参数可以设置，具体可以看main函数源码的注释

 ### 1.2 baas是如何运作的
**uiautomator2**：`uiautomator2` 是一个用于自动化 Android 设备的 Python 库，通过该库与模拟器设备连接并进行截图，点击，滑动等操作。

**ocr**：
详见https://github.com/breezedeus/CnOCR
通过ocr识别模拟器截图中的文字，并提取其中特征信息来判断当前页面是游戏中哪个页面

**threading**：每隔一定时间开启一个截图并判断位置的线程，将结果存入self.pos列表中（该列表的元素数不大于2），并在调用self.pd_pos函数时，如果self.pos中两个元素表示的位置相同，就确定了当前位置。这样做的好处是分离了屏幕截屏进程，提高了效率和位置判断的准确性


