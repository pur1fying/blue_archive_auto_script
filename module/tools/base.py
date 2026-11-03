# -*- coding: utf-8 -*-
"""工具插件基类与描述结构。

后人新增工具：复制 module/tools/_template/，改 manifest + 实现类即可。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class SchedulerSpec:
    """需要挂调度时的声明（local 工具不要填）。"""

    event_name: str
    func_name: str
    owns_funcs: bool = False
    priority: int = -3
    interval: int = 300
    daily_reset: Optional[list] = None


@dataclass
class InterceptSpec:
    """调度队列拦截声明（仅 kind=scheduler 有意义；local 禁止）。"""

    funcs: List[str] = field(default_factory=list)
    always_allow: List[str] = field(default_factory=list)
    # 可选：由插件自行实现 filter；有则优先
    custom: bool = False


@dataclass
class HomeContribution:
    """主页槽位贡献。"""

    slot: str = "below_title"  # 真实槽位仅 below_title | below_startup；其它值会告警并回退
    order: int = 100
    # 构建函数名提示；实际由 tool.build_home_widget 实现
    widget: str = "build_home_widget"


@dataclass
class ToolManifest:
    id: str
    name: str
    version: str = "1.0.0"
    summary: str = ""
    icon: str = "APPLICATION"
    category: str = "general"
    order: int = 100
    kind: str = "local"  # local | scheduler | home | device
    entry: str = ""
    ui: str = ""
    permissions: List[str] = field(default_factory=list)
    scheduler: Optional[Dict[str, Any]] = None
    intercept: Optional[Dict[str, Any]] = None
    home: Optional[Dict[str, Any]] = None
    config_prefix: str = ""
    config_defaults: Optional[Dict[str, Any]] = None
    enabled_by_default: bool = True
    show_in_lobby: bool = True
    home_hooks: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolManifest":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        payload = {k: v for k, v in (data or {}).items() if k in known}
        return cls(**payload)

    def scheduler_spec(self) -> Optional[SchedulerSpec]:
        if self.kind not in ("scheduler",) or not self.scheduler:
            return None
        s = self.scheduler
        return SchedulerSpec(
            event_name=str(s.get("event_name") or self.name),
            func_name=str(s.get("func_name") or self.id),
            owns_funcs=bool(s.get("owns_funcs")),
            priority=int(s.get("priority", -3)),
            interval=int(s.get("interval", 300)),
            daily_reset=s.get("daily_reset"),
        )

    def intercept_spec(self) -> Optional[InterceptSpec]:
        if self.kind == "local":
            return None
        raw = self.intercept
        if not raw:
            return None
        return InterceptSpec(
            funcs=list(raw.get("funcs") or []),
            always_allow=list(raw.get("always_allow") or []),
            custom=bool(raw.get("custom")),
        )

    def home_contribution(self) -> Optional[HomeContribution]:
        raw = self.home
        if not raw:
            return None
        return HomeContribution(
            slot=str(raw.get("slot") or "below_title"),
            order=int(raw.get("order", self.order)),
            widget=str(raw.get("widget") or "build_home_widget"),
        )


class ToolPlugin:
    """所有工具插件的统一接口。"""

    manifest: ToolManifest

    def __init__(self, manifest: ToolManifest):
        self.manifest = manifest
        # 注册配置默认（若 manifest 带了）
        try:
            from module.tools.config_registry import register_config_defaults

            if self.manifest.config_defaults:
                register_config_defaults(dict(self.manifest.config_defaults))
        except Exception as e:
            # 注册失败=插件配置键缺默认值，启动期一次性事件，留痕
            print(f"[tools] {manifest.id} 配置默认值注册失败: {e}")
        try:
            self.register_config()
        except Exception as e:
            print(f"[tools] {manifest.id} register_config 失败: {e}")

    def register_config(self) -> None:
        """子类可覆盖：register_config_defaults({...})。"""

    # ---- 元信息 ----
    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def name(self) -> str:
        # 工具大厅「编辑插件标签」覆盖（空=回清单名，不落盘到 manifest）
        ov = getattr(self, "_label_override", "")
        return str(ov) if ov else self.manifest.name

    @property
    def summary(self) -> str:
        return self.manifest.summary

    @property
    def kind(self) -> str:
        return self.manifest.kind

    @property
    def order(self) -> int:
        return self.manifest.order

    @property
    def icon_name(self) -> str:
        return self.manifest.icon or "APPLICATION"

    @property
    def permissions(self) -> Sequence[str]:
        return list(self.manifest.permissions or [])

    @property
    def config_prefix(self) -> str:
        return self.manifest.config_prefix or f"tool_{self.id}_"

    @property
    def show_in_lobby(self) -> bool:
        return bool(self.manifest.show_in_lobby)

    # ---- 生命周期 / UI ----
    def build_widget(self, parent=None, config=None):
        """返回工具页主控件（QWidget）。子类必须实现（lobby 展示时）。"""
        raise NotImplementedError(self.id)

    def build_home_widget(self, parent=None, config=None):
        """主页槽位控件。

        框架默认（共享方法，所有插件同一实现）：未声明 home 的插件
        自动发「进入××」按钮（PrimaryPushButton 蓝色，与囤体
        「进入囤体」同款，不另造样式）；点击经 open_requested 信号
        由主页接 open_tool 导航。声明了 home 的插件覆盖本方法返回
        自家板块；覆盖后返回 None 表示该插件此刻无主页贡献。
        """
        try:
            if self.get_home_contribution() is not None:
                return None
        except Exception:
            pass
        try:
            from qfluentwidgets import PrimaryPushButton

            name = (getattr(self.manifest, "name", "") or self.id or "")
            tid = str(self.id)
            btn = PrimaryPushButton("进入" + name[:4], parent)
            try:
                btn.setToolTip("打开工具里的%s页" % name)
            except Exception:
                pass
            btn.clicked.connect(
                lambda _checked=False, _w=btn, _tid=tid: _navigate_to_tool(
                    _w, _tid, config
                )
            )
            return btn
        except Exception as _e:
            print("[base] auto entry build failed: %r" % (_e,))
            return None

    def on_enable(self, config) -> None:
        """工具被打开时（可选）。"""

    def on_disable(self, config) -> None:
        """工具被关闭时（可选）。"""

    def validate_config(self, config) -> Optional[str]:
        """返回错误文案；None 表示通过。"""
        return None

    def get_scheduler_spec(self) -> Optional[SchedulerSpec]:
        return self.manifest.scheduler_spec()

    def get_intercept_spec(self) -> Optional[InterceptSpec]:
        return self.manifest.intercept_spec()

    def get_home_contribution(self) -> Optional[HomeContribution]:
        return self.manifest.home_contribution()

    def is_enabled(self, config) -> bool:
        """默认：scheduler 工具看 prefix_enabled / 专用键；local/home 恒为 True。"""
        if self.kind in ("local", "home"):
            return True
        key = f"{self.config_prefix}enabled" if self.config_prefix else None
        # 囤体历史键
        if self.id == "hoard_ap":
            return _cfg_bool(config, "hoard_ap_enabled", True)
        if not key:
            return True
        return _cfg_bool(config, key, self.manifest.enabled_by_default)

    def auto_settings_entries(self):
        """config_defaults 声明 → 结构化设置项（框架自动设置页用）。

        作者零 Qt：在 manifest.config_defaults 里声明 bool/int/str/枚举，
        工具大厅顶栏自动出现「插件设置」，点开即得开关/旋钮/输入框/下拉。
        """
        try:
            from module.tools.auto_settings import normalize_entries

            return normalize_entries(self.manifest)
        except Exception:
            return []

    def home_visible(self, config) -> bool:
        """主页入口是否显示。

        所有启用的插件默认 True：框架为未声明 home 的插件自动发一个
        主页入口卡（声明 home 的插件用自家板块）。是否真出现由
        registry.list_home_contributions 的框架级总开关
        （tool_<id>_home_visible）与插件自身覆盖逻辑共同决定。
        """
        return True


def _navigate_to_tool(widget, tool_id, config=None):
    """自动入口的点击导航：从任意子控件向上找窗口并打开工具页。

    与主页 open_tool 同款向上走法（hasattr open_tool_page），不依赖
    信号/子类——qfw 按钮子类化会触发其内部关键字转发问题。
    """
    try:
        w = widget
        while w is not None and not hasattr(w, "open_tool_page"):
            w = w.parentWidget()
        if w is not None and hasattr(w, "open_tool_page"):
            w.open_tool_page(tool_id, config=config)
            return True
    except Exception as e:
        print("[base] auto entry navigate failed:", e)
    return False


def _cfg_bool(config, key: str, default: bool = False) -> bool:
    try:
        if config is None:
            return default
        if hasattr(config, "get"):
            v = config.get(key, default)
        else:
            v = getattr(config, key, default)
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        s = str(v).strip().lower()
        if s in ("1", "true", "yes", "on", "是"):
            return True
        if s in ("0", "false", "no", "off", "否", ""):
            return False
        return bool(v)
    except Exception:
        return default


def _cfg_set(config, key: str, value) -> None:
    """写配置键：优先 config.set（带持久化），回退内层 config 属性，最后直接 setattr。"""
    try:
        if config is not None and hasattr(config, "set"):
            config.set(key, value)
            return
    except Exception as e:
        print("[tools] cfg set failed(config.set):", key, e)
    try:
        if config is None:
            return
        inner = getattr(config, "config", None)
        if inner is not None:
            setattr(inner, key, value)
        else:
            setattr(config, key, value)
    except Exception as e:
        print("[tools] cfg set failed(setattr):", key, e)


def resolve_dotted(path: str) -> Any:
    """'pkg.mod:Class' 或 'pkg.mod.Class' → 对象。"""
    if not path:
        raise ImportError("empty entry")
    if ":" in path:
        mod_name, attr = path.split(":", 1)
    else:
        parts = path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(f"bad entry: {path}")
        mod_name, attr = parts
    import importlib

    mod = importlib.import_module(mod_name)
    obj = mod
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj
