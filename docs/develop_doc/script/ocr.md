# 文字识别(OCR)

## 简介(Introduction)
OCR 已使用[C++重构](https://github.com/pur1fying/BAAS_Cpp), 作为BAAS的子进程, 通过http请求为BAAS提供文字识别服务

- 相关文件路径:
    1. **BAAS**实际调用的ocr:
        ```shell
        /core/ocr/ocr.py    
        ```
    2. ocr安装脚本:
        ```shell
        /core/ocr/baas_ocr_client/server_installer.py
        ```
    3. ocr客户端:
        ```shell
        /core/ocr/baas_ocr_client/Client.py
        ```
    4. ocr可执行程序安装目录:
        ```shell
        /core/ocr/baas_ocr_server/bin
        ```
## 预编译版本(Prebuild Version)
1. **BAAS_ocr_server**使用github-action自动构建在不同操作系统的可执行程序, 并推送至[github仓库](https://github.com/pur1fying/BAAS_Cpp_prebuild)
2. **BAAS**使用core/ocr/baas_ocr_client/server_installer.py自动 **安装/更新** 最新的可执行程序
3. 可使用的预编译版本
    -   | 操作系统    | 架构     | 操作系统版本       | 可执行程序分支                                                                        |
        |---------|--------|--------------|--------------------------------------------------------------------------------|
        | Windows | x86_64 | win10/win11  | [windows-x64](https://github.com/pur1fying/BAAS_Cpp_prebuild/tree/windows-x64) |
        | Linux   | x86_64 | ubuntu-22.04 | [linux-x64](https://github.com/pur1fying/BAAS_Cpp_prebuild/tree/linux-x64)     |
        | MacOS   | arm64  | 最新版本         | [macos-arm64](https://github.com/pur1fying/BAAS_Cpp_prebuild/tree/macos-arm64) |
4. 如果你的操作系统无法使用预编译版本, 可能需要自行编译 / 联系开发者适配
5. **BAAS_ocr_server** 在编译时默认不支持cuda, 原因是使用cuda会使依赖的dll增加约500MB, 但是可以自行编译支持cuda的版本, 仅需要在CMake选项中设置BAAS_OCR_SERVER_USE_CUDA为ON

## **配置列表(Config)**

配置文件路径:
```shell
可执行程序安装目录/config/global_setting.json
```

| 编号 | 配置名                              | 说明                   |
|----|----------------------------------|----------------------|
| 1  | **/ocr/gpu_id**                  | 如果使用cuda加速, 推理的gpu编号 |
| 2  | **/ocr/num_thread**              | onnxruntime推理的线程数    |
| 3  | **/ocr/enable_cpu_memory_arena** | 是否使用内存池              |
| 4  | **/ocr/server/host**             | 服务的ip地址              |
| 5  | **/ocr/server/port**             | 服务的端口号               |
| 6  | **/log/flush_interval**          | 日志刷新间隔时间(ms)         |

**note**: 
1. 1, 2, 3 项是初始化模型时可以指定的参数(当没有以任何形式指定时, 使用配置文件中的默认值)
2. 考虑到onnxruntime使用gpu推理时库的大小, BAAS_ocr_server的发行版编译时**没有支持cuda**, 但是可以自行编译支持cuda的版本

## **API列表**

### 初始化模型

#### **请求信息**
| 方法     | URL           |
|--------|---------------|
| `POST` | `/init_model` |

#### **请求体**
| 参数                     | 类型          | 必填 | 说明      |
|------------------------|-------------|----|---------|
| `language`             | `List[str]` | 是  | 语言      |
| `gpu_id`               | `int`       | 否  | gpu id  |
| `num_thread`           | `int`       | 否  | 推理线程数   |
| `EnableCpuMemoryArena` | `bool`      | 否  | 是否使用内存池 |

**note**: 
1. 当使用内存池时, BAAS_ocr_server会占用更多内存, 推理速度略有增加
2. num_thread越大, 推理速度越块, 经测试4时达最快速度
3. language字段[可选的语言](#可选的语言)

#### **响应体**
| 参数                     | 类型          | 说明        |
|------------------------|-------------|-----------|
| `ret`                  | `List[int]` | 每个模型初始化状态 |
| `time`                 | `int`       | 初始化时间(ms) |

`ret`中每个数字含义如下表

| 值   | 含义        |
|-----|-----------|
| `0` | 不存在的语言    |
| `1` | `success` |
| `2` | 已经初始化过的语言 |

### 释放模型

#### **请求信息**
| 方法     | URL              |
|--------|------------------|
| `POST` | `/release_model` |


#### **请求体**
| 参数         | 类型          | 必填 | 说明       |
|------------|-------------|----|----------|
| `language` | `List[str]` | 是  | 语言       |

**note**: onnxruntime C++ 库存在内存泄露问题, 所以请勿频繁 加载 / 释放 模型

#### **响应体**
| 参数                     | 类型           | 说明        |
|------------------------|--------------|-----------|
| `ret`                  | `List[bool]` | 每个模型释放    |
| `time`                 | `int`        | 释放总时间(ms) |

`ret`中每个bool含义如下表

| 值       | 含义        |
|---------|-----------|
| `false` | 不存在的语言    |
| `true`  | `success` |

### 释放所有模型

#### **请求信息**
| 方法    | URL            |
|-------|----------------|
| `Get` | `/release_all` |

#### **响应体**

仅有一个`int`, 表示释放总时间(ms)


### 获取图像的文字框

暂未实现


[//]: # ()
[//]: # (#### **请求体**)

[//]: # (| 参数                          | 类型             | 必填 | 说明           |)

[//]: # (|-----------------------------|----------------|----|--------------|)

[//]: # (| `/image/pass_method`        | `unsigned int` | 是  | 图像传递方式       |)

[//]: # (| `/image/local_path`         | `string`       | 否  | 图像本地路径       |)

[//]: # (| `/image/shared_memory_name` | `string`       | 否  | 图像数据所在的共享内存名 |)

### ocr_for_single_line

#### **请求信息**
| 方法     | URL                    |
|--------|------------------------|
| `POST` | `/ocr_for_single_line` |

#### **请求体**
| 参数                          | 类型             | 必填 | 说明           |
|-----------------------------|----------------|----|--------------|
| `/language`                 | `string`       | 是  | 语言           |
| `/candidates`               | `string`       | 否  | 可能出现的字       |
| `/image/pass_method`        | `unsigned int` | 是  | 图像传递方式       |
| `/image/local_path`         | `string`       | 否  | 图像本地路径       |
| `/image/shared_memory_name` | `string`       | 否  | 图像数据所在的共享内存名 |
| `/image/resolution`         | `[int, int]`   | 否  | 图像尺寸         |

**note**:
1. [pass_method](#图像传递方式-pass-method)填写说明

#### **响应体**
| 参数            | 类型            | 说明                        |
|---------------|---------------|---------------------------|
| `ocr_time`    | `int`         | ocr耗费时间                   |
| `time`        | `int`         | 处理请求总时间(ocr_time与解码图像的时间) |
| `text`        | `string`      | ocr得到的文字                  |
| `char_scores` | `List[float]` | 每个文字的得分                   |

### ocr

#### **请求信息**
| 方法     | URL    |
|--------|--------|
| `POST` | `/ocr` |


#### **请求体**
| 参数                          | 类型             | 必填 | 说明           |
|-----------------------------|----------------|----|--------------|
| `/language`                 | `string`       | 是  | 语言           |
| `/candidates`               | `string`       | 否  | 可能出现的字       |
| `/image/pass_method`        | `unsigned int` | 是  | 图像传递方式       |
| `/image/local_path`         | `string`       | 否  | 图像本地路径       |
| `/image/shared_memory_name` | `string`       | 否  | 图像数据所在的共享内存名 |
| `/image/resolution`         | `[int, int]`   | 否  | 图像尺寸         |
| `ret_options`               | `unsigned int` | 否  | 返回选项         |

**note**:
1. **ret_options**

    | 值                     | 含义                 |
    |-----------------------|--------------------|
    | `ret_options & 0b001` | 为真时返回`angle_net`信息 |
    | `ret_options & 0b010` | 为真时返回每个字符得分        |
    | `ret_options & 0b100` | 为真时返回所有字符框         |
2. [pass_method](#图像传递方式-pass-method)填写说明

#### **响应体**
| 参数                    | 类型            | 说明                               |
|-----------------------|---------------|----------------------------------|
| `dbNet_time`          | `double`      | 获取图像文字框的时间                       |
| `full_detection_time` | `double`      | ocr总耗费时间                         |
| `str_res`             | `string`      | ocr得到的所有文字, 每个文字框中文字由换行符分割组成的字符串 |
| `time`                | `int`         | 处理请求总时间(ocr_time与解码图像的时间)        |
| `text_list`           | `List[dict]`  | ocr得到的文字列表                       |

**note**: 
1. 可以通过`ret_options`来选择返回的信息
2. `text_list`中dict每个字段含义如下表

| 参数                 | 类型                | 说明                     |
|--------------------|-------------------|------------------------|
| `/angle_net/index` | `int`             | 是否旋转180°检测             |
| `/angle_net/score` | `float`           | 旋转检测得分                 |
| `/angle_net/time`  | `double`          | 旋转检测耗时                 |
| `/char_scores`     | `List[float]`     | 每个文字的得分                |
| `/crnn_time`       | `double`          | 识别文字的耗时                |
| `/position`        | `List[List[int]]` | 文字框左上, 右上, 右下, 左下四个点坐标 |
| `/text`            | `string`          | 文字内容                   |

**example**:
```json
{
    "dbNet_time": 6.0052000023424625,
    "full_detection_time": 27.64159999974072,
    "str_res": "I love Aris\n",
    "text_list": [
        {
            "angle_net": {
                "index": 0,
                "score": 1.0,
                "time": 3.0
            },
            "char_scores": [
                0.9848999977111816,
                0.9710265398025513,
                0.9992157220840454,
                0.9999686479568481,
                0.999990701675415,
                0.9999799728393555,
                0.9991695880889893,
                0.9998763799667358,
                0.9999078512191772,
                0.9999631643295288,
                0.9999544620513916
            ],
            "crnn_time": 19.0,
            "position": [
                [
                    0,
                    1
                ],
                [
                    0,
                    29
                ],
                [
                    109,
                    29
                ],
                [
                    109,
                    1
                ]
            ],
            "text": "I love Aris"
        }
    ],
    "time": 28
}
```
### 创建共享内存

#### **请求信息**
| 方法     | URL                     |
|--------|-------------------------|
| `POST` | `/create_shared_memory` |



#### **请求体**
| 参数                    | 类型                   | 必填 | 说明     |
|-----------------------|----------------------|----|--------|
| `/shared_memory_name` | `string`             | 是  | 共享内存名  |
| `/size`               | `unsigned long long` | 是  | 共享内存大小 |


## 可选的语言
| language   | 语言               |
|------------|------------------|
| `zh-cn`    | `ppocr_v4简体中文模型` |
| `zh-cn_v3` | `ppocr_v3简体中文模型` |
| `zh-tw`    | `繁体中文`           |
| `en-us`    | `英文`             |
| `ja-jp`    | `日文`             |
| `ko-kr`    | `韩文`             |
| `ru-ru`    | `俄文`             |


## 图像传递方式(pass_method)

### 本地图像
1. 共享内存传递
2. 提供图像路径, ocr_server读取对应图像 (仅保证支持png格式)
3. 传递图像png编码后的二进制数据

### 远程图像
1. 传递图像png编码后的二进制数据

### pass_method

| 值	 | 传递方式	            | 必填参数                             |
|----|------------------|----------------------------------|
| 0	 | 共享内存             | 	shared_memory_name , resolution |
| 1	 | 传递图像png编码后的二进制数据 | 	image_data                      |
| 2	 | 本地路径             | 	local_path                      |

**note**:
1. 必填参数是指使用该方式传递图像ocr_for_single_line与ocr请求体中的参数
2. `pass_method`为2时, post请求应该传递file参数, 没有json参数
    - 示例
   ![pass_method1_example](/assets/ocr/pass_method1_example.png)
   


