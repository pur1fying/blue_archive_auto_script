# 费用 (Cost)

指可用于释放学生技能的费用

## 简介 (Introduction)
1. 本文主要考虑如何在图像中高效的提取以下信息:
   1. 可用于释放学生技能的费用(`Cost`)

## `CostUpdater`


## `cost`精度
可监测的`cost`最小变化精度约为 **0.035(1/28.7)**
- **note** : 也就是说填写任何表示`cost`值时, 最大精度为小数点后两位

## `CostCondition`
以下为cost比较方法


### `op`
- **type**: `string`
- **description** : 指示数据比较操作
- **constrains**:
-   | 值          | 含义   | 必填字段              |
    |------------|------|-------------------|
    | `over`     | 大于   | [`value`](#value) |
    | `below`    | 小于   | [`value`](#value) |
    | `in_range` | 处于区间 | [`range`](#range) |
    | `increase` | 增长   | [`value`](#value) |
    | `decrease` | 下降   | [`value`](#value) |

### `value`
- **type** : `double`
- **range** : [0.0, 10.0]

### `range`
- **type** : `List[double]`
- **length** : 2
  - **element** : `double`
  - **range** : [0.0, 10.0]
- **description** : 期望的`cost`值所在区间
- **note**: 值1 < 值2, 增量应大于[最大精度](#cost精度), 否则`range`中的值可能将永远无法被监测到

### `reset`
- **type** : `bool`
- **description** : 指示条件判断开始前是否重置记录的`cost`值
