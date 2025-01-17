::: info
本文档收录BAAS每一条配置
1. **type** : 数据类型
2. **element** : 列表 / 字典元素的数据类型
3. **constrains** : 可选值范围(n 选 1)
4. **range** : 数值范围
5. **description** : 配置描述
6. **note** : 需要注意的地方
7. **example** : 填写示例
8. **related docs** : 相关文档
9. **related issue** : 相关issue(这项配置由于这个issue才被添加)
:::
# Emulator Related (模拟器相关)

## `screenshot_interval`
- **type** : double
- **range** : [0.3, INF]
- **description** : 截图间隔
- **note** : 这里的 **间隔** 是指从获取上一张截图的函数调用完毕到下一次获取函数截图开始的时间间隔

## `adbIP`
- **type** : str
- **description** : 模拟器的ip地址
- **note** : 参见 [`adbPort`的note](#adbport)

## `adbPort`
- **type** : Union[int, str]
- **description** : 模拟器端口号
- **note** : 当你的模拟器序列号并非为`<IP>:<Port>`格式时, 将`adbIP` 或 `adbPort` 设置为空, 另一个设置为需要连接的模拟器的完整的序列号即可,
- **example** : 首先请阅读[adb设备连接管理
  ](https://github.com/mzlogin/awesome-adb?tab=readme-ov-file#%E8%AE%BE%E5%A4%87%E8%BF%9E%E6%8E%A5%E7%AE%A1%E7%90%86):

<div style="margin-left: 20px;">

**连接 `10.129.164.6:5555`:**
- `adbIP`: `10.129.164.6`
- `adbPort`: `5555`

<br>

**连接 `emulator-5554`:**

1. **方案一**:
  - `adbIP`: `''`
  - `adbPort`: `emulator-5554`
  - 
2. **方案二**:
  - `adbIP`: `emulator-5554`
  - `adbPort`: `''`

</div>


## `screenshot_method`
- **type** : str 
- **description** : 模拟器截图方式
- **related docs** : [从模拟器获取截图](/develop_doc/script/screenshot.md)
## `control_method`
- **type** : str 
- **description** : 模拟器控制方式
- **related docs** : [模拟器控制方案](/develop_doc/script/control.md)
## `server`
- **type** : str
- **constrains** : "官服" / "B服" / "日服" / "国际服" / "国际服青少年" / "韩国ONE"
- **description** : 服务器名称
- **note** : 
  1. 用于`Baas_thread`类中的`self.server`, `self.package`以及`ConfigSet`类中的`self.server_mode`变量值
  2. 不同服务器的配置不同, 切换服务器时需要**重启UI**以更新配置
## `then`
- **type** : str
- **constrains** :
`"退出 Baas"` / `"退出 模拟器"` / `"退出 Baas 和 模拟器"` / `"关机"` / `"无动作"`
- **description** : BAAS运行完毕后的动作
- **note** : 运行完毕的标志为 **下一次执行任务的等待时间>=120s**
## `program_address`
- **type** : str
- **description** : 模拟器的安装路径
- **note** : 
1. 特定模拟器截图/控制需要加载其安装路径下的动态库
2. 启动模拟器时确定可执行文件位置
## `open_emulator_stat`
- **type** : bool
- **description** : 启动调度器后是否先启动模拟器
## `emulator_wait_time`
- **type** : int
- **range** : [0, INF] 
- **description** : 开启模拟器的等待时间,在这一固定时间后BAAS认为模拟器已经打开完全,可以执行具体任务
- **note** : 未来希望去除这一配置,模拟器的启动与否不是单纯靠等待一个固定时间决定的,需要有方法去检测模拟器是否启动完全
## `emulatorIsMultiInstance`
- **type** : bool
- **description** : 模拟器是否为多开
## `emulatorMultiInstanceNumber`
- **type** : int
- **range** : [0, INF]
- **description** : 模拟器多开号
## `multiEmulatorName`
- **type** : str
- **description** : 使用的模拟器的名称
- **constrains** : 
1. `"mumu"`: 'MuMu模拟器',
2. `"mumu_global"`: 'MuMu模拟器全球版',
3. `"bluestacks_nxt_cn"`: '蓝叠模拟器',
4. `"bluestacks_nxt"`: '蓝叠国际版'
---
<div style="margin-top: 100px;"></div>

# Arena (竞技场)
## `purchase_arena_ticket_times`
- **type** : int
- **range** : [0, INF]
- **description** : 每日购买竞技场门票次数
- **note** : 每日竞技场战斗次数 = 5 + 5 * 购买次数
## `ArenaLevelDiff`
- **type** : int
- **range** : [-INF, INF]
- **description** : 竞技场选择对手时能接受的最大等级差距, 正数表示可以接受对手等级高于自己的对手, 负数表示可以接受对手等级低于自己的对手
## `ArenaComponentNumber`
- **type** : int
- **range** : [1, 3]
- **description** : 竞技场对手编号
## `maxArenaRefreshTimes`
- **type** : int
- **range** : [0, INF]
- **description** : 当遇到等级差距过大的对手时, 最多刷新次数
---
<div style="margin-top: 100px;"></div>

# Cafe (咖啡厅)

## `cafe_reward_invite1_criterion`
- **type**: str
- **Constraints**:
  - `"lowest_affection"`: 邀请最低好感度学生
  - `"highest_affection"`: 邀请最高好感度学生
  - `"starred"`: 邀请收藏的[指定编号](#cafe-reward-invite1-starred-student-position)的学生  // fail to jump
  - `"name"`: 邀请[指定名字](#favorstudent1)的学生
- **Description**: 1号咖啡厅的邀请方式
## `cafe_reward_invite1_starred_student_position`
- **type**: int
- **range**: [1, 5]
## `favorStudent1`
- **type**: List[str]
- **Description**: 1号咖啡厅的邀请学生名字
- **note**: 索引小到大逐次尝试, 邀请时[`ocr`]()获取的姓名与配置名完全匹配才会邀请
## `cafe_reward_invite2_criterion`
- **type**: str
- **Constraints**:
  - `"lowest_affection"`: 邀请最低好感度学生
  - `"highest_affection"`: 邀请最高好感度学生
  - `"starred"`: 邀请收藏的[指定编号](#cafe-reward-invite2-starred-student-position)的学生  // fail to jump
  - `"name"`: 邀请[指定名字](#favorstudent2)的学生
- **Description**: 2号咖啡厅的邀请方式
## `cafe_reward_invite2_starred_student_position`
- **type**: int
- **range**: [1, 5]
## `favorStudent2`
- **type**: List[str]
- **Description**: 2号咖啡厅的邀请学生名字
- **note**: 索引小到大逐次尝试, 邀请时[`ocr`]()获取的姓名与配置名完全匹配才会邀请

<div style="margin-top: 100px;"></div>

# Create (制造)

## `createTime`
- **type** : int
- **range** : [0, INF]
- **description** : 每日制造次数上限
## `alreadyCreateTime`
- **type** : int
- **range** : [0, INF]
- **description** : 当日已经制造次数
- **note** : 每日4:00重置
## `create_phase`
- **type** : int
- **range** : [1, 3]
- **description** : 制造级数
## `createPriority_phase1`
- **type**: List[str]
- **Description**: 制造一阶段选择节点的优先级
## `create_phase_1_select_item_rule`
- **type**: str
- **Description**: 制造一阶段选择材料的方式
- - **constrains**
1.  `"default"`: 使用10个制造石碎片或1个制造石
## `createPriority_phase2`
- **type**: List[str]
- **Description**: 制造二阶段选择节点的优先级
## `create_phase_2_select_item_rule`
- **type**: str
- **Description**: 制造二阶段选择材料的方式
- - **constrains**
1.  `"default"`: 使用数量最多的白色材料
## `createPriority_phase3`
- **type**: List[str]
- **Description**: 制造三阶段选择节点的优先级
## `create_phase_3_select_item_rule`
- **type**: str
- **constrains** 
1.  `"default"`: 使用数量最多的金色材料
- **Description**: 制造三阶段选择材料的方式
## `create_item_holding_quantity`
- **type**: dict[str, int]
- **Description**: 每一种制造材料的剩余数量
- **note**: BAAS在选择制造材料时会确定每个位置的材料名称和数量, 当材料以数量排序时, 用于确定图像匹配的顺序
## `use_acceleration_ticket`
- **type**: bool
- **Description**: 自动制造是否使用加速券
---
<div style="margin-top: 100px;"></div>

# Lesson (日程)

## `purchase_lesson_ticket_times`
- **type** : int
- **range** : [0, 4]
- **description** : 购买日程券的次数
## `lesson_each_region_object_priority`
- **type** : List
- **element** : List
  - **element** : str
  - **description** : 每个区域选择日程的等级
  - **example** : 
  ```json
        [
            "primary",
            "normal",
            "superior"
        ]
  ```
  **表示这个区域会优先做编号为7-8的日程(superior) --> 3-4(normal) --> 1-2(primary)**
- **note** : 当在两个日程间做选择时,会优先选择获得好感经验多的日程
## `lesson_relationship_first`
- **type** : bool
- **description** : 选择日程时是否优先选择可获得好感度多的
## `lesson_times`
- **type** : List
- **element** : int
  - **range** : [0, INF]
- **length** : 不同服务器长度不同
- **description** : 每个区域日程次数
---
<div style="margin-top: 100px;"></div>

# Common Task

## `mainlinePriority`
- **type** : str
- **description** : 普通任务的扫荡关卡
- **note**
## `unfinished_normal_tasks`
- **type** : str
- **description** : 普通任务的扫荡关卡
- **note** : 
## `explore_normal_task_regions`
---
<div style="margin-top: 100px;"></div>

# Hard Task

## `hardPriority`

## `unfinished_hard_tasks`

## `explore_hard_task_need_sss` & `explore_hard_task_need_present` & `explore_hard_task_need_task`

- **type** : bool
- **note** : 当使用困难推图时,共有三个任务要完成:
1. 打到sss
2. 拿取走格子过程中的礼物
3. 完成挑战任务(通常是以一个较少的回合通关)

由于完成不同的任务可能需要的走格子路线不同,所以为了避免体力浪费,BAAS检测已经完成了哪些任务,自动舍去不必要的走格子,当用户指定一个关卡并未指定需要完成以上三个任务的哪几个时, BAAS会根据以上变量的值确定要打什么关卡

## `explore_hard_task_List`

# Drill (战术综合测试)

## `drill_difficulty_List`
- **type** : List
- **element** : int
  - **range** : [1, 4]
- **description** : 战术综合测试三次挑战的难度
## `drill_fight_formation_List`
- **type** : List
- **element** : int
  - **range** : [1, 4]
- **description** : 战术综合测试三次挑战的队伍编号
- **note** : 队伍编号不能重复
## `drill_enable_sweep`
- **type** : bool
- **description** : 是否扫荡综合战术测试
---
<div style="margin-top: 100px;"></div>

# Common Shop

## `CommonShopList`
- **type** : List
- **range** : [0, 3]
- **description** : 日常商店的刷新次数
## `CommonShopRefreshTime`
- **type** : int
- **range** : [0, 3]
- **description** : 日常商店的刷新次数
---
<div style="margin-top: 100px;"></div>

# Tactical Challenge Shop

## `TacticalChallengeShopList`

- **type** : int
- **range** : [0, 3]
- **description** : 竞技场商店的刷新次数

## `TacticalChallengeShopRefreshTime`
---
<div style="margin-top: 100px;"></div>

# bounty (悬赏委托)

## `rewarded_task_times`
- **type** : List[Union[int, str]]
- **element** : [0, INF] or 'max'
- **length** : 3
- **description** : 每个区域使用学园交流会券的次数
## `purchase_rewarded_task_ticket_times`
- **type** : int
- **range** : [0, 12]
- **description** : 购买悬赏委托券的次数
---
<div style="margin-top: 100px;"></div>

# Commissions (特殊委托)

## `special_task_times`
- **type** : List[Union[int, str]]
- **element** : [0, INF] or 'max'
- **length** : 2
- **description** : 扫荡经验本(据点防御)和钱本(信用回收)的次数
---
<div style="margin-top: 100px;"></div>

# Scrimmage (学园交流会)
## `scrimmage_times`
- **type** : List[Union[int, str]]
- **element** : [0, INF] or 'max'
- **length** : 3
- **description** : 每个区域使用学园交流会券的次数
## `purchase_scrimmage_ticket_times`
- **type** : int
- **range** : [0, 12]
- **description** : 购买学院交流会券的次数
---
<div style="margin-top: 100px;"></div>

# Activity 

## `activity_sweep_task_number`

## `activity_sweep_times`

## `activity_exchange_reward'

## `activity_exchange_50_times_at_once`
---
<div style="margin-top: 100px;"></div>

# Clear Friend (自动清好友)

## `clear_friend_white_List`
---
<div style="margin-top: 100px;"></div>

# Other 

## `auto_start`
- **type** : bool
- **description** : 在启动BAAS ui启动完全后自动运行这一项配置

## `burst1` `burst2` `pierce1` `pierce2` `mystic1` `mystic2` `shock1` `shock2`

## `manual_boss`

## `push_after_error`

## `push_after_completion`

## `push_json`

## `push_serverchan`

## `last_refresh_config_time`

## `new_event_enable_state`
- **type** : str
- **description** : 当BAAS更新新的功能时,如果它加入调度器,那么它的开关状态
- **related issue** : [#166](https://github.com/pur1fying/blue_archive_auto_script/issues/166)
## `bannerVisibility`
- **type** : bool
- **description** : 是否显示ui首页banner(关闭后日志界面更大)
## `name`
- **type** : str
- **description** : ui界面顶层显示的该配置的配置名

# 在不同服务器有区别的配置
