# Baas on Android
本文件为修改说明与计划。

## GUI
baas 的 GUI 使用 PyQt5 + PyQt-Fluent-Widgets 实现。

1. PyQt5 虽然支持部署到 Android 上，但资料少且旧，构建难度大
    * 本着最小化改动的原则，目前借助 qtpy 兼容层 + monkey patch，将 PyQt5 迁移到了 PySide6
    * 从长期来看，建议迁移 PyQt5 到 PySide6 或 qtpy
2. PyQt-Fluent-Widgets 该组件库对触摸屏的支持较差（特别是滑动）
    * 暂时没有什么改动

## OCR
baas 的 OCR 使用 C++ 实现，底层为 onnxruntime + paddleocr，为独立进程运行，C++ 与 Python 之间通过内存共享与 HTTP 进行进程间通信。

1. 在 Android 上使用内存共享方案难度大
    * 目前将 RapidOCR 的 Android 版本封装为了库，让 Python 调用，完全替换原有 C++ 方案
    * 从长期来看，为了保持一致性，可能需要将 C++ 部分改为以动态链接库或 Python 扩展的形式与 Python 通信

## 设备控制
