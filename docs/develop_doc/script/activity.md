# 活动 (Activity)

## 简介 (Introduction)

**BAAS**的活动模块代码基于以下事实
1. 各服务器进度不同, 活动不同
2. 活动会复刻, 复刻活动和原始活动内容基本完全相同
3. 每期活动玩家需要推故事(Story), 任务(Mission), 挑战(Task), 扫荡关卡获取每期活动专属货币兑换奖励
4. 不同活动的UI布局不同, 导致点击位置不同
5. 活动可能会附带以下几个玩法, 相同玩法的UI布局和逻辑基本相同
    - 翻牌 
    - 抽奖
    - 新年活动抽签
    - 运动会活动摇骰子
6. 推故事(Story), 任务(Mission), 挑战(Task)时都可能有走格子
7. 挑战关卡非走格子关卡auto无法完成, 需要手操

根据以上规律, 我们可以发现活动有很大相似性, 根据以下活动配置我们可以驱动**BAAS**完成活动

## 活动配置

你可以根据以下步骤完善活动配置
1. 确定活动名
    - 修改`core/config/default_config.py`中, `"current_game_activity"`字段为当期活动名
      - 推荐使用的活动名: 
        1. 直接使用日期`"JP_2025_04_17"`
        2. 活动英文名`"AbydosResortRestorationCommittee"`, 你可以在[BlueArchive Wiki](https://bluearchive.fandom.com/wiki/Event/Event_List)上查询活动英文名
2. 活动配置以`json`文件存放在`src/explore_task_data/activities`下, **文件名必须与活动名相同**
3. 截取进入活动关卡需要的图像
   - 步骤:
        1. 假设你的活动名为
           ```python
           activity_name = "AbydosResortRestorationCommittee"           
           ```
        2. 创建以下文件夹
           ```python
           f"src/images/{server}/activity/{activity_name}"
           ```
        3. 创建以下文件
           ```python
           f"src/images/{server}/x_y_range/activity/{activity_name}.py"
           ```
           - 内容为
               ```python
               prefix = "activity"  
               path = "activity/AbydosResortRestorationCommittee" 
               x_y_range = {
                   'enter1': (1180, 180, 1202, 200),
                   'enter2': (96, 140, 116, 150),
                   'enter3': (176, 519, 265, 564)
               }
               ```
        4. 截取enter1 / 2 / 3 图像并放入 2. 创建的文件夹中, 分别对应以下区域模板
            - enter1
               ![enter1.png](../../assets/activity/enter1.png)
            - enter2
               ![enter2.png](../../assets/activity/enter2.png)
            - enter3
               ![enter3.png](../../assets/activity/enter3.png)

**note**: 
1. 国际服需要同时更新英文, 繁体中文, 韩文的图像
2. 活动结束后将`core/config/default_config.py`中, `"current_game_activity"`字段设置为`null`

## 配置文件字段含义
### `"total_story"`
- **type**: `int`
- **description**: 活动故事总数
- **note**: 如果有走格子, 需要在`"story" + str(i)`添加走格子数据

### `"mission"`
- **type**: `list`
- **description**: 活动任务属性列表
- **note**: 如果有走格子, 需要在`"mission" + str(i)`添加走格子数据

### `"sweep_ap_cost_mission"`
- **type**: `list`
- **description**: 活动扫荡关卡消耗体力列表

### `"grid_tasks_challenge"`
- **type**: `list`
- **description**: 活动挑战走格子需完成任务列表
- **example**:
```json
{
   "grid_tasks_challenge": 
   [
      "challenge2_sss",
      "challenge2_task",
      "challenge4_sss",
      "challenge4_task"
   ]
}
```
表示共需完成四次走格子, 分别为 `挑战2三星`, `挑战2成就任务`, `挑战4三星`, `挑战4成就任务`

同时需要在活动配置中添加这四次走格子的推图数据

### `"has_draw_card"`
- **type**: `bool`
- **description**: 是否有翻牌玩法

### `"has_exchange_reward"`
- **type**: `bool`
- **description**: 是否有抽奖玩法

