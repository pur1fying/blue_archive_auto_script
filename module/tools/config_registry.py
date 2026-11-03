# -*- coding: utf-8 -*-
"""插件配置字段注册：不改上游 DEFAULT_CONFIG / Config dataclass。

宿主 ConfigSet 在 load/save 时：
- load：把已注册键的默认值补进 raw json；非 Config 字段用 setattr 挂到 config 实例
- save：asdict(config) 后再并入已注册的插件键，写回 config.json

插件在 import / registry.load_all 时调用 register_config_defaults。
"""
from __future__ import annotations

from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {}


def register_config_defaults(defaults: Dict[str, Any]) -> None:
    """合并插件默认字段（后注册不覆盖先注册的同名键，除非显式 force）。"""
    if not defaults:
        return
    for k, v in defaults.items():
        if not k:
            continue
        if k not in _DEFAULTS:
            _DEFAULTS[k] = v


def register_config_defaults_force(defaults: Dict[str, Any]) -> None:
    if not defaults:
        return
    _DEFAULTS.update({k: v for k, v in defaults.items() if k})


def registered_defaults() -> Dict[str, Any]:
    return dict(_DEFAULTS)


def registered_keys() -> frozenset:
    return frozenset(_DEFAULTS.keys())


def merge_plugin_defaults(raw: Dict[str, Any]) -> Dict[str, Any]:
    """返回新 dict：缺的插件键用默认补齐；已有用户值保留。"""
    out = dict(raw or {})
    for k, v in _DEFAULTS.items():
        if k not in out:
            out[k] = v
    return out


def collect_plugin_values(config_obj: Any) -> Dict[str, Any]:
    """从 config 实例上收集已注册插件键的当前值。

    没有挂上的键也写出默认，避免 save 丢键、下次 merge 又回到默认开。
    """
    out: Dict[str, Any] = {}
    if config_obj is None:
        return out
    for k, default in _DEFAULTS.items():
        try:
            if hasattr(config_obj, k):
                out[k] = getattr(config_obj, k)
            else:
                out[k] = default
        except Exception:
            out[k] = default
    return out


def apply_extras_to_config(config_obj: Any, raw: Dict[str, Any], known_fields: set) -> None:
    """把非 dataclass 字段 setattr 到 config 实例，供 getattr/get 使用。"""
    if config_obj is None:
        return
    for k, v in (raw or {}).items():
        if k in known_fields:
            continue
        try:
            setattr(config_obj, k, v)
        except Exception:
            pass
    # 确保注册过的键至少有默认
    for k, v in _DEFAULTS.items():
        if k in known_fields:
            continue
        if not hasattr(config_obj, k):
            try:
                setattr(config_obj, k, v)
            except Exception:
                pass
