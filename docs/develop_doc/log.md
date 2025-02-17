# 日志 `class Logger`
对应文件路径 : `"core/utils.py"`, 
::: info
Wiki中所有与`logger`有关的变量都是指`Logger`类的实例
:::
## Members
### `self.logger`
**type**: `Logger`

### `self.logger_signal`
**type**: `pyqtSignal`
**description**: 用于发送日志信号, 使UI主界面显示日志(window.py)
**note**: 信号为`None`时日志会打印在终端(main.py)

## 使用须知
### 1.语言
日志的所有**静态字符串(Static String)**请都使用**英文(English)**
### 2.使用方法
- `Baas_thread`的成员`self.logger`是一个Logger对象, module中所有函数的`self`成员变量都是`Baas_thread`实例, 所以可以直接使用以下方法

```python
self.logger.info("Info Message")
self.logger.warning("Warning Message")
self.logger.error("Error Message")
self.logger.critical("Critical Message")
self.logger.line()
```

### 何时使用对应级别日志
#### ```info```
BAAS正常运行日志
#### ```warning```
遇到了一些异常情况但是BAAS可以自行解决的异常
#### ```error```
**BAAS**无法在当前任务模块自行解决的异常, 需要**重启游戏和对应任务**或停止**BAAS**
#### ```critical```
参数设置错误无法启动**BAAS** **|** 无法执行当前任务 的异常, 通常每个独立的任务出先无法解决的错误时会使用[**error**](#error)级别
#### ```line```
分隔上下文时使用, 用于区分不同的任务