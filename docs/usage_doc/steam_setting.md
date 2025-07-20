## Steam用户配置

### **BAAS**设置
1. 在模拟器设置中, 选择服务器为 `Steam国际服`
    ![steam_server_setting.png](/assets/steam/BAAS_setting_game_server_steam_global.png)
2. 在脚本设置中, 选择截图方式为 `mss` 或 `pyautogui`
    ![steam_screenshot_setting.png](/assets/steam/BAAS_setting_screenshot_method_mss_or_pyautogui.png)
3. 在脚本设置中, 选择控制方式为 `pyautogui`
    ![steam_control_setting.png](/assets/steam/BAAS_setting_control_method_pyautogui.png)

### 游戏内设置
- **分辨率**: 
    1. 推荐使用`窗口模式`, 屏幕比例**必须**选择`16:9`, 也就是启用以下选项
        ![screen_windowed_ratio_16_9.png](/assets/steam/setting_screen_windowed_ratio_16_9.png)
        - 调整为`窗口模式后`, 默认分辨率为1280x720, 也就是**最佳分辨率**, 但是如果通过拉动窗口边框来调整窗口大小, 可能会导致窗口分辨率不是标准的`16:9`, 但是接近`16:9`, 此时**BAAS**不会报错, 但是有**极大的可能**导致无法识别游戏画面
            ![screen_windowed_ratio_16_9.png](/assets/steam/BAAS_log_screen_ratio_not_16_9.png)
    2. 如果你的显示器比例为 `16:9`, 也可以选择`全屏模式`
- 记忆大厅：请勿选取亚子，爱露, 若藻等角色, 推荐**关闭记忆大厅**
- 语言：支持**英文/繁体中文/韩文**
- 游戏内设置

| 名称       | 选项      |
|----------|---------|
| 帧率       | 60      |
| 加速渲染模式   | 兼容      |
| 后期处理     | ON      |
| 抗锯齿      | ON      |
| 战斗画面上下黑边 | **OFF** |

### 游戏窗口
- 游戏窗口不能被移动到屏幕外
- **BAAS**运行时, 会强制窗口置顶, 否则无法进行截图

### 其他
- **BAAS**运行时, 会占用你的鼠标进行点击, 滑动操作
