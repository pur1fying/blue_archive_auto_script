## 简介(Introduction)
当你需要确定角色技能是否出现 / 在特定位置出现时, 可以使用该条件

- 例
1. 你可以在进入战斗时使用`at`来确定技能初始顺序是否正确
2. 在战斗过程中使用`appear`确定特定技能是否出现

## 额外参数

## `op`

- **description**: 比较类型
- **type**: `string`
- **constrains**:
  - | 值        | 含义     | 额外参数                      |
    |----------|--------|---------------------------|
    | `appear` | 技能出现   | [`name`](#name)           | 
    | `at`     | 技能在特定槽 | [`name`](#name) [`p`](#p) |

## `name`
- **description**: 技能名称
- **type**: `string`
- **constrains**: 必须是[`all_appeared_skills`](/develop_doc/script/auto_fight#formation-all-appeared-skills)中出现的名称

## `p`
- **description**: 技能槽位置
- **type**: `unsigned int`
- **range**: [0, [`slot_count`](/develop_doc/script/auto_fight#formation-slot-count)]
