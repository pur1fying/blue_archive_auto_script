# 插件作者指南（tools framework）

> 三步上手：复制 `module/tools/_template/` → 改名 → 写业务。
> 复制后**目录名不要带下划线开头**（`_` 开头的目录框架直接跳过）。

## 1. manifest.json 逐字段说明

```jsonc
{
  // 必填。全局唯一 id；配置键、主页开关键都从它派生
  "id": "my_tool",

  // 必填。显示名（大厅卡片、自动主页按钮「进入」+前四字）
  "name": "我的工具",

  "version": "1.0.0",          // 语义化版本，框架不校验
  "summary": "一句话说明",      // 大厅卡片副标题
  "icon": "APPLICATION",       // FluentIcon 图标名，见 qfluentwidgets
  "category": "general",       // 大厅分类（保留字段）
  "order": 150,                // 大厅/主页排序权重，越小越靠前

  // local=纯界面工具；scheduler=挂调度（需 scheduler 节）；home=纯主页板块
  "kind": "local",

  // 入口："module.tools.<目录名>.tool:Tool"；留空=按目录名默认
  "entry": "module.tools.my_tool.tool:Tool",

  // 留空即可（框架按"能力"探测页面，不要求声明）
  "ui": "",

  // 配置键前缀；留空=默认 tool_<id>_
  "config_prefix": "tool_my_tool_",

  // ★ 配置声明：键名=前缀+字段，值类型决定自动设置的控件
  //   bool→开关  int→旋钮  str→输入框
  //   枚举→ ["甲","乙"]（默认=第一项）
  //     或 {"type":"enum","options":[...],"default":"乙","label":"显示名"}
  //   任何类型都能写 dict 形式拿完整控制：
  //     {"type":"int","min":1,"max":10,"default":3,"label":"数量","restart":true}
  //   "restart":true → 设置页显示名追加（重启生效）提示
  //   dict 里都能带 "label" 自定义设置页显示名
  "config_defaults": {
    "tool_my_tool_enabled": true,
    "tool_my_tool_max_count": 3,
    "tool_my_tool_note": "示例文本",
    "tool_my_tool_mode": ["标准", "极速", "稳定"]
  },

  "enabled_by_default": true,  // scheduler 工具的默认开关（local 无意义）
  "show_in_lobby": true        // false=不在大厅出现
}
```

**禁止项**：`kind=local` 不允许声明 `intercept`（写了也会被忽略并告警）。

## 2. 框架自动发放（什么都不用写）

| 能力 | 说明 |
|------|------|
| 主页入口 | 未声明 `home` 的插件自动发「进入××」蓝色按钮（取 name 前四字），主页栏位随大厅「栏1/栏2」选择 |
| 大厅顶栏 | 自动发「主页显示」开关（键 `tool_<id>_home_visible`，默认开） |
| 插件设置 | `config_defaults` 声明的字段自动生成顶栏「插件设置」弹窗：开关/旋钮/输入框/下拉，改完即时落盘 config.json |

## 3. 必写的代码：tool.py

```python
from module.tools.base import ToolPlugin

class Tool(ToolPlugin):
    def build_widget(self, parent=None, config=None):
        from module.tools.my_tool.ui import Layout
        return Layout(parent=parent, config=config)
```

- 读配置：`getattr(config.config, "tool_my_tool_max_count", 3)`
  （框架在启动时已把注册键 setattr 到内层 config 上）
- 可选钩子：`on_enable/on_disable(config)`、`validate_config(config)`、
  `build_home_widget(parent, config)`（想自定义主页板块才覆盖）

## 4. UI 红线（详见 THEME_BORDER.md）

1. 颜色一律走 `gui/components/expand/tool_style.py` 的 `themed_*()`；
2. 插件内部边框 1px；2px 属于框架基层设置栏（棋盘画布类描边除外）；
3. `paintEvent` 里禁止对 painter 字体 `setPointSize/setFont`（像素字体静默掉画）；
4. 布局出问题先查几何，不要去改 tool_style.py（那是主题引擎，只管颜色）。

## 5. 加载失败会怎样

`registry.load_all` 按目录隔离：单个插件 manifest/入口炸了只会
在工具大厅出现一张灰卡「<目录名>（加载失败已禁用）」+ 错误摘要，
主页栏尾也会有一行「⚠ 插件加载失败已禁用：…」，其余插件与主程序
不受影响。作者按摘要里的异常文字排查即可。
`registry.errors`（property）= `{目录名: 错误}`，可用于自检。
注意：`kind=scheduler` 而**没有** `scheduler` 节会被判为加载失败
（详见 `module/tools/_template/README_SCHEDULER.md`）。
