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
1. 确定活动名`core/config/default_config.py`中, `"current_game_activity"`字段
2. 活动配置的`json`文件存放在`src/explore_task_data/activities`下, **文件名必须与活动名相同**

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

