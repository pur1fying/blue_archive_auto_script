# -*- coding: utf-8 -*-
"""声明式调度接线：从 manifest.scheduler 自动生成 event.json 条目。

插件在 manifest.json 声明 ``scheduler`` 字段后，本模块把声明转成
event.json 的事件条目——不再需要硬编码 event_snippet.json 逐插件手写。

设计：
- 只补缺失条目（func_name 不在 event.json 中的才注入），不覆盖用户手动编辑。
- 启用的插件 → enabled=True；未启用的 → enabled=False。
- 调用时机：Baas_thread 启动时 / 安装脚本安装后。

可靠性：
- 注册表加载失败 → 静默返回 0（不阻塞调度）。
- event.json 损坏 → 按 [] 处理（只补不覆盖）。
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger("baas.tools.scheduler_wire")


def _spec_to_event_entry(spec) -> Dict[str, Any]:
    """SchedulerSpec → event.json 条目结构（与 event_snippet.json 对齐）。"""
    return {
        "enabled": False,
        "priority": int(spec.priority),
        "interval": int(spec.interval),
        "daily_reset": list(spec.daily_reset or []),
        "next_tick": 0,
        "event_name": str(spec.event_name),
        "func_name": str(spec.func_name),
        "disabled_time_range": [],
        "pre_task": [],
        "post_task": [],
    }


def wire_events(config_dir: str, config: Any = None) -> int:
    """把所有 scheduler 类插件的 manifest.scheduler 声明合并进 event.json。

    返回新增的事件条目数。已存在的同名事件不覆盖（用户手动编辑优先）。
    """
    if not config_dir:
        return 0

    event_path = os.path.join(config_dir, "event.json")
    events: List[Dict[str, Any]] = []
    if os.path.isfile(event_path):
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            events = loaded if isinstance(loaded, list) else []
        except Exception:
            events = []

    try:
        from module.tools.registry import get_registry

        reg = get_registry()
    except Exception as e:
        logger.warning("scheduler_wire: registry unavailable: %s", e)
        return 0

    existing_funcs = {
        str(ev.get("func_name") or "")
        for ev in events
        if isinstance(ev, dict)
    }
    added = 0
    for tool in reg.list_tools():
        try:
            spec = tool.get_scheduler_spec()
        except Exception:
            spec = None
        if spec is None:
            continue
        # 已存在的不覆盖（用户编辑优先）
        if spec.func_name in existing_funcs:
            continue
        entry = _spec_to_event_entry(spec)
        try:
            if tool.is_enabled(config):
                entry["enabled"] = True
        except Exception:
            pass
        events.append(entry)
        existing_funcs.add(spec.func_name)
        added += 1
        logger.info(
            "scheduler_wire: wired %s -> event %s", tool.id, spec.func_name
        )

    if added > 0:
        try:
            tmp = event_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            os.replace(tmp, event_path)
        except Exception as e:
            logger.warning("scheduler_wire: write event.json failed: %s", e)
    return added
