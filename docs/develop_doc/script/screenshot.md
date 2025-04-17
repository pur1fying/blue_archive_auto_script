
# 从模拟器获取第一张截图(core\Screenshot.py)

```python
class Screenshot:
    def __init__(self, method, connection):
        self.connection = connection
        self.screenshot_instance = None
        self.init_screenshot_instance(method)

    def screenshot(self):
        image = self.screenshot_instance.screenshot()
        return image

    def init_screenshot_instance(self, method):
        if method == "nemu":
            self.screenshot_instance = NemuScreenshot(self.connection)
        elif method == "adb":
            self.screenshot_instance = AdbScreenshot(self.connection)
        elif method == "uiautomator2":
            self.screenshot_instance = U2Screenshot(self.connection)
        elif method == "scrcpy":
            self.screenshot_instance = ScrcpyScreenshot(self.connection)
```
这个类是BAAS源码中的`Screenshot`类的简化版本
<br>
初始化它需要两个参数:
1. `method` 
截图方式
<br>
目前可选的截图方式以及其优劣

| 方式           | 速度/ms | 无损截图 |
|--------------|-------|------|
| nemu         | 5-20  | 是    |
| adb          | 300   | 是    |
| uiautomator2 | 300   | 是    |
| scrcpy       | 17    | 否    |

类似C++多态, `init_screenshot_instance` 根据 `method` 初始化 `screenshot_instance` 为对应的截图类, 使得 `screenshot` 函数可以直接调用对应截图类的 `screenshot` 函数
<br>
2. `connection` 
<br>
这是另一个类([**Connection**](/develop_doc/script/Connection))的实例,它告诉了类该从哪个模拟器截图
简述:
Screenshot 类集成了多种截图方式
每一种截图方式的具体实现:
1. [nemu](/develop_doc/script/nemu#nemu-screenshot)
2. [adb]()
3. [uiautomator2]()
4. [scrcpy]()
