## 简介(Introduction)
用于费用比较的条件

## 额外参数

## `op`
- **description**: 比较类型
- **type**: `string`
- **constrains**:
  - | 值          | 含义     | 额外参数              |
    |------------|--------|-------------------|
    | `over`     | 费用高于   | [`value`](#value) | 
    | `below`    | 费用低于   | [`value`](#value) |
    | `in_range` | 费用在范围内 | [`range`](#range) |
    | `increase` | 费用增长   | [`value`](#value) |
    | `decrease` | 费用减少   | [`value`](#value) |

## `value`
- **description**: 用于比较的费用值
- **type**: `double`
- **range**: [0.0, 10.0]

## `range`
- **description**: 用于范围内比较的费用值
- **type**: `list`
- **length**: 2
    - **elements**:
        - **description**: 范围比较的最小值和最大值
        - **type**: `double`
        - **range**: [0.0, 10.0]
