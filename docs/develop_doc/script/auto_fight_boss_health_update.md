# Boss血量 (Boss Health)

## 相关配置 (Related Config)

## static_config

`"/BAAS/auto_fight/BossHealth"` 字段下

```json
{
    "BossHealth": {
      "current_ocr_region": [549, 47, 656, 64],
      "max_ocr_region": [666, 47, 775, 64],
      "ocr_region": [549, 47, 775, 64]
    }
}
```
### `current_ocr_region`
- **type**: `List[int]`
- **length**: `4`
- **description** : BOSS实际血量文字识别区域
- **note** : 不同服务器, 不同BOSS, 血量分割符位置完全相同, 因此这个数据可通用, 下同理

### `max_ocr_region`
- **type**: `List[int]`
- **length**: `4`
- **description** : BOSS最大血量文字识别区域


### `ocr_region`
- **type**: `List[int]`
- **length**: `4`
- **description** : `current_ocr_region` + `max_ocr_region` 拼接的识别区域

## screenshot_data
```cpp
struct screenshot_data {
    std::optional<long long> boss_current_health;
    std::optional<long long> boss_max_health;
    std::uint8_t boss_health_update_flag = 0b010;
}
```

### `boss_current_health`
- **type**: `std::optional<long long>`
- **description**: BOSS当前血量

### `boss_max_health`
- **type**: `std::optional<long long>`
- **description**: BOSS最大血量

### `boss_health_update_flag`
- **type**: `std::uint8_t`
- **description**: BOSS血量需要更新数据的标志位
- **meaning**:

    | 位     | 含义          |
    |-------|-------------|
    | `001` | 更新最大血量      |
    | `010` | 更新当前血量      |
    | `100` | 更新当前血量和最大血量 |
