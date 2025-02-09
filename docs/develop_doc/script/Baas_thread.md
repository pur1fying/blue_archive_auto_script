# BAAS (class Baas_thread)
对应文件路径 : `"core/Baas_thread.py"`

## 总览
`Baas_thread`集成了所有**BAAS**控制模拟器, 完成指定任务所需要的功能
- 模拟器截图
- 模拟器控制
- 文字识别(OCR)
- 调度器
- 日志记录

**note**: 目前图像比较方法并没有集成在`Baas_thread`中, 而是在`core/image.py` 中

## Members

### `project_dir`
- **description**: 项目根目录路径

### `u2_client`
- **type**: `U2Client` 实例.

### `u2`
- **type**: `uiautomator2` `Device` 实例
- **note**: 
  1. 这并不是**BAAS**实现类, 而是[`uiautomator2`](https://github.com/openatx/uiautomator2)库中`Device`类的实例
  2. 保留它的原因是项目初期主要用`uiautomator2`实现模拟器截图和控制, 
### `dailyGameActivity`
- **description**: 日常小游戏名

### `config_set`
- **type**: `ConfigSet` 实例

### `process_name`

### `emulator_start_stat`

### `lnk_path`

### `file_path`

### `wait_time`

### `serial`
- **description**: 模拟器序列号

### `scheduler`
- **type**: `Scheduler` 实例

### `screenshot_interval`

### `flag_run`

### `current_game_activity`

### `package_name`

### `server`

### `rgb_feature`

### `config_path`

### `config`

### `ratio`

### `next_time`

### `task_finish_to_main_page`

### `static_config`

### `ocr`
- **type**: `Baas_ocr` 实例

### `logger`

### `last_refresh_u2_time`

### `latest_img_array`
- **description**: 最近一次模拟器截图的数组

### `total_assault_difficulty_names`

### `button_signal`

### `update_signal`

### `exit_signal`

### `stage_data`

### `activity_name`

### `control`
- **type**: `Control` 实例

### `screenshot`
- **type**: [`Screenshot`](/develop_doc/script/screenshot) 实例
