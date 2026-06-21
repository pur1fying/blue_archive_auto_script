# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

BAAS（Blue Archive Auto Script）是一个带 PyQt5 GUI 的自动化工具，用于接管蔚蓝档案在安卓模拟器上的日常任务。面向 16:9 分辨率（1280×720 最佳），支持 CN（国服）/ Global（国际服）/ JP（日服）。自动战斗使用 YOLOv8；性能敏感的部分（目前是 OCR）正逐步用 C++ 重写（`BAAS_Cpp`）。

## 环境配置

- Python **3.9**（推荐 3.9.21）。安装路径**不能含中文**（Qt 框架限制）。
- Windows：`pip install -r requirements.txt`；Linux/macOS：`pip install -r requirements-linux.txt`。
- 注意版本锁很重要 —— `numpy < 2.0`、`opencv-python == 4.8.1.78`、`av == 12.0.0`、`uiautomator2 == 2.16.23`、`PyQt-Fluent-Widgets == 1.2.0`。

## 常用命令

```bash
# 启动 GUI（主入口）
python window.py

# 通过 CLI 示例无界面运行单个任务（先修改文件内的任务列表）
python cli.example.py      # 运行其 __main__ 块中的任务
python service.example.py  # 基于 asyncio 的定时任务运行器

# 跑单个 unittest（这些测试会驱动真实模拟器/设备，详见各文件 setUp）
python -m unittest develop_tools/test/test_explore_normal_task.py
python -m unittest develop_tools/test/test_explore_hard_task.py

# i18n：为 GUI 重新生成翻译 .ts/.qm（需 Qt Linguist，见 docs/i18n.md）
# 打包安装器（Windows）：
deploy/installer/build.bat   # 或 build.sh；通过 PyInstaller 生成 BlueArchiveAutoScript.exe
```

项目未配置 linter/formatter。请遵循周边代码风格；代码库混用中文注释与英文标识符。

## Git 约定

仓库**刻意不在根目录放置 `.gitignore`**（会影响所有贡献者的环境）。请改用自己的 `.git/info/exclude` 来忽略内容。**不要**在根目录添加 `.gitignore`。`config/`、`*.pyc`、生成的图像缓存等应通过这种方式在本地忽略。

## 架构

### 核心循环与任务分发

BAAS 按设计文档运行固定控制循环：**1. 截图 → 2. 推导游戏状态 → 3. 决定操作**。

- `core/Baas_thread.py` —— 中央编排器。每个自动化任务是一个字符串键，通过模块级 `func_dict` 映射到函数（几乎都是 `module/<task>.implement`）。分发发生在 `Baas_thread.solve(activity)`，它把每次调用包在一个 3 次重试循环中，遇到 `FunctionCallTimeout` 和 `PackageIncorrect` 时通过重启游戏来恢复。
- `thread_starter()` 是调度器驱动的入口：调用 `scheduler.heartbeat()` 取下一个 `{pre_task, current_task, post_task}` 三元组，通过 `solve()` 执行，再用 `scheduler.systole()` 记录下次运行时间。`solve('restart')` 总是最先运行，用于校验包名并回到主页。
- 新增任务的方法：写 `module/<name>.py`，导出 `implement(self)` 函数（`self` 是 `Baas_thread`），然后在 `core/Baas_thread.py` 的 `func_dict` 中注册。

### 任务位于 `module/`

每个文件导出 `implement(self) -> bool`，操作 `Baas_thread` 实例。`to_main_page`、`click`、`get_screenshot_array`、`ocr.*`、`image.*`、`picture.*` 等都是 `self` 上的方法。活动（轮换活动）在 `module/activities/` 中各有一个类；当前活动名在 `core/config/default_config.py` 的 `current_game_activity`，其推图数据在 `src/explore_task_data/activities/<name>.json`。

### 配置（`core/config/`）

- `ConfigSet`（config_set.py）持有两个 dataclass：`static_config`（来自 `config/static.json`）和 `config`（来自 `config/<dir>/config.json`）。这些 dataclass 是**生成**的 —— `develop_tools/generate_dataclass_code.py` 读取 `default_config.py`（`USER_DEFAULT_CONFIG`、`STATIC_DEFAULT_CONFIG`）并写出 `generated_user_config.py` / `generated_static_config.py`。新增配置项时，先加到 `default_config.py`，再重新生成。
- `config/` **不在仓库中** —— 由 GUI 在运行时创建。一个"配置"是 `config/` 下包含 `config.json` 和 `event.json` 的目录。`ConfigSet(config_dir="name")` 解析 `config/<name>`（相对路径）或绝对路径。
- 服务器 → 模式映射（`get_server_mode`）：`官服`/`B服` → CN，`国际服`/`韩国ONE`/`Steam国际服` → Global，`日服` → JP。`server` 字段决定使用哪套图像资源与行为分支。

