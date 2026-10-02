# 挂调度（scheduler 类）插件说明

local 模板不用读这个；要写**常驻调度型**工具（每天自动跑、拦截队列等）才需要。

## manifest 变化（相对 local 模板）

```jsonc
{
  "kind": "scheduler",                      // 必须；缺 scheduler 节会被判为加载失败
  "scheduler": {
    "event_name": "囤体",                   // 挂到哪个调度事件（与 main.schedule 里的事件名一致）
    "func_name": "my_tool_run",             // 调度调用的函数名（注册到你模块的名字）
    "owns_funcs": true,                     // 本插件自己管理这些函数的启停（一般 true）
    "priority": -3,                         // 越小越先跑
    "interval": 300,                        // 轮询间隔（秒）
    "daily_reset": ["04:00"]                // 可选：每日重置时刻列表
  },
  "intercept": {                            // 可选：调度队列拦截
    "funcs": ["some_func"],                 // 要拦截的函数名
    "always_allow": [],                     // 无条件放行的函数名
    "custom": false                         // true=自己实现 filter（进阶）
  }
}
```

## 红线

1. `kind=scheduler` 而**没有** `scheduler` 节 → 加载失败（大厅显示禁用卡）；
2. `kind=local` 声明 `intercept` → 被忽略并告警；
3. `func_name` 指向的函数必须真实存在，框架的 gate 会按清单校验函数归属；
4. 拦截不影响主线的函数不要放进 `funcs`，避免与主线抢队列。
