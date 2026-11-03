# -*- coding: utf-8 -*-
"""插件配置声明 → 自动设置界面（作者零 Qt）。

声明处：manifest.config_defaults。默认值类型决定控件：
- bool  → 开关（SwitchButton）
- int   → 旋钮（SpinBox，0..9999）
- str   → 输入框（LineEdit）
- 枚举  → 下拉（ComboBox）；声明方式二选一：
    1) 值直接写选项列表 ["甲", "乙"]（默认=第一项）
    2) 值写 {"type": "enum", "options": ["甲", "乙"], "default": "乙"}

dict 形式可用 "label" 自定义显示名；普通键显示名 = 去掉
config_prefix（或 tool_）前缀后的原文。框架读当前值走
config 实例（ConfigSet.load 已把注册键 setattr 上去）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Qt/qfluentwidgets 惰性导入：normalize_entries/read_value 必须在
# 无 GUI 的测试环境可用（headless 单测没有 PyQt5）。


def normalize_entries(manifest) -> List[Dict[str, Any]]:
    """manifest.config_defaults → 结构化设置项列表。"""
    defaults = dict(getattr(manifest, "config_defaults", None) or {})
    prefix = str(getattr(manifest, "config_prefix", "") or "")
    entries: List[Dict[str, Any]] = []
    for key, val in defaults.items():
        if not key:
            continue
        label = str(key)
        if prefix and label.startswith(prefix):
            label = label[len(prefix):]
        elif label.startswith("tool_"):
            label = label[5:]
        options: Optional[List[str]] = None
        default: Any = val
        vmin, vmax = 0, 9999
        restart = False
        if isinstance(val, dict):
            default = val.get("default", val.get("value"))
            label = str(val.get("label") or label)
            dtype = str(val.get("type", "")).lower()
            if dtype == "enum" or "options" in val:
                options = [str(o) for o in (val.get("options") or [])]
            elif dtype in ("bool", "int", "str"):
                default = val.get("default", {"bool": False, "int": 0, "str": ""}[dtype])
            restart = bool(val.get("restart") or val.get("needs_restart"))
            if dtype == "int":
                try: vmin = int(val.get("min", 0))
                except Exception: vmin = 0
                try: vmax = int(val.get("max", 9999))
                except Exception: vmax = 9999
        elif isinstance(val, list) and val and all(isinstance(x, str) for x in val):
            options = [str(x) for x in val]
            default = val[0]
        if options is not None:
            kind = "enum"
        elif isinstance(default, bool):
            kind = "bool"
        elif isinstance(default, int) and not isinstance(default, bool):
            kind = "int"
        else:
            kind = "str"
            default = "" if default is None else str(default)
        if restart:
            label += "（重启生效）"
        entries.append(
            {"key": str(key), "label": label, "kind": kind,
             "options": options, "default": default,
             "min": vmin, "max": vmax, "restart": restart}
        )
    return entries


def read_value(config, entry: Dict[str, Any]) -> Any:
    """读当前值：优先 config.config（内层 Config），退回 config 本身，再退默认。"""
    key = entry["key"]
    inner = getattr(config, "config", None)
    for holder in (inner, config):
        if holder is None:
            continue
        try:
            if hasattr(holder, key):
                return getattr(holder, key)
        except Exception:
            pass
    return entry["default"]


def build_panel(plugin, config, parent=None, on_change=None):
    """生成设置面板：每行 [显示名 | 控件]。on_change(key, value) 由宿主接落盘。"""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
    from qfluentwidgets import ComboBox, LineEdit, SpinBox, SwitchButton

    entries = normalize_entries(getattr(plugin, "manifest", None))
    host = QWidget(parent)
    lay = QVBoxLayout(host)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    for entry in entries:
        row = QFrame(host)
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)
        label = QLabel(entry["label"], row)
        rl.addWidget(label, 0, Qt.AlignVCenter)
        value = read_value(config, entry)
        if entry["kind"] == "bool":
            ctl = SwitchButton(row)
            try:
                ctl.setChecked(bool(value))
            except Exception:
                pass
            if on_change is not None:
                ctl.checkedChanged.connect(
                    lambda on, k=entry["key"]: on_change(k, bool(on))
                )
            rl.addStretch(1)
            rl.addWidget(ctl, 0, Qt.AlignVCenter)
        elif entry["kind"] == "int":
            ctl = SpinBox(row)
            ctl.setRange(int(entry.get("min", 0)), int(entry.get("max", 9999)))
            try:
                ctl.setValue(int(value))
            except Exception:
                ctl.setValue(0)
            if on_change is not None:
                ctl.valueChanged.connect(
                    lambda v, k=entry["key"]: on_change(k, int(v))
                )
            rl.addStretch(1)
            rl.addWidget(ctl, 0, Qt.AlignVCenter)
        elif entry["kind"] == "enum":
            ctl = ComboBox(row)
            ctl.addItems([str(o) for o in (entry["options"] or [])])
            try:
                idx = [str(o) for o in (entry["options"] or [])].index(str(value))
                ctl.setCurrentIndex(max(0, idx))
            except Exception:
                pass
            if on_change is not None:
                ctl.currentTextChanged.connect(
                    lambda t, k=entry["key"]: on_change(k, str(t))
                )
            rl.addStretch(1)
            rl.addWidget(ctl, 0, Qt.AlignVCenter)
        else:
            ctl = LineEdit(row)
            ctl.setText(str(value))
            ctl.setFixedWidth(180)
            if on_change is not None:
                ctl.editingFinished.connect(
                    lambda c=ctl, k=entry["key"]: on_change(k, str(c.text()))
                )
            rl.addStretch(1)
            rl.addWidget(ctl, 0, Qt.AlignVCenter)
        lay.addWidget(row)
    lay.addStretch(1)
    return host


def open_settings_dialog(plugin, config, parent=None) -> bool:
    """弹设置框（项目既有 MessageBoxBase 模式，不另造样式）。True=用户确认。"""
    try:
        from qfluentwidgets import MessageBoxBase, SubtitleLabel

        class _AutoSettingsBox(MessageBoxBase):
            def __init__(self, plugin_, config_, parent_):
                super().__init__(parent=parent_)
                self.setWindowTitle("插件设置")
                title = SubtitleLabel(str(getattr(plugin_, "name", "") or "插件设置"), self)
                self.viewLayout.addWidget(title)
                panel = build_panel(
                    plugin_, config_, self,
                    on_change=lambda k, v: _persist(config_, k, v),
                )
                self.viewLayout.addWidget(panel)
                self.yesButton.setText("完成")
                self.cancelButton.setText("取消")
                self.widget.setMinimumWidth(360)

        box = _AutoSettingsBox(plugin, config, parent)
        box.exec_()
        return True
    except Exception as e:
        print("[auto_settings] dialog failed:", e)
        return False


def _persist(config, key: str, value: Any) -> None:
    """与 tools._set_tool_cfg 同款写法：set + setattr + save。"""
    try:
        if hasattr(config, "set"):
            config.set(key, value)
    except Exception as e:
        print("[auto_settings] cfg set failed:", key, e)
    try:
        inner = getattr(config, "config", None)
        if inner is not None:
            try:
                setattr(inner, key, value)
            except Exception:
                try:
                    object.__setattr__(inner, key, value)
                except Exception:
                    pass
        if hasattr(config, "save"):
            config.save()
    except Exception as e:
        print("[auto_settings] cfg save failed:", key, e)
