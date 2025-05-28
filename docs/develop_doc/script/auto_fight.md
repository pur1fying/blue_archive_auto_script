# 自动战斗(Auto Fight)

## 简介(Introduction)

本文档记录了**BAAS**自动战斗的框架以及原理, 并通过一个例子教学如何按照**BAAS**的自动战斗框架的规范书写自动战斗的轴文件

::: info 
**如果你是C++小白,不用理解代码是如何书写的,重点关注轴文件的格式, 跟着本文的指导一步一步理解也可以写出正确的轴文件**
:::
::: warning
轴文件为json格式, 请先学习json的书写规范, 否则你可能会因为json格式错误导致轴文件无法被解析
:::

- 首先明确一点, 这里的自动战斗并非指使用游戏内的auto让角色盲目的释放技能, 而是指**BAAS**通过截取战斗时的图像并提取其中的信息, 根据一个用户指定的`流程`在`恰当的条件`下`释放技能`
- 这个流程简称为`轴`, `轴`是一个`json`格式的文件, 里面包含了自动战斗的所有信息
- 使用者可以根据需求与**自动战斗规范**书写`轴`文件, **BAAS**负责解析`轴`是否合法并运行合法的轴
- **BAAS**的自动战斗运作理念类似于编译原理中的**有限状态自动机**

## 例子(Example)
以下图的简单流程作为自动战斗轴文件的书写例子, 当你理解了这个例子, 你就能完全理解**BAAS**自动战斗的工作原理, 以及轴文件该如何书写
    ![procedure_draft](/assets/auto_fight/procedure_draft.png)

观察这个流程图, 我们可以发现:
- 流程中存在以下条件`condition` (每一个箭头上的文字)
    1. 血量 > 500w
    2. 血量 < 500w
    3. 血量 > 0
    4. 血量 < 0
- 流程中存在以下动作`action`
    1. 释放技能1 `release_skill_1`
    2. 释放技能2 `release_skill_2`
    3. 重开 `restart`

- 我们可以将流程拆分为以下状态`state`
    1. 自动战斗开始 `start`
        - 下一个状态 : 释放技能1
    2. 释放技能1 `release_skill_1`
        - 动作 : 释放技能1
        - 状态转移 : 
            1. 条件 : 血量 > 500w  | 下一个状态 : 重开
            2. 条件 : 血量 < 500w | 下一个状态 : 释放技能2
    3. 释放技能2 `release_skill_2`
        - 动作 : 释放技能2
        - 状态转移 : 
            1. 条件 : 血量 > 0 | 下一个状态 : 重开
            2. 条件 : 血量 < 0 | 下一个状态 : 结束
    4. 重开 `restart`
       - 动作 : 重开
       - 下一个状态 : 释放技能1
    5. 结束 `end`

:::info
你或许会疑惑`state`中的释放技能1 / 释放技能2 / 重开 是不是与上面的`action`重复了, 这实际上是完全不同的概念, 状态名`state`是可以和动作名`action`相同的, 请注意区分同名的状态和动作
:::

