## 简介(Introduction)
用于boss血量比较的条件

## 额外参数

## `op`
- **description**: 比较类型
- **type**: `string`
- **constrains**:
  - | 值            | 含义       | 额外参数              |
    |--------------|----------|-------------------|
    | `C_over`     | 当前血量高于   | [`value`](#value) | 
    | `C_below`    | 当前血量低于   | [`value`](#value) |
    | `C_in_range` | 当前血量在范围内 | [`range`](#range) |
    | `C_increase` | 当前血量增加   | [`value`](#value) |
    | `C_decrease` | 当前血量减少   | [`value`](#value) |
    | `M_equal`    | 最大血量值等于  | [`value`](#value) |

## `value`
- **description**: 用于比较的boss血量数值
- **type**: `double`

## `range`
- **description**: 用于范围内比较的boss血量数值
- **type**: `list`
- **length**: 2
    - **elements**:
        - **description**: 范围比较的最小值和最大值
        - **type**: `double`
