# 自动战斗(Auto Fight)

## 简介(Introduction)

本文档设计**BAAS**自动战斗的内容, 我们欢迎你在Issue中提出优化或新特性, 使自动战斗尽可能适用于各种场景

- 这里的自动战斗并非指使用游戏内的auto让角色盲目的释放技能, 而是指**BAAS**通过截取战斗时的图像并提取其中的信息, 根据一个确定流程在`恰当的条件`下释放技能
- 这个流程简称为`轴`
- 使用者可以根据需求与规范书写`json`格式的轴, **BAAS**负责解析轴并执行
- 轴的运作理念类似于编译原理中的**有限状态自动机**
- 下图为一个简单的流程图
    ![procedure_draft](/assets/auto_fight/procedure_draft.png)

### 队伍配置
- 通过规定角色练度确定是否可以使用这个轴 (可选)
- 选择初始技能

### 可监测的数据
以下图为例介绍在自动战斗中图像中可被提取的数据
- ![total_assault_general.png](/assets/auto_fight/total_assault_general.png)
1. BOSS的最大血量 / 总血量 [Code](/develop_doc/script/auto_fight_boss_health_update.md)
![boss_health.png](/assets/auto_fight/boss_health.png)
2. 每个技能槽学生的技能以及技能释费用 [Code](/develop_doc/script/auto_fight_skill_update.md)
![student_skill.png](/assets/auto_fight/student_skill.png)
3. 倍速 / 自动状态
![acc_auto_phase.png](/assets/auto_fight/acc_auto_phase.png)
4. 当前可用于释放技能的Cost
![current_cost.png](/assets/auto_fight/current_cost.png)
5. 战斗剩余时间
![fight_left_time.png](/assets/auto_fight/fight_left_time.png)
6. 房间剩余时间
![room_left_time.png](/assets/auto_fight/room_left_time.png)
7. 学生位置坐标及
![student_position.png](/assets/auto_fight/student_position.png)
8. 敌对角色的位置
![enemy_position.png](/assets/auto_fight/enemy_position.png)

