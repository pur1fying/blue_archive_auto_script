# BAAS_Cpp
- [仓库地址](https://github.com/pur1fying/BAAS_Cpp)

**note**:
1. BAAS_Cpp是一个安卓自动化脚本框架, 这是对blue_archive_auto_script的C++重构 , 目的是实现一个功能齐全的自动化脚本框架,简化开发流程
2. BAAS目前使用的一部分模块(如自动战斗, OCR) 都在此仓库实现
3. BAAS_Cpp根据核心代码, 衍生出以下不同的应用
   - `BAAS_APP` : 游戏`蔚蓝档案`自动战斗实现
   - `BAAS_auto_fight_workflow_checker`: 自动战斗工作流检查器, 用于检查自动战斗的工作流`json`文件是否正确
   - `ISA` : 游戏`学园偶像大师`日常脚本
   - `baas_ocr_server` : 跨平台的本地文字识别服务器
   - 编译以上应用参见[编译](#编译)部分

## 依赖

BAAS_Cpp 目前使用的一些重要库的版本如下

| 库              | 版本       |
|----------------|----------|
| `OpenCV`       | `4.9.0`  |
| `ONNX Runtime` | `1.22.0` |
| `CUDA`         | `12.2`   |
| `cuDNN`        | `9.9.0`  |

## 编译

### BAAS_APP
- **note**:
1. 目前仅支持Windows系统
2. CMake >= `3.22`
3. Visual Studio == `2022`
4. 可选择是否使用CUDA
    - [启用CUDA编译](#启用cuda编译baas-app)

#### 启用CUDA编译BAAS_APP
1. 需要先下载ONNX Runtime 1.22.0 预编译包
    - 下载链接
    ```
    https://github.com/microsoft/onnxruntime/releases/download/v1.22.0/onnxruntime-win-x64-gpu-1.22.0.zip
    ```
2. 解压并将`lib/onnxruntime_providers_cuda.dll`移动到`dll/Windows/`目录下
3. 接着在`x64 Native Tools Command Prompt for VS 2022`中运行

```shell
cmake -S . -B build -G Ninja -DBUILD_APP_BAAS=TRUE -D CMAKE_BUILD_TYPE=Release -D BAAS_APP_USE_CUDA=TRUE -D BUILD_BAAS_OCR=FALSE
```

```shell
cmake --build build --config Release -j 4
```