- 根据以上例子, 你可能发现了, **BAAS**自动战斗轴文件本质上需要你完成三个内容:
    - `状态(state)` : 自动战斗在到达状态时执行动作, 并按照转移条件转移到下一个状态
        - [状态书写规范](#状态-state)
    - `条件(condition)` : 状态转移的条件
        - [条件书写规范](#条件-condition)
    - `动作(action)` : 到达一个状态后立即执行的动作
        - [动作书写规范](#动作-action)

- 接下来我们逐步讲解自动战斗轴该如何书写

## 截图数据监测
- 相关代码见 `apps/BAAS/src/module/auto_fight/screenshot_data` 文件夹

### 可监测的数据
以下图为例介绍在自动战斗中图像中可被提取的数据
- ![total_assault_general.png](/assets/auto_fight/total_assault_general.png)
1. BOSS的最大血量 / 总血量 [Code](/develop_doc/script/auto_fight_boss_health_update.md)
![boss_health.png](/assets/auto_fight/boss_health.png)
2. 每个技能槽学生的技能名以及技能释费用 [Code](/develop_doc/script/auto_fight_skill_update.md)
![student_skill.png](/assets/auto_fight/student_skill.png)
3. (倍速 [Code](/develop_doc/script/auto_fight_acc_phase_update.md))  / (自动 [Code](/develop_doc/script/auto_fight_auto_state_update.md)) 状态
![acc_auto_phase.png](/assets/auto_fight/acc_auto_phase.png)
4. 当前可用于释放技能的费用 [Code](/develop_doc/script/auto_fight_cost_update.md)
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

- 每个数据更新都对应一个类, 他们都继承自[`class BaseDataUpdater`](/develop_doc/script/auto_fight_BaseDataUpdater.md)
 类`screenshot_data` 中 `d_updater_mask` 用于指示一轮数据更新中哪些`update()` 函数需要被调用, 每一位对应一个数据更新类, 对应关系如下

    | Bit | Updater                    |
    |-----|----------------------------|
    | `1` | `CostUpdater`              |
    | `2` | `BossHealthUpdater`        |
    | `3` | `SkillNameUpdater`         |
    | `4` | `SkillCostUpdater`         |
    | `5` | `AccelerationPhaseUpdater` |
    | `6` | `AutoStateUpdater`         |

  **example**: 当`d_updater_mask` 被设置为 `0b1101` 则表示 `CostUpdater` , `SkillNameUpdater` 和 `SkillCostUpdater` 的 `update()` 函数需要被调用 

- 数据更新多线程并行进行, 线程数量由配置中的`/auto_fight/d_update_max_thread`字段决定
- 数据更新任务提交至线程池的顺序由每个`updater`重写的[`estimated_time_cost`](/develop_doc/script/auto_fight_BaseDataUpdater#estimated-time-cost)决定, 按照更新耗时由小到大进行更新

## 基准测试(Benchmark)

在不同的设备下测试了**BAAS**自动战斗各模块的性能, 数据仅供参考

### 模拟器截图/控制速度测试
截图/控制速度主要与模拟器 和 CPU 有关, 推荐使用`雷电`模拟器 / `MuMu`模拟器

| CPU / 模拟器               | `雷电`                      | `MuMu`                       |
|-------------------------|---------------------------|------------------------------|
| `Amd Ryzen 9 9950x`     | `0.8ms - 2.5ms` 平均`1.5ms` | `1.9ms - 3.4ms` 平均`2.5ms`    |
| `Amd Ryzen 6 6800H`     | -                         | `4.9ms - 8.2ms` 平均`7.1ms`    |
| `Intel Core i5-9300H`   | -                         | `12.1ms - 21.3ms` 平均`15.3ms` |
| `Intel Core i9-13900HX` | `1.7ms - 6.8ms` 平均`3.5ms` | `4.2ms - 8.7ms` 平均`5.9ms`    |

 - 以上截图方式分别为
    - 雷电 : ldopengl 
    - MuMu : nemu

| CPU + 控制模式 / 模拟器                 | `MuMu`                         |
|----------------------------------|--------------------------------|
| `Amd Ryzen 9 9950x`+`adb`        | `4.9ms` - `7.1ms` 平均`6.1ms`    |
| `Amd Ryzen 9 9950x`+`nemu`       | `40us` - `90us` 平均`50us`       |
| `Amd Ryzen 9 9950x`+`scrcpy`     | `5.2ms` - `5.9ms` 平均`5.5ms`    |
| `Amd Ryzen 6 6800H`+`adb`        | `12.5ms` - `14.7ms` 平均`13.3ms` |
| `Amd Ryzen 6 6800H`+`nemu`       | `43us` - `87us` 平均`59us`       |
| `Amd Ryzen 6 6800H`+`scrcpy`     | `5.6ms` - `5.7ms` 平均`5.6ms`    |
| `Intel Core i9-13900HX`+`adb`    | `11.9ms` - `16.3ms` 平均`13ms`   |
| `Intel Core i9-13900HX`+`nemu`   | `50us` - `110us` 平均`70us`      |
| `Intel Core i9-13900HX`+`scrcpy` | `5.3ms` - `6.4ms` 平均`5.6ms`    |


### 数据更新速度测试

1. `纯CPU`更新数据

    | CPU / 数据                | `Cost`                    | `SkillName`                      | `ObjPos`                            |
    |-------------------------|---------------------------|----------------------------------|-------------------------------------|
    | `Amd Ryzen 9 9950x`     | `3us - 9us`<br/>平均`6us`   | `1.8ms - 2.1ms`<br/>平均`2ms`      | `33.1ms - 39.5ms`<br/>平均`35ms`      |
    | `Amd Ryzen 6 6800H`     | `6us - 28us`<br/>平均`15us` | `3.1ms - 4.5ms`<br/>平均`3.5ms`    | `79.1ms - 91.0ms`<br/>平均`86ms`      |
    | `Intel Core i5-9300H`   | `6us - 53us`<br/>平均`20us` | `10.4ms - 14.9ms`<br/>平均`12.5ms` | `159.3ms - 222.5ms`<br/>平均`175.5ms` |
    | `Intel Core i9-13900HX` | `3us - 19us`<br/>平均`7us`  | `1.9ms - 5.4ms`<br/>平均`3.6ms`    | `70.1ms - 107.0ms`<br/>平均`90ms`     |

    | CPU / 数据                | `BossHealth`                   | `SkillCost`                      | `Acc`                      |
    |-------------------------|--------------------------------|----------------------------------|----------------------------|
    | `Amd Ryzen 9 9950x`     | `5.0ms - 9.0ms`<br/>平均`7.8ms`  | `1.6ms - 3ms`<br/>平均`1.8ms`      | `6us - 24us`<br/>平均`13us`  |
    | `Amd Ryzen 6 6800H`     | `35.0ms - 50.0ms`<br/>平均`39ms` | `6.4ms - 8.4ms`<br/>平均`7.5ms`    | `14us - 21us`<br/>平均`20us` |
    | `Intel Core i5-9300H`   | `52.0ms - 79.3ms`<br/>平均`65ms` | `16.0ms - 22.7ms`<br/>平均`20.2ms` | `25us - 36us`<br/>平均`30us` |
    | `Intel Core i9-13900HX` | `31.4ms - 90.1ms`<br/>平均`60ms` | `5.1ms - 18.9ms`<br/>平均`8.5ms`   | `13us - 23us`<br/>平均`16us` |

    - **note**: `SkillCost`指更新一个槽技能的时间, 三个槽时间需要 x 3

    | CPU / 数据                | `Auto`                      | 
    |-------------------------|-----------------------------|
    | `Amd Ryzen 9 9950x`     | `9us - 24us`<br/>平均`16us`   | 
    | `Amd Ryzen 6 6800H`     | `16us - 22us`<br/> 平均`20us` |
    | `Intel Core i5-9300H`   | `27us - 43us`<br/>平均`30us`  | 
    | `Intel Core i9-13900HX` | `13us - 23us`<br/>平均`19us`  |

2. YOLO模型推理 : `CUDA加速`和`纯CPU`速度对比

| 设备 / 数据                 | `ObjPos`                            | 
|-------------------------|-------------------------------------|
| `RTX 5090`              | `9.1ms - 11.0ms` <br/>平均`10.1ms`    |
| `Amd Ryzen 9 9950x`     | `33.1ms - 39.5ms` <br/>平均`35ms`     | 
| `Amd Ryzen 6 6800H`     | `79.1ms - 91.0ms` <br/>平均`86ms`     |
| `Intel Core i5-9300H`   | `159.3ms - 222.5ms`<br/>平均`175.5ms` | 
| `Intel Core i9-13900HX` | `70.1ms - 107.0ms`<br/>平均`90ms`     |

## 基本配置

下图为一个轴文件的基本配置, 规定了一下自动战斗的基本信息
1. Boss血量的文字识别配置
2. YOLO目标检测配置
3. 出场角色以及所有出现的技能配置

你可以在本文找到这些配置的含义, 一般来说, 你只需要设置 `3` 所相关的内容, 也就是`formation` 字段下的内容

```json
{
  "formation": {
    "front": ["Kayoko", "Koharu", "Mika", "Eimi"],
    "back": ["Himari", "Fuuka (New Year)"],
    "slot_count": 3,
    "all_appeared_skills": [
      "Himari",
      "Kayoko",
      "Fuuka (New Year)",
      "Mika",
      "Koharu",
      "Eimi"
    ]
  },
    "BossHealth": {
    "current_ocr_region": [549, 45, 656, 60],
    "max_ocr_region": [666, 45, 775, 60],
    "ocr_region": [549, 45, 775, 60],
    "ocr_model_name": "en-us"
  },
  "yolo_setting": {
    "model": "best.onnx",
    "update_interval": 100
  }
}
```

### `/formation/front`
- **description**: 突击角色的名称列表
- **type**: `list`
- **elements**: 
    - **description**: 角色名称
    - **type**: `string`
- **note**: 
  1. 这些名称直接决定了yolo模型检测的角色列表
  2. `resource/yolo_models/data.yaml` 中`names` 列举了所有可以被yolo模型识别的角色列表, 同时这也是**BAAS** YOLO模型的训练配置
    ![formation_names.png](/assets/auto_fight/yolo_data_yaml_names.png)
  3. 目前可识别的角色还较少, 随着数据集的逐渐扩充, **BAAS**将会适配大部分的学生 / 敌对角色 的识别, 如果你愿意为**BAAS**做一点贡献, 欢迎你参与数据集标注工作, 请在[qq群](/usage_doc/qq_group_regulation/#qq群号)内联系作者

### `/formation/back`
- **description**: 后排角色的名称列表
- **type**: `list`
- **elements**: 
    - **description**: 角色名称
    - **type**: `string`

### `/formation/slot_count`
- **description**: 技能槽的数量
- **type**: `unsigned int`
- **note**: 一般设置为`3`, 未来可能会支持更多的技能槽(爬塔玩法中六槽)

### `/formation/all_appeared_skills`
- **description**: 所有出现的技能名称列表
- **type**: `list`
- **elements**: 
    - **description**: 技能名称
    - **type**: `string`
- **note**:
1. **BAAS**自动战斗在检测技能时, 只会检测该配置列出的技能
2. 你可以在`/resource/images/CN/zh-cn/skill/active`查询已被录入的技能, 这个列表的技能名与该文件夹下的图片名一一对应
![auto_fight_skill_templates](/assets/auto_fight/skill_templates.png)

### `/BossHealth/current_ocr_region`
- **description**: BOSS当前血量的文字识别区域
- **type**: `list`
- **length**: `4`
- **elements**:
    - **description**: 文字识别区域的坐标, 由四个整数值组成, 分别表示`左上角x坐标`, `左上角y坐标`, `右下角x坐标`, `右下角y坐标`
    - **type**: `int`
  
### `/BossHealth/max_ocr_region`
- **description**: BOSS最大血量的文字识别区域
- **type**: `list`
- **length**: `4`
- **elements**: 
    - **type**: `int` 
- **note**: 这个区域的坐标填写和`/BossHealth/current_ocr_region`相同, 但是它的坐标是**BOSS最大血量**的坐标

### `/BossHealth/ocr_region`
- **description**: BOSS血量的文字识别区域
- **type**: `list`
- **length**: `4`
- **elements**: 
    - **type**: `int` 
- **note**: 这个区域的坐标同时包含最大血量和当前血量

### `/BossHealth/ocr_model_name`
- **description**: 文字识别模型的名称
- **type**: `string`
- **constrains**:
  - | 值          | 含义       |
    |------------|----------|
    | `en-us`    | 英文模型     |
    | `zh-cn`    | v4简体中文模型 |
    | `zh-cn_v3` | v3简体中文模型 |
    | `ru-ru`    | 俄文模型     |
    | `ja-jp`    | 日文模型     |
    | `zh-tw`    | 繁体中文模型   |
    | `ko-kr`    | 韩文模型     |
  
- **note**: 一般不需要修改

### `/yolo_setting/model`
- **description**: YOLO模型的名称
- **type**: `string`
- **constrains**:
  - | 值                | 含义     |
    |------------------|--------|
    | `best.onnx`      | fp32模型 |
    | `best_fp16.onnx` | fp16模型 |

### `/yolo_setting/update_inverval`
- **description**: 我们不希望每一张截图都更新目标位置, 设定一定间隔更新
- **type**: `unsigned int`
- **note**: 单位为`ms`, 值越小, 更新频率越快, cpu/gpu的负载越高

## 状态(State)

### `states`
1. 所有状态都在`states`中定义, 它是一个字典, 每个键值对表示一个状态, `键表示状态名`, 值表示状态的参数

**example**:
1. 下图在`states`中定义了三个状态, `状态一` / `状态二` / `状态三`, 起始状态为`状态一`
```json
{
  "state_state": "状态一",
  
  "states": {
    
    "状态一": {

    },
    
    "状态二": {
      
    },
    
    "状态三": {
      
    }
  }  
}
```

### 单个`state`的参数
[`states`](#states) 中的例子列举了三个状态, 但是他们并没有任何实际内容, 我们需要在单个状态中设置以下参数以赋予状态意义 
1. [`action`](#action)
2. [`action_fail_transition`](#action-fail-transition)
3. [`transitions`](#transitions)
4. [`default_transition`](#default-transition)

**note**: 以上个参数都是可选的, 你可以根据需要自行选择

#### `action`
- **description**: 到达这个状态后立即执行的行为（如技能释放, 开启auto/倍速, 重开战斗, 尝试跳过转阶段动画等)
- **type**: `string`
- **constrains**: **动作引用**必须在[`actions`](#actions)中被定义

#### `action_fail_transition`
- **description**: 当`action`执行失败时(如未跳过转阶段动画时), 自动战斗会转移到这个状态
- **type**: `string`
- **constrains**: **状态引用**必须在[`states`](#states)中被定义

#### `transitions`
- **description**: 指示`action`结束后的状态转移, 它是一个`列表`, 每个元素表示[一个状态转移](#一个状态转移)
- **type**: `list`
    - **elements**: 
        - `dict` : 每个元素表示[一个状态转移](#一个状态转移)

#### 一个状态转移
每个状态转移转移表示在某个条件成立时转移到下一个状态, 我们需要指定`条件` 和 `下一个状态`, 分别对应以下参数
1. `condition`
    - **description**: 状态转移的条件名
    - **type**: `string`
    - **constrains**: **条件引用**必须在[`conditions`](#conditions)中被定义

2. `next`
    - **description**: 状态转移的下一个状态名
    - **type**: `string`
    - **constrains**: **状态引用**必须在[`states`](#states)中被定义

#### `default_transition`
1. 当`transitions`中的**所有条件**都不被满足时(或`transitions`没有任何条件), 默认转移状态

### `start_state`
- **description**: 自动战斗开始时的初始状态
- **type**: `string`
- **constrains**: **状态引用**必须在[`states`](#states)中被定义
- **note**: 它**必须**在自动战斗流程文件中被定义, 指示自动战斗开始时的进入的状态

### 示例
**example**: 
1. 当自动战斗转移到这个状态时, 会立即执行`释放技能一`
2. 如果释放技能失败, 转移到`重新开始战斗`
3. 如果释放技能成功, 并且`boss血量小于500w`, 转移到`释放技能二`
4. 否则转移到`重新开始战斗`
```json
{
  "状态一": {
    "action": "释放技能一",
    "action_fail_transition": "重新开始战斗",
    "transitions": [
      {
        "condition": "boss血量小于500w",
        "next": "释放技能二"
      }
    ],
    "default_transition": "重新开始战斗"
  }
}
```

**note**:这个例子中的`action` 以及 `condition` 都还未被定义, 你需要在[`actions`](#动作action) 和 [`conditions`](#条件condition)中学习如何定义这些动作和条件

### 注意事项
1. 初始状态`start_state`**必须被定义**
2. 结束条件: 自动战斗会在**没有任何可转移状态**时退出循环, 可能情况如下:
    - `transitions`中任何条件都不成立, 并且没有`default_transition`
    - `transitions`中没有条件, 并且没有`default_transition`
3. 值得一提的是, 没有`default_transition`, 自动战斗也可以实现它的功能, 你只需要找到所有其他都不成立的条件, 并将其作为transition的最后一个条件也可以实现`default_transition`的功能


## 动作(Action)

### `actions`
1. 所有动作都在`actions`中定义, 它是一个字典, 每个键值对表示一个动作序列, `键表示动作名`, 值是一个**列表**
2. 注意再次强调, 每个`action`的值是一个**列表**, 这个列表中的**每个元素**表示[`一个动作`](#单个action的参数), 你可以将它理解为一个动作序列, 这个动作序列会被依次执行

**example**:
```json
{
  "actions": {
    "释放技能1": [
      {
        "desc": "释放技能1的第一个操作"
      },
      {
        "desc": "释放技能1的第二个操作"
      }
    ],
    "释放技能2": [
      {
        "desc": "释放技能2的第一个操作"
      }
    ]
  }
}
```

**note**: 
设置单一`action`是一个动作列表有许多好处, 如下
1. 允许你自由定义技能释放流程
    - 释放完第一个技能后你可以立刻释放第二个技能, 实现游戏中`反手拐`(在主c技能释放后释放辅助增伤技能)的效果
    - 释放技能前你可以选择调整游戏倍速为`1`
    - 释放技能后你可以选择调整游戏倍速回到`3`
2. 简化了`state`的书写
    - `state`仅需指定`action`的名称, 而不需要重写所有`action`

### 单个`action`的参数

[`actions`](#actions) 中的例子列举了一些动作, 但是他们并没有任何实际内容, 我们需要在单个动作中设置以下参数以赋予状态意义

1. 首先你需要通过`t`字段指定`action`的类型, 合法的`t`如下, 接着你需要根据`t`的值设置额外参数
    - | `t`     | `含义`         | 额外需要的设置的参数                                                        |
      |---------|--------------|-------------------------------------------------------------------|
      | `acc`   | 调整游戏`倍速`     | [`acc动作额外参数`](/develop_doc/script/auto_fight_action_acc#额外参数)     |
      | `auto`  | 调整游戏`auto`状态 | [`auto动作额外参数`](/develop_doc/script/auto_fight_action_auto#额外参数)   |
      | `skill` | 释放技能         | [`skill动作额外参数`](/develop_doc/script/auto_fight_action_skill#额外参数) |


## 条件(Condition)

### `conditions`
1. 所有条件都在`conditions`中定义, 它是一个字典, 每个键值对表示一个条件序列, `键表示条件名`, 值是一个**字典**

**example**:
```json
{
  "conditions": {
    
    "条件1": {

    },
    
    "条件2": {

    }
  }
}
```

### 单个`condition`的参数
[`conditions`](#conditions) 中的例子列举了两个条件, 但是他们并没有任何实际内容, 我们需要在单个条件中设置以下参数以赋予状态意义

1. 首先你需要通过`type`字段指定`condition`的类型, 合法的`type`如下, 接着你需要根据`type`的值设置额外参数
    - | `type`         | `含义`                    | 额外需要的设置的参数                                                                         |
      |----------------|-------------------------|------------------------------------------------------------------------------------|
      | `and_combined` | 组合条件<br/>若干条件同时成立时才成立的  | [`and_combined条件额外参数`](/develop_doc/script/auto_fight_condition_and_combined#额外参数) |
      | `or_combined`  | 组合条件<br/>若干条件中任意一个成立就成立 | [`or_combined条件额外参数`](/develop_doc/script/auto_fight_condition_or_combined#额外参数)   |
      | `skill_name`   | 技能名称相关                  | [`skill_name条件额外参数`](/develop_doc/script/auto_fight_condition_skill_name#额外参数)     |
      | `cost`         | 费用相关                    | [`cost条件额外参数`](/develop_doc/script/auto_fight_condition_cost#额外参数)                 |
      | `boss_health`  | boss血量相关                | [`boss_health条件额外参数`](/develop_doc/script/auto_fight_condition_boss_health#额外参数)   |

2. 可选参数
    - [`timeout`](#timeout)
    - [`and`](#and) 
    - [`or`](#or)

#### `timeout`
**description**: 判断这个条件成立的时限, **超时则认为该条件不成立**
- **type**: `unsigned int`
- **note**: 
    1. 这个参数的设计是为了避免条件判断陷入死循环
    2. 单位为`ms`, 默认为`5000`

#### `and`
**description**: 你可以指定一系列条件, 当前条件成立时, 这些条件必须同时成立(加强条件的成立要求)
- **type**: `list`
    - **elements**: 
        - **description**: 需要同时成立条件的名称
        - **type**: `string`
        - **constrains**: **条件引用**必须在[`conditions`](#conditions)中被定义

#### `or`
**description**: 你可以指定一系列条件, 如果它们中任意一个成立, 当前条件也会被视为成立(可以理解为一种补救措施, 减弱条件成立要求)
- **type**: `list`
    - **elements**: 
        - **description**: 补救条件的名称
        - **type**: `string`
        - **constrains**: **条件引用**必须在[`conditions`](#conditions)中被定义
    
**note**: 一个条件存在`本体`, `与条件`和 `或条件`, 它们共同决定了条件成立与否, 具体逻辑如下
1. 在一轮截图 + 数据更新后进行条件判断
    - `本体`待定, 某个`与条件`不成立, 则认为整体条件不成立
    - `本体`待定, 某个`或条件`成立, 则认为整体条件成立
    - `本体`待定, 没有不成立的`与条件`, 且没有成立的`或条件`, 则继续进行截图 + 数据更新
    - `本体`成立, 某个`与条件`不成立, 则认为整体条件不成立
    - `本体`成立, 没有不成立的`与条件`, 且有待定的`与条件`, 则继续进行截图 + 数据更新
    - `本体`不成立, 某个`或条件`成立, 则认为整体条件成立
    - `本体`不成立, 没有成立的`或条件`, 且有待定的`或条件`, 则继续进行截图 + 数据更新

### 条件类(Condition Class)
我们希望[可监测的数据](#可监测的数据)满足一些条件时进行自动化操作, 条件类让我们能用一种规范的语言表达我们所需要的条件

1. 为了持续监测条件
    - 在循环中依次执行 `截图 --> 数据更新 --> 条件判断`
    - 数据更新前, 遍历每个`condition`, 通过标志位指示需要被更新的数据
    - 数据更新前, 首先判断界面是否为战斗中, 非战斗中则重新截图
    - 数据更新前, 等待正在更新数据线程数为`0` (防止同一数据更新同时进行)
    - 由上一条可得, 如果`一条数据`不被当前`任意一个condition`所需要, 则不更新会该数据 
    - 当某一条件成立 / 所有条件不成立时结束判断
2. 单一状态信息更新后**紧接着**进行条件判断
    - 条件判断的耗时远低于数据更新, 如果有多条数据同时在更新, 其中一条数据更新完毕后立即进行条件判断
3. 根据[可监测的数据](#可监测的数据)中任意**一个**进行比较的条件称为`原始条件 (primitive condition)`
4. 条件可根据`or / and`进行自由组合, 称为`组合条件`
5. 每个条件包含`timeout`字段
    - 条件判断开始后时限内期望条件未被判断为(未)成立则认为该条件不成立
    - 设计`timeout`的一大原因是可以有效避免条件判断陷入死循环
6. 条件类仅在加载自动战斗工作流时初始化, 条件类可被重复使用, 每次使用`condition`前刷新上一次使用的数据
7. `desc`字段作为这个条件的描述, 方便理解, 并不会对条件判断产生任何影响


### 条件判断 (Condition Judgement)
按照下图的架构实现自动战斗的条件判断, 该架构设计参照[条件类](#条件类-condition-class)所需的特性
![condition_judgement.png](/assets/condition_judgement.png)

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


# `Class AutoFight`

- **description**: 集成 condition / action / state 并最终执行自动战斗的类

## 成员变量 (Members)

### `config`


### `logger`


### `default_active_skill_template` / `default_inactive_skill_template`


### `template_j_ptr_prefix`


### `d_update_max_thread`

**type**: int
**description**: 数据更新最大同时运行的线程数量 (线程池大小)

## `d_update_thread_pool`
**type**: `std::unique_ptr<ThreadPool>`
**description**: 数据更新使用的线程池

## `d_update_thread_mutex`
**type**: `std::mutex`
**description**: 用于线程同步的互斥量


## `d_updater_running_thread_count`
**type**: `std::atomic<int>`
**description**: 当前正在运行的数据更新线程数量

## `d_updater_thread_finish_notifier`
**type**: `std::condition_variable`
**description**: 用于通知数据更新线程结束的条件变量

## `d_updaters`
**type**: `std::vector<std::unique_ptr<BaseDataUpdater>>`
**description**: 指向所有数据更新类的指针集合

## `d_wait_to_update_idx`
**type**: `std::vector<uint8_t>`
**description**: 需要被执行的数据更新函数所对应的类在[`d_updaters`](#d-updaters)中的索引

## `d_updater_queue`
**type**: `std::queue<uint8_t>`
**description**: 根据数据更新的预估耗时排序后的`d_wait_to_update_idx`队列

## `d_updater_map`
**type**: `std::map<std::string, uint64_t>`
**description**: 数据更新类的名称与偏移的映射

## `d_auto_f`
**type**: `auto_fight_d`
**description**: 自动战斗的共享数据, 用于在 `action` / `condition` / `updaters` / `state` 之间传递数据

## `_cond_type`
**type**: `std::string`
**description**: 目前正在录入的条件的类型名称

## `all_cond`
**type**: `std::vector<std::unique_ptr<BaseCondition>>`
**description**: 所有条件的指针集合

## `cond_name_idx_map`
**type**: `std::map<std::string, uint64_t>`
**description**: 条件名与[`all_cond`](#all-cond)中位置的映射
**note**:
1. 请注意**条件名**与**条件类型名**是完全不同的概念

## `_cond_is_matched_recorder`
**type**: `std::vector<bool>`
**description**: 记录条件是否成立, 已被判断成立 / 不成立的条件不会参与以下内容
1. 超时检查
2. 条件成立判断

**note**:  
1. 长度与[`all_cond`](#all-cond)相同

## `_cond_checked`
**type**: `std::vector<bool>`
**description**: 条件的 超时监测 / 重置状态 / 成立判断 是递归进行的, 记录每一项检查过的条件, 避免无限递归
**note**:
1. 长度与[`all_cond`](#all-cond)相同

## `all_state`
**type**: `std::vector<state_info>`
**description**: 所有状态集合

## `_state_trans_name_recorder`
**type**: `std::vector<std::vector<std::string>>`
**description**: 每个state可能有多个状态转移, 记录每个状态的每个状态转移的下一个状态名
**note**: 当一个状态初始化时, 可能它的目标状态未初始化, 此时不知道该状态的索引, 该变量记录所有转移的下一个状态名, 以便再次遍历更新索引

## `_state_default_trans_name_recorder`
**type**: `std::vector<std::optional<std::string>>`
**description**: 作用同[`_state_trans_name_recorder`](#state-trans-name-recorder), 使用`optional`原因为`state`允许没有默认转移

## `state_name_idx_map`
**type**: `std::map<std::string, uint64_t>`
**description**: 状态名与[`all_state`](#all-state)中位置的映射

## `_curr_state_idx`
**type**: `uint64_t`
**description**: 当前状态的索引

## `_state_cond_j_start_t`
**type**: `long long`
**description**: 状态转移 条件判断循环的开始时间(ms)

## `_state_cond_j_loop_start_t`
**type**: `long long`
**description**: 状态转移 条件判断循环每一轮循环的开始时间(ms)

## `_state_cond_j_elapsed_t`
**type**: `long long`
**description**: 状态转移 条件判断循环的总耗时(ms)

## `_state_trans_cond_matched_idx`
**type**: `std::optional<uint64_t>`
**description**: 第一个状态转移条件成立的转移索引

## `_state_flg_all_trans_cond_dissatisfied`
**type**: `bool`
**description**: 指示是否所有状态转移条件都不成立

## `_state_cond_j_loop_running_flg`
**type**: `bool`
**description**: 指示条件判断循环是否正在运行

## `start_state_name`
**type**: `std::string`
**description**: 初始状态的名称

## `workflow_path`
**type**: `std::filesystem::path`
**description**: 轴文件的路径

## `workflow_name`
**type**: `std::string`
**description**: 轴的名称

## `baas`
**type**: `BAAS*`
**description**: `BAAS`实例

