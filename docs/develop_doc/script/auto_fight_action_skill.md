## 简介(Introduction)
用于角色技能释放的动作

我们先来考虑一下如何在游戏内释放一个角色的技能?
1. 通过 `auto` 游戏会帮助我们自动释放技能
2. 通过点击`技能槽`, 我们可以`选中技能`, 再次点击一个位置([技能目标](#target)), 我们可以向这个位置释放技能
3. 通过观测费用条的下降, 我们可以监测技能是否释放成功([释放检查](#check))

**note**:
1. 总而言之, 我们需要确定释放技能的`技能槽`, 技能释放的`坐标`, 以及技能完成释放的`标志` 
    - [`skill_n`](#skill-n) 和 [`l_rel_idx`](#l-rel-idx) 用于确定释放技能的`技能槽`
    - [`target`](#target) 用于确定释放技能的`坐标`
    - [`check`](#check) 用于检查技能是否被正确释放
2. `auto` 释放技能并不需要我们指定技能槽和目标位置, 游戏会自动帮我们做决定, 但是我们需要知道`cost`下降了多少时, 认定技能被成功释放, 也就是说我们需要设置[`check`](#check)

## 额外参数

## `op`

- **description**: 释放一个技能的方式
- **type**: `string`
- **constrains**:
- 
    | 值         | 含义                                     | 必须设置的额外参数                                     |
    |-----------|----------------------------------------|-----------------------------------------------|
    | `auto`    | 开启`auto`释放                             | [`check`](#check)                             |
    | `name`    | 通过技能名查找槽中对应技能                          | [`target`](#target) [`skill_n`](#skill-n)     |
    | `l_rel_p` | 上一个释放的技能的所在技能槽会被选择<br/>(不需要通过技能名确定技能槽) | [`target`](#target) [`l_rel_idx`](#l-rel-idx) |

**note**:
1. 方式 `auto` 需要设置[`check`](#check)
2. 方式 `name`, `l_rel_p` 需要设置[`target`](#target) 
3. 方法 `l_rel_p` 是专门为`反手拐`设计的

## `skill_n`
- **description**: 需要释放的技能的名称
- **type**: `string`
- **note**: 技能名称必须在`/formation/all_appeared_skills`中出现
- **example**:
```json
{
  "formation": {
    "all_appeared_skills": [
      "Himari",
      "Kayoko",
      "Fuuka (New Year)",
      "Mika",
      "Koharu",
      "Eimi"
    ]
  },
  
  "actions": {
    
    "释放风香(新年)的技能": [
      {
        "p": "skill",
        "op": "name",
        "skill_n": "Fuuka (New Year)"
      }
    ]
  }
}
```

## `l_rel_idx`
- **description**: 设前三个释放技能的技能槽分别为`0, 1, 2`, 注意`0`是最近释放的技能, 假设本配置的数值为`0`, 则会选择槽`0`的技能释放, 如果数值为`2`, 则会选择槽`2`的技能释放
- **note**: 
1. 设计这个技能释放方式的初衷是允许跳过技能检测, 当你已知某个技能释放完后下一个技能就是你所需要释放的技能, 可以`跳过技能名称检测`这一步骤, 直接释放技能
2. 举一个现实的例子, 你刚刚释放完`女仆爱丽丝`技能, 按照轴流程可以确定这个技能的下一个技能必定是`亚子`, 此时你可以设置值为`0`跳过技能检测, 直接释放`女仆爱丽丝技能释放完毕后对应槽出现的下一个技能`

- **type**: `int`
- **range**: `[0, 2]`
- **example**:
  - 释放 **爱丽丝 (女仆)** 的技能后立即释放 **亚子** 技能到 **爱丽丝 (女仆)** 
  ```json
  {
    "actions": {
      
      "释放 爱丽丝 (女仆) 的技能后立即释放 亚子 技能到 爱丽丝 (女仆) ": [
        {
          "p": "skill",
          "op": "name",
          "skill_n": "Aris (Maid)",
          "target": {
          
          }
        }
      ]
    }
  }
  ```

## `target`

### `/target/op`
- **description**: 技能释放的目标类型, 固定位置 / yolo检测位置
- **type**: `string`
- **constrains**:
  - | 值          | 含义           | 需要字段                                              |
    |------------|--------------|---------------------------------------------------|
    | `fixed`    | 固定坐标         | [`/target/x`](#target-x) [`/target/y`](#target-y) |
    | `yolo_t_p` | yolo检测矩形顶部中心 | [`/target/obj`](#target-obj)                      |
    | `yolo_c_p` | yolo检测矩形中心   | [`/target/obj`](#target-obj)                      |
    | `yolo_g_p` | yolo检测矩形底部中心 | [`/target/obj`](#target-obj)                      |
    | `yolo_l_p` | yolo检测矩形左侧中心 | [`/target/obj`](#target-obj)                      |
    | `yolo_r_p` | yolo检测矩形右侧中心 | [`/target/obj`](#target-obj)                      |
- **examples**:
1. 释放 **风香 (新年)** 技能至 **固定坐标`(1180, 360)`**
    ```json
    {
      "actions": {
        
        "释放**风香 (新年)** 的技能到固定点位(1180, 360)": [
          {
            "p": "skill",
            "op": "name",
            "skill_n": "Fuuka (New Year)",
            "target": {
              "op": "fixed",
              "x": 1180,
              "y": 360
            }
          }
        ]
      }
    }
    ```
2. 释放 **风香 (新年)** 技能至yolo检测到的 **未花** 位置的 **矩形中心**
    ```json
    {
      "actions": {
        
        "释放风香 (新年) 技能至yolo检测到的未花位置的中心": [
          {
            "p": "skill",
            "op": "name",
            "skill_n": "Fuuka (New Year)",
            "target": {
              "op": "yolo_c_p",
              "obj": ["Mika"]
            }
          }
        ]
      }
    }
    ```

3. 释放 **小春** 技能至yolo检测到的 **未花** 和 **艾米** 的 **底部连线** 的中心
   ```json
   {
      "释放 小春 技能至yolo检测到的 未花 和 艾米 位置的底部连线的中心": [
        {
          "t": "skill",
          "op": "name",
          "skill_n": "Koharu",
          "target": {
            "op": "yolo_g_p",
            "obj": ["Mika", "Eimi"]
          }
        }
      ]
   }
   ```

### `/target/x`
- **description**: 释放技能到固定位置的x坐标
- **type**: `int`
- **range**: `[0, 1280]`

### `/target/y`
- **description**: 释放技能到固定位置的y坐标
- **type**: `int`
- **range**: `[0, 720]`

### `/target/obj`


## `check`

- **description**: 检查技能是否被释放的方式
- **type**: `dict`
- **note**:
    `dict`中的参数
    1. [`op`](#check-op)
    2. [`value`](#check-value)
    3. [`timeout`](#check-timeout)
- **examples**:
一个增加了`check`的动作
  - 这个动作的含义是, 使用`auto` 释放技能, 当`cost`下降2.5时认定技能释放成功
  - 在`5000ms`内没有检测到`cost`下降, 认定技能释放失败

```json
{
  "actions": {
    
    "释放技能1": [
      {
        "p": "skill",
        "op": "auto",
        "check": {
          "op": "C_decrease",
          "value": 2.5,
          "timeout": 5000
        }
      }
    ]
  }
}
```
**note**:
1. 如果技能原始的释放费用为`x`, 推荐设置检查费用下降值为`x - 0.5`, 原因是虽然技能实际使用了`x`的费用, 但是费用在截图中的每一帧都会增长, **BAAS**实际能监测到的费用下降约为`x - 0.1`(略小于`x`), 这也是上文例子设置为2.5的原因

### `/check/op`
- **description**:技能释放检查的方式
- **type**: `string`
- **constrains**:
-   | 值           | 含义                  | 必须设置的额外参数               |
    |-------------|---------------------|-------------------------|
    | `C_decrese` | 通过`cost`下降监测技能是否被释放 | [`value`](#check-value) |

### `/check/value`
- **description**: 当`op`为`C_decrease`时, 含义为`cost`下降的值
- **type**: `double`

### `/check/timeout`
- **description**: 技能释放检测的超时时间, 单位为ms
- **type**: `int`
- **default value**: 5000
