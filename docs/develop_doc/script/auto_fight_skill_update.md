# 技能 (Skill)

## 简介 (Introduction)
1. 本文主要考虑如何在图像中高效的提取以下信息:

   `a.` 每个槽`Slot`的技能名称

   `b.` 技能是否可用`Active`

   `c.` 每个槽的技能费用`Cost`是多少
2. `a` 与 `b` --> [`SkillNameUpdater`](#skillnameupdater)
3. `c` --> [`SkillCostUpdater`](#skillcostupdater)


## `SkillNameUpdater`

## `SkillCostUpdater`

## 相关配置

## static_config
`"/BAAS/auto_fight/Skill"` 字段下

```json
{
  "Skill": {
    "slot": {
      "center": [
        [883,  621],
        [985,  621],
        [1087, 621]
      ],
      "match_template_regions": [
        [839, 594, 982, 670],
        [940, 594, 1032, 670],
        [1041, 594, 1133, 670]
      ],
      "cost_ocr_regions": [
        [839, 594, 982, 670],
        [940, 594, 1032, 670],
        [1041, 594, 1133, 670]
      ]
    },
    "templates": {
      "Ui": {
        "active": ["active"],
        "inactive": ["l_inactive", "r_inactive"]
      }
    }
  }
}
```

### `/slot/center`
- **type**: `List`
- **length**: `3`
    - **elements**:
        - **type**: `List[int]`
        - **length**: `2`
- **description** : 每个技能槽中心
- **note** : 释放技能时选定技能的坐标

### `/slot/match_template_regions`
- **type**: `List`
- **length**: `3`
    - **elements**:
        - **type**: `List[int]`
        - **length**: `4`
- **description** : 每个技能槽的模板匹配区域
- **note** : 该区域内的图像会被提取出来, 用于与[`技能模板`](#templates)进行匹配

### `/slot/cost_ocr_regions`
- **type**: `List`
- **length**: `3`
    - **elements**:
        - **type**: `List[int]`
        - **length**: `4`
- **description** : 每个技能槽的`cost`文字识别区域

### `/templates`
- **type**: `Dict`
- **description** : 技能槽的模板
- **note**: 
    1. `active` : 技能可使用时模版, 默认含一个值`active`
    2. `inactive` : 技能不可使用时模版, 默认含两个值`l_inactive`和`r_inactive`
- **example**:
    默认的三个模板图像
    1. `active`
    ![active](/assets/auto_fight/example_skill_active_template.png) 
    2. `l_inactive`
    ![l_inactive](/assets/auto_fight/example_skill_l_inactive_template.png)
    3. `r_inactive`
    ![r_inactive](/assets/auto_fight/example_skill_r_inactive_template.png)

## screenshot_data

```cpp
struct slot_skill{
    std::optional<int>         index;    
    std::optional<int>         cost;     
    std::optional<bool>        is_active;
};

struct template_info {
    cv::Mat template;
    std::vector<double> estimated_match_template_time_cost;
}

struct skill_template {
    std::string name;    
    std::vector<template_info> active_templates;
    std::vector<template_info> inactive_templates;
}

struct screenshot_data {
    std::vector<slot_skill>  skills;
    std::vector<std::vector<int>> each_slot_possible_templates; 
    std::vector<skill_template> all_possible_skills;
    uint32_t skill_cost_update_flag = 0b000000;
    int slot_count;
}
```

## struct `slot_skill`
记录运行时一个槽检查状态的数据

### `index`
- **type**: `std::optional<int>`
- **description**: 识别到的技能在[`all_possible_skills`](#all-possible-skills)中的索引

### `cost`
- **type**: `std::optional<int>`
- **description**: 识别到的技能槽的`cost`值

### `is_active`
- **type**: `std::optional<bool>`
- **description**: 识别到的技能是否可用

## struct `template_info`
记录技能槽的模板图像数据, 以及模板匹配的估计时间

### `template`
- **type**: `cv::Mat`
- **description**: 模板图像

### `estimated_match_template_time_cost`
- **type**: `std::vector<double>`
- **length**: [`skills.size()`](#skills)
- **description**: 在每个槽的模版匹配的估计时间

## struct `skill_template`
记录技能槽的模板图像数据

### `name`
- **type**: `std::string`
- **description**: 技能名称

### `active_templates`
- **type**: `std::vector<template_info>`
- **description**: 技能可用模板

### `inactive_templates`
- **type**: `std::vector<template_info>`
- **description**: 技能不可用模板

## struct `screenshot_data`

### `skills`
- **type**: `std::vector<slot_skill>`
- **description**: 记录运行时每个技能槽的状态数据

### `each_slot_possible_templates`
- **type**: `std::vector<std::vector<int>>`
- **description**: 每个槽可能的技能的技能在[`all_possible_skills`](#all-possible-skills)中的索引, 用于模板匹配

### `all_possible_skills`
- **type**: `std::vector<skill_template>`
- **description**: 所有可能的技能模板

### `skill_cost_update_flag`
- **type**: `uint32_t`
- **description**: 第i位表示第i个[`skill`](#skills)的[`cost`](#cost)需要更新

### `slot_count`
- **type**: `int`
- **description**: 技能槽总数, [skills](#skills) , [each_slot_possible_templates](#each_slot_possible_templates)与之等长

## `SkillNameUpdater`
### `estimated_time_cost()`
1. 模版匹配的耗时:
    设模版图像的大小为 `x1,y1`, 匹配区域的大小为 `x2,y2`, 则
    ```cpp
    double t_one_match_template = (x2 - x1 + 1) * (y2 - y1 + 1) * (x2 * y2)
    ```
2. 每次`update()`需要的耗时
    假设每个槽中出现的技能概率相同, 并且每个模板出现的概率也相同
    
    ```cpp
    double cost = 0.0;
    size_t tmp_cnt;
    double d_tmp_cnt;
    for (int i = 0; i < data->each_slot_possible_templates.size(); i++) {
        for (auto& _template : data->each_slot_possible_templates[i]) {
            tmp_cnt = data->all_possible_skills[_template].skill_active_templates.size() +
                      data->all_possible_skills[_template].skill_inactive_templates.size();
        }
        d_tmp_cnt = double(tmp_cnt);
        for (int j = 0; j < data->each_slot_possible_templates[i].size(); j++) {
            for (auto _template : data->all_possible_skills[data->each_slot_possible_templates[i][j]].skill_active_templates)
                cost += _template.estimated_match_template_time_cost[i] * (d_tmp_cnt - j) / d_tmp_cnt;
            for (auto _template : data->all_possible_skills[data->each_slot_possible_templates[i][j]].skill_inactive_templates)
                cost += _template.estimated_match_template_time_cost[i] * (d_tmp_cnt - j) / d_tmp_cnt;
        }
    }

    return cost
    ```

## `SkillCostUpdater`

### `estimated_time_cost()`
1. 每更新一个技能的cost需要进行一次ocr, 平均耗时为 `更新技能数 * 一次ocr平均耗时`
2. code
    ```cpp
    cost = double(BAASUtil::count_bit(data->skill_cost_update_flag)) * 1.0 * 1e8;
    ```
