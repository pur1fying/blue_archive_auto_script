# 数据更新基类 `class BaseDataUpdater`

```cpp
class BaseDataUpdater {
public:
    explicit BaseDataUpdater(BAAS* baas, screenshot_data* data);

    virtual void update();

    virtual double estimated_time_cost();

    virtual constexpr std::string data_name();

    virtual void display_data();

protected:
    BAASLogger* logger;

    BAAS* baas;

    screenshot_data* data;
};
```

## 成员函数 (Member Functions)

### `update`
- 每一项数据更新的具体逻辑在此实现

### `estimated_time_cost`
- 数据更新的预估时间, 用于决定数据更新顺序

### `data_name`
- 数据名

### `display_data`
- 展示更新数据

## 成员变量 (Members)

### `logger`
日志记录器指针

### `baas`
`baas` 类实例, 提供模拟器交互 / 截图等api

### `screenshot_data`
指向自动战斗数据记录结构的指针
