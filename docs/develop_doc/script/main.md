以下是根据您提供的代码生成的完整 Markdown 文档，包含类的每个函数、成员的参数和返回值说明。如果部分信息无法直接从代码中提取（例如参数含义或返回值），会标注为 "无具体说明"：

---

# Documentation for `main.py`

## Class: `Main`

`Main` 类处理项目的核心逻辑，包括初始化 OCR 模块、读取静态配置、管理线程等。

---

### `__init__`

初始化 `Main` 类。

#### 参数
- `logger_signal` (*optional*): 用于日志记录的信号。
- `ocr_needed` (*list*, *optional*): 指定需要的 OCR 模块。

#### 返回值
无。

---

### `init_all_data`

初始化所有数据，包括 OCR 模块和静态配置。

#### 参数
无。

#### 返回值
无。

---

### `init_ocr`

初始化 OCR 模块。

#### 参数
无。

#### 返回值
- (*bool*): 初始化成功返回 `True`，否则返回 `False`。

---

### `get_thread`

创建并返回一个新的线程对象。

#### 参数
- `config`: 配置对象。
- `name` (*str*, *optional*): 线程名称，默认值为 `'1'`。
- `logger_signal` (*optional*): 日志信号。
- `button_signal` (*optional*): 按钮信号。
- `update_signal` (*optional*): 更新信号。
- `exit_signal` (*optional*): 退出信号。

#### 返回值
- (*Baas_thread*): 创建的线程对象。

---

### `stop_script`

停止指定名称的脚本线程。

#### 参数
- `name` (*str*): 要停止的线程名称。

#### 返回值
- (*bool*): 成功停止返回 `True`，否则返回 `False`。

---

### `init_static_config`

加载静态配置文件 `static.json`。

#### 参数
无。

#### 返回值
- (*bool*): 成功加载返回 `True`，否则返回 `False`。

---

### `operate_dict`

递归处理字典中的数据类型，确保所有值的类型为 Python 内置类型。

#### 参数
- `dic` (*dict*): 输入的字典。

#### 返回值
- (*dict*): 处理后的字典。

---

### `is_float`

检查输入字符串是否为浮点数。

#### 参数
- `s` (*str*): 要检查的字符串。

#### 返回值
- (*bool*): 如果是浮点数返回 `True`，否则返回 `False`。

---

### `operate_item`

对字典或列表中的元素进行类型处理。

#### 参数
- `item` (*any*): 输入元素，可以是任意类型。

#### 返回值
- (*any*): 处理后的元素，类型根据输入自动调整。

---

## 模块使用示例

以下是主函数的执行逻辑：
1. 初始化 `Main` 对象，并加载 OCR 模块及静态配置。
2. 通过 `Baas_thread` 对象运行多种任务，如：
    - `explore_normal_task`
    - `main_story`
    - 更多任务（已注释）。

---

## 外部依赖

### 引用的模块
- `json`
- `os`
- `core.utils`（定义了 `Logger` 类）
- `core.ocr`（定义了 `ocr` 模块）
- `gui.util.config_set`（定义了 `ConfigSet` 类）
- `core.Baas_thread`（定义了 `Baas_thread` 类）
- `module.create`（定义了多个任务处理方法）

---

此文档格式化为 Markdown，可直接用于 **VitePress** 或 **MkDocs** 等静态站点生成工具。