### 数据记录类 
screenshot_data_recorder
使用类来记录[可监测的数据](#可监测的数据)中的数据, 以供[动作(action)](#动作-action) 和 [条件(condition)](#条件-condition)使用

### 数据更新
按照下图的架构实现自动战斗的数据更新
![screenshot_data_update_cycle.png](/assets/auto_fight/screenshot_data_update_cycle.png)

## 状态(State)
每个状态由以下内容组成
1. action: 到达这个状态后执行的行为（如技能释放、开启auto/倍速等
2. transition: action结束后的状态转移列表
3. condition: 状态转移的条件
4. next_state: 下一个状态

**example**: 以上述内容书写一个简介中简单流程图的状态机
```json
{
  "states": {
    "start_state": {
      "next_state": "state_release_skill_1"
    },
    "state_release_skill_1": {
      "action": "release_skill_1",
      "transitions": [
        {
          "condition": "condition_boss_health_over_500w",
          "next_state": "state_release_skill_2"
        },
        {
          "condition": "condition_null",
          "next_state": "state_release_skill_2"
        }
      ]
    },
    "state_release_skill_2": {
      "action": "release_skill_2",
      "transitions": [
        {
          "condition": "condition_boss_health_over_0",
          "next_state": "state_restart"
        },
        {
          "condition": "condition_null",
          "next_state": "state_end"
        }
      ]
    },
    "state_restart": {
      "action": "restart",
      "transitions": [
        {
          "condition": "condition_null",
          "next_state": "start_state"
        }
      ]
    },
    "state_end": {
      "description": "This is end of script."
    }
  },
  "conditions": {
    "condition_null": {
      
    },
    
    "condition_boss_health_over_500w": {
      "condition": "Boss health > 5_000_000"
    },
    
    "condition_boss_health_over_0": {
      "condition": "Boss health > 0"
    }
  },
  "actions": {
    "release_skill_1": {
      "release_method": 1,
      "slot": {
        "number": 1
      },
      "target": {
        "position": [1180, 360],
        "name": "goz"
      },
      "check": {
        "type": 0
      }
    },
    "release_skill_2": {
      "release_method": 1,
      "slot": {
        "number": 1
      },
      "target": {
        "position": [1180, 360],
        "name": "goz"
      },
      "check": {
        "type": 0
      }
    },
    "restart": {
      "description": "Restart The Game"
    }
  }
  
}

```


## 动作(Action)

释放技能有关的参数

### release_method

- **description**: 释放一个技能的方式
- **type**: `int`
- **constrains**:
-
    | 值   | 含义                       |
    |-----|--------------------------|
    | `0` | 开启`auto`释放 (确保`auto`被选中) |
    | `1` | 自定义点击顺序                  |
    | `2` | 保证槽技能被选中-->释放            |

**note**:
方式 `2, 3` 需要设置[`target`](#target) 

### target

#### type
- **description**: 技能释放的目标类型
- **type**: `int`
- **constrains**:
- 
    | 值   | 含义           | 需要字段       |
    |-----|--------------|------------|
    | `0` | 一个固定坐标       | `position` |
    | `1` | 一个运行过程中生成的坐标 | `name`     |
- **examples**:
1. `type` = 0
    ```json
    {
      "target": {
        "type": 0,
        "position": [1180, 360]
      }
    }
    ```
    **explanation**: 释放技能的固定坐标为(1180, 360)
2. `type` = 1
    ```json
    {
      "target": {
        "type": 0,
        "name": "goz"
      }
    }
    ```
    **explanation**: 释放技能位置在运行时生成, 为yolo检测出名为"goz"的坐标
### check

- **description**: 检查技能释放的方式
- **type**: `int`
- **constrains**:
-
    | 值   | 含义       |
    |-----|----------|
    | `0` | 不作检测     |
    | `1` | `cost`减少 |
    | `2` | 技能槽图标消失  |

- **examples**:
```json
{
  "release_skill_Mika": {
      "release_method": 2,
      "slot": "Mika",
      "target": {
        "type": 0,
        "name": "goz"
      },
      "check": {
        "type": 1,
        "decrease": 2.9
      }
    }
}
```

## 重开条件(Restart Condition)

重开是凹分必不可少的环节之一, 列举以下重开条件以供参考

### BOSS血量范围
- **description**: 检查BOSS血量是否在某一范围
- **checkpoint**:
    1. 战斗剩余时间达到某值
    2. 释放技能后x秒
- **usage**:
    1. 技能未暴击
    2. 其他异常 (学生退场 / 寿司开盾减伤 / 黑白转阶段)

### BOSS血量减少
- **description**: 检查BOSS血量是否在某一时间段内下降期望值
- **checkpoint**:
  1. 战斗剩余时间达到某值计时x秒
  2. 释放技能后计时x秒
  
### 技能槽
- **description**:检查学生技能是否出现在技能槽
- **checkpoint**:
  1. 战斗剩余时间达到某值计时x秒
  2. 释放技能后计时x秒
- **usage**:
   1. 检查初始技能顺序是否正确
   2. 学生退场 --> 技能排序变化
   3. `auto`异常释放技能

### 技能Cost
- **description**:检查技能Cost是否为指定值
- **checkpoint**:
  1. 战斗剩余时间达到某值计时x秒
  2. 释放技能后计时x秒
- **usage**:
   1. 检查忧, 枫香(新年) 等减费角色的技能是否释放到期望目标


## 条件(Condition)

### 条件类(Condition Class)

条件类需要有以下特性
1. 主循环截图并更新状态
2. 单一状态信息更新后**紧接着**进行条件判断
    - 从截图提取的状态信息也会用于[`动作action`](#动作-action), 状态信息需要被`共享`
3. 根据[可监测的数据](#可监测的数据)中任意**一个**进行比较的条件称为`原始条件 (primitive condition)`
4. 条件可根据`or / and`进行组合, 称为`组合条件`
5. 采用`多线程`进行状态信息提取
6. 如果`一个状态信息`不被当前`任意一个条件`所需要, 则不更新 
7. 每个条件必须包含一个`截止时间字段`, 时限内未出现期望状态则条件为false

## 使用前须知
### 必要的游戏内设置
1. **必须关闭游戏内释放技能动画**


## 轴的基本信息

### `name` (轴名称)
- **description**: 轴的名称
- **type**: `string`
- **example**: 特殊委托关卡L, 使用女仆爱丽丝的通关轴
```json
{
  "name": "Special-Task-L Aris Maid Workflow"
}
```

### formation (配队信息)

### 完整组合
```json
{
  "name": "Special-Task-L Aris Maid Workflow",
  "formation": {
    "front": ["Aris (Maid)", "Wakamo", "Kayoko (New Year)", "Ui"],
    "back": ["Ako", "Himari"],
    "initial_skills": ["Wakamo", "Ako", "Himari"],
    "all_appeared_skills": [
      "Aris (Maid)",
      "Wakamo",
      "Kayoko (New Year)",
      "Ui",
      "Ako",
      "Himari"
    ],
    "borrow": ""
  },
  "battle": {
    "boss_max_health": {
      "phase1": 188796,
      "phase2": 224756,
      "phase3": 260729,
      "phase4": 287696,
      "phase5": 323657
    }
  }

}


```


