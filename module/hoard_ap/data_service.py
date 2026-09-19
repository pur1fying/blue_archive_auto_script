"""统一数据访问服务。

职责边界（事实来源）：
- InventoryService    : 当前体力 / 邮箱 / 咖啡 / 已领标记（唯一读写入口）
- StateService        : 相位、计划缓存、执行游标
- ExecutionLogService : 只追加的完成记录
- UserConfig 动态字段 : 仍可镜像写一份兼容旧 GUI，但读优先 inventory

其它模块应优先通过本文件访问三份 json，避免直接 load/save 散落。
底层 load_inventory / load_state / append_exec 仍保留，供测试与渐进迁移。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from module.hoard_ap.execution_log import (
    ExecEntry,
    append_exec,
    done_actions,
    format_log_section,
    load_log,
)
from module.hoard_ap.inventory import InventorySnapshot, load_inventory, save_inventory
from module.hoard_ap.state import HoardRuntimeState, load_state, save_state


def config_dir_of(obj: Any) -> str:
    """从 BAAS 线程 / config 对象推测 config 目录。"""
    if obj is None:
        return "."
    for attr in ("config_path", "config_dir"):
        v = getattr(obj, attr, None)
        if v:
            return str(v)
    try:
        cs = getattr(obj, "config_set", None)
        if cs is not None:
            for attr in ("config_dir", "config_path"):
                v = getattr(cs, attr, None)
                if v:
                    return str(v)
    except Exception:
        pass
    try:
        cfg = getattr(obj, "config", None)
        if cfg is not None:
            for attr in ("config_dir", "config_path"):
                v = getattr(cfg, attr, None)
                if v:
                    return str(v)
    except Exception:
        pass
    return "."


def _mirror_config(cfg: Any, key: str, value: Any) -> None:
    """兼容旧字段：镜像写到 config（不作为事实来源）。"""
    if cfg is None:
        return
    try:
        if hasattr(cfg, "set"):
            cfg.set(key, value)
            return
        setattr(cfg, key, value)
        inner = getattr(cfg, "config", None)
        if inner is not None and inner is not cfg:
            try:
                setattr(inner, key, value)
            except Exception:
                pass
        if hasattr(cfg, "save"):
            try:
                cfg.save()
            except Exception:
                pass
    except Exception:
        pass


class InventoryService:
    """当前数值与已领标记的唯一读写入口。"""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir or "."

    def load(self) -> InventorySnapshot:
        return load_inventory(self.config_dir)

    def save(self, snap: InventorySnapshot) -> None:
        save_inventory(self.config_dir, snap)

    def update(self, **kwargs: Any) -> InventorySnapshot:
        snap = self.load()
        for k, v in kwargs.items():
            if hasattr(snap, k):
                setattr(snap, k, v)
        self.save(snap)
        return snap

    def set_current_ap(self, value: int, *, cfg: Any = None) -> None:
        ap = int(value)
        now_s = datetime.now().replace(second=0, microsecond=0).isoformat(
            sep=" ", timespec="seconds"
        )
        self.update(current_ap=ap, snapped_at=now_s)
        if cfg is not None:
            _mirror_config(cfg, "hoard_ap_current_ap", str(ap))

    def set_claimed(
        self,
        *,
        task: Optional[bool] = None,
        lesson: Optional[bool] = None,
        jjc: Optional[bool] = None,
        group: Optional[bool] = None,
        free_buy: Optional[bool] = None,
        cfg: Any = None,
    ) -> InventorySnapshot:
        kw: Dict[str, Any] = {}
        if task is not None:
            kw["task_claimed"] = bool(task)
        if lesson is not None:
            kw["lesson_claimed"] = bool(lesson)
        if jjc is not None:
            kw["jjc_claimed"] = bool(jjc)
        if group is not None:
            kw["group_claimed"] = bool(group)
        if free_buy is not None:
            kw["free_buy_claimed"] = bool(free_buy)
        snap = self.update(**kw) if kw else self.load()
        if cfg is not None:
            try:
                _mirror_config(cfg, "hoard_ap_claimed_day_start", datetime.now().strftime("%Y-%m-%d"))
            except Exception:
                pass
            if task is not None:
                _mirror_config(cfg, "hoard_ap_task_claimed", bool(task))
            if lesson is not None:
                _mirror_config(cfg, "hoard_ap_lesson_claimed", bool(lesson))
                if lesson:
                    _mirror_config(cfg, "hoard_ap_lesson_ready", False)
            if jjc is not None:
                _mirror_config(cfg, "hoard_ap_jjc_claimed", bool(jjc))
            if group is not None:
                _mirror_config(cfg, "hoard_ap_group_claimed", bool(group))
            if free_buy is not None:
                _mirror_config(cfg, "hoard_ap_free_buy_claimed", bool(free_buy))
        return snap

    def set_mail(
        self,
        *,
        mail_ap: Optional[int] = None,
        mail_bags: Optional[List[Dict[str, Any]]] = None,
        cfg: Any = None,
        also_after_cafe: bool = False,
    ) -> InventorySnapshot:
        kw: Dict[str, Any] = {}
        if mail_ap is not None:
            kw["mail_ap"] = int(mail_ap)
        if mail_bags is not None:
            kw["mail_bags"] = list(mail_bags)
            kw["mail_scanned_at"] = datetime.now().replace(
                second=0, microsecond=0
            ).isoformat(sep=" ", timespec="seconds")
        snap = self.update(**kw) if kw else self.load()
        if cfg is not None and mail_ap is not None:
            _mirror_config(cfg, "hoard_ap_mail_ap", str(int(mail_ap)))
            if also_after_cafe:
                _mirror_config(cfg, "hoard_ap_mail_after_cafe", str(int(mail_ap)))
            if mail_bags is not None:
                try:
                    import json

                    _mirror_config(
                        cfg,
                        "hoard_ap_mail_bags_json",
                        json.dumps(mail_bags, ensure_ascii=False),
                    )
                except Exception:
                    pass
        return snap


class StateService:
    """运行相位与计划缓存。"""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir or "."

    def load(self) -> HoardRuntimeState:
        return load_state(self.config_dir)

    def save(self, state: HoardRuntimeState) -> None:
        save_state(self.config_dir, state)

    def set_plan(self, plan: Dict[str, Any], *, step_index: Optional[int] = None) -> HoardRuntimeState:
        st = self.load()
        st.plan = plan
        if step_index is not None:
            st.step_index = int(step_index)
        st.updated_at = datetime.now().timestamp()
        self.save(st)
        return st

    def mark_replanned(self, state: Optional[HoardRuntimeState] = None, when: Optional[datetime] = None) -> HoardRuntimeState:
        """写入 replanned_at，供 GUI / 时间轴插入「更新计划」。"""
        st = state if state is not None else self.load()
        when = when or datetime.now()
        stamp = when.strftime("%Y-%m-%d %H:%M:%S")
        plan = dict(st.plan or {})
        plan["replanned_at"] = stamp
        sm = dict(plan.get("summary") or {})
        sm["replan_at"] = stamp
        sm["replanned_at"] = stamp
        plan["summary"] = sm
        st.plan = plan
        st.updated_at = when.timestamp()
        self.save(st)
        return st


class ExecutionLogService:
    """执行账本：只追加。"""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir or "."

    def load(self) -> List[ExecEntry]:
        return load_log(self.config_dir)

    def append(
        self,
        action: str,
        note: str = "",
        ok: bool = True,
        step_index: int = -1,
        meta: Optional[Dict[str, Any]] = None,
        when: Optional[datetime] = None,
    ) -> None:
        append_exec(
            self.config_dir,
            action=action,
            note=note,
            ok=ok,
            step_index=step_index,
            meta=meta,
            when=when,
        )

    def done_actions(self) -> List[str]:
        return done_actions(self.config_dir)

    def format_recent(self, limit: int = 12) -> str:
        return format_log_section(self.config_dir, limit=limit)


class HoardDataService:
    """聚合三个服务，方便注入。"""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir or "."
        self.inventory = InventoryService(self.config_dir)
        self.state = StateService(self.config_dir)
        self.log = ExecutionLogService(self.config_dir)

    @classmethod
    def from_baas(cls, baas: Any) -> "HoardDataService":
        return cls(config_dir_of(baas))