### 调度器（`core/scheduler.py`）

读取 `config/<dir>/event.json` —— 一个事件列表，每项含 `enabled`、`priority`、`interval`、`daily_reset`、`func_name`、`pre_task`/`post_task`、`disabled_time_range`。`heartbeat()` 挑出下一个到期任务；`systole(task, next_time)` 重新调度它。`event.json` 默认值来自 `default_config.py` 的 `EVENT_DEFAULT_CONFIG`。

### 设备交互（`core/device/`）

按 `method` 字符串多态，来自配置：

- `Screenshot` —— `nemu` / `adb` / `uiautomator2` / `scrcpy` / `pyautogui` / `mss`（各子目录一个文件）。nemu（约 5–20ms）和 scrcpy（约 17ms）是快速路径；adb/u2 约 300ms。
- `Control` —— 同一组方法；`nemu` 点击内联执行，其余在线程中执行。
- `Connection` —— 解析 serial/package/activity，区分安卓设备与窗口，服务器检测。
- `emulator_manager` —— 启停模拟器进程，多实例处理。

截图被归一化为横屏并按 `self.ratio = width / 1280` 缩放。所有点击/区域坐标都按 **1280×720 逻辑空间** 编写，点击时乘以 `ratio` —— 不要硬编码真实设备像素。

### 图像 / 状态识别

- `core/position.py` —— 加载由 `src/images/<server>/x_y_range/*.py` 描述的图像模板。每个此类文件声明 `prefix`、`path` 和 `x_y_range = {name: (x1,y1,x2,y2)}`。真实图像路径为 `src/images/<server>/<path>/<name>.png`。加载后的模板存于 `position.image_dic[server][f"{prefix}_{name}"]`，区域存于 `image_x_y_range`。**`name` 不能含 `_`**（用 `rsplit` 分割），请改用 `-`。`init_image_data(self)` 加载某一服务器的全部图像，外加当前活动的图像。
- `core/image.py` —— 模板匹配（`compare_image`、`search_in_area`、`search_image_in_area`、`get_image_all_appear_position`、`swipe_search_target_str`）。图像特征参数按 `docs/develop_doc/develop_format.md` 接受三种形式：纯字符串 `"main_page"`（默认阈值 0.8）、元组 `("main_page", 0.9)`、或二者组合的列表。
- `core/color.py` —— RGB 像素比较（`match_rgb_feature`），用于固定颜色的界面线索。
- `core/picture.py` —— 高层状态机 `co_detect(...)`：循环截图，检查 `rgb_ends`/`img_ends` 是否为终止状态，按 `rgb_reactions`/`img_reactions` 点击，处理弹窗、试探性点击，超时 → `FunctionCallTimeout`，包名错误 → `PackageIncorrect`。这是大多数 `module/*.implement` 函数所依赖的主力。
- `core/ocr/` —— `Baas_ocr` 与独立的 OCR 服务端通信（`baas_ocr_client/`）。`server_installer.check_git` 在启动时拉取/更新 OCR 服务端仓库；`client.start_server()` 启动它。OCR 语言按服务器请求（日服还需 `"Global"`，否则会崩溃）。远程 vs 本地服务端决定 `ocr_img_pass_method`（共享内存 vs 文件）。

### GUI（`window.py` + `gui/`）

`window.py` 是 PyQt5 + qfluentwidgets 的 `MSFluentWindow` 应用。`gui/fragments/` 是各标签页（home、process、settings、switch、history、readme）。配置通过 GUI 创建/管理，由 GUI 填充 `config/<dir>/`。翻译位于 `gui/i18n/*.ts/.qm`（en_US、ja_JP、ko_KR）；按 `docs/i18n.md` 通过 `gui/util/language.py` 的 `Language` 枚举新增语言。

## 关键注意事项

- 坐标为 1280×720 逻辑空间，由 `ratio` 缩放。竖屏安卓截图会被自动旋转为横屏。
- 不要在根目录添加 `.gitignore`，请用 `.git/info/exclude`。
- 修改配置 schema 后，通过 `develop_tools/generate_dataclass_code.py` 重新生成 dataclass，并更新 `default_config.py`。
- 日服配置要求 `ocr_needed` 包含 `"Global"`，否则会崩溃。
- 图像 `name` 不能含 `_`；`prefix` 可以。
- `develop_tools/test/` 中的 unittest 会启动真实的 `Main`/`Baas_thread` 并连接设备 —— 它们是集成测试，不是隔离单元测试。
