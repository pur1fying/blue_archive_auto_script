# -*- coding: utf-8 -*-
"""通用任务闸门：调度队列的唯一官方拦截点。

宿主 core/scheduler.py 只需：

    from module.tools.gate import filter_events
    _valid_event = filter_events(_valid_event, config_dir)

无插件 / 插件全关 → 原样返回。
不修改任何业务 module 的 implement。

可靠性约定（审计修复）：
- 囤体过滤不依赖插件注册表是否加载成功：它自己读 config.json 开关，
  注册表挂掉时仍要尝试拦截。
- 拦截器自身故障必须高声告警（logger.warning），不能静默放行。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("baas.tools.gate")


def filter_events(
    events: List[Dict[str, Any]],
    config_dir: str,
    config: Any = None,
) -> List[Dict[str, Any]]:
    """汇总所有已加载工具的拦截规则，过滤调度事件列表。"""
    if not events:
        return events

    # config 降级：宿主未传时从 config_dir 读 config.json，
    # 否则 is_enabled 拿不到真值 → 插件拦截全部失效
    if config is None:
        try:
            import json as _json
            import os as _os

            cfg_path = _os.path.join(config_dir or ".", "config.json")
            if _os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    config = _json.load(f)
        except Exception:
            pass

    out = list(events)

    # 囤体过滤独立于注册表：scheduler_filter 自己读 config.json 开关。
    # 注册表加载失败（缺依赖/插件损坏）不能连带取消拦截。
    try:
        from module.hoard_ap.scheduler_filter import filter_events_for_hoard

        enabled = True
        try:
            from module.tools.registry import get_registry

            hoard = get_registry().get("hoard_ap")
            if hoard is not None and config is not None:
                enabled = bool(hoard.is_enabled(config))
        except Exception:
            enabled = True
        out = filter_events_for_hoard(out, config_dir, enabled)
    except Exception as e:
        # 拦截器自身故障：保持原队列，但必须被看见（调度线程没有界面可报）。
        logger.warning("hoard filter FAILED, events pass through unfiltered: %r", e)

    # 其它 scheduler 插件可实现 filter_events(events, config_dir, config)
    try:
        from module.tools.registry import get_registry

        reg = get_registry()
    except Exception as e:
        logger.warning("tools registry unavailable, plugin filters skipped: %r", e)
        reg = None
    if reg is not None:
        for tool in reg.list_tools():
            if getattr(tool, "id", None) == "hoard_ap":
                continue
            fn = getattr(tool, "filter_events", None)
            # 1) 自定义 filter_events 方法优先
            if callable(fn):
                try:
                    if not tool.is_enabled(config):
                        continue
                except Exception:
                    pass
                try:
                    nxt = fn(out, config_dir, config)
                    if isinstance(nxt, list):
                        out = nxt
                except Exception as e:
                    logger.warning(
                        "tool %s filter_events failed: %s", getattr(tool, "id", "?"), e
                    )
                continue
            # 2) 声明式 intercept_spec：用 funcs / always_allow 过滤
            try:
                spec = tool.get_intercept_spec()
            except Exception:
                spec = None
            if spec is None or not spec.funcs:
                continue
            try:
                if not tool.is_enabled(config):
                    continue
            except Exception:
                pass
            blocked = set(spec.funcs)
            allow = set(spec.always_allow)
            new_out = []
            for ev in out:
                name = ev.get("func_name") or ev.get("current_task") or ""
                if name in allow:
                    new_out.append(ev)
                elif name in blocked:
                    logger.debug(
                        "gate: tool %s blocked %s", getattr(tool, "id", "?"), name
                    )
                else:
                    new_out.append(ev)
            out = new_out
    return out


# 兼容旧 import 名
def filter_events_for_tools(
    events: List[Dict[str, Any]],
    config_dir: str,
    hoard_enabled: bool = True,
) -> List[Dict[str, Any]]:
    return filter_events(events, config_dir, config=None)
