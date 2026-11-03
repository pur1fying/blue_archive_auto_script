"""Scheduler 冲突过滤：囤体启用且活跃时，接管相关日常。

用法（打进 core/scheduler.py 的 update_valid_task_queue）：

    from module.hoard_ap.scheduler_filter import filter_events_for_hoard
    _valid_event = filter_events_for_hoard(_valid_event, config_dir)

规则（按用户意见）：
1. 只要囤体开关开着，且运行相位处于活跃（Armed…SpendReady），
   HOARD_OWNED_FUNCS 里的调度任务一律不进队列——由囤体计划在规定时间点执行。
2. hoard_ap 本身永远放行。
3. Idle/Done/Aborted 或未启用：不压制。
4. cafe_reward 整包在队列层被压；若其它路径直接调 implement，
   再用 should_skip_cafe_collect / should_skip_task 二次兜底。
"""

from __future__ import annotations

from typing import Any, Dict, List

from module.hoard_ap.constants import (
    HOARD_OWNED_FUNCS,
    HOARD_SPEND_BLOCK_FUNCS,
    PHASE_ABORTED,
    PHASE_SPEND_READY,
    PHASE_DONE,
    PREFER_CLEAR_ALLOW,
    PREFER_CLEAR_HIGH_VALUE,
    PREFER_CLEAR_MAINLINE,
    PREFER_CLEAR_NONE,
)
import os
import threading
from module.hoard_ap.state import is_active_phase, load_state


# 囤体任务本身永远放行；凌晨四点重启也永远放行
HOARD_FUNC = "hoard_ap"
ALWAYS_ALLOW_FUNCS = frozenset({"hoard_ap", "restart"})


def _read_config_json(config_dir: str) -> dict:
    import json

    cfg_path = os.path.join(config_dir or ".", "config.json")
    if not os.path.isfile(cfg_path):
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _hoard_enabled_from_config(config_dir: str, fallback: bool = True) -> bool:
    data = _read_config_json(config_dir)
    if not data:
        return fallback
    return bool(data.get("hoard_ap_enabled", fallback))


def _prefer_clear_mode(config_dir: str) -> str:
    data = _read_config_json(config_dir)
    v = str(data.get("hoard_ap_prefer_clear") or "").strip().lower()
    # 旧 mainline 保持兼容（放行普通+困难）
    if v == "mainline":
        return PREFER_CLEAR_MAINLINE
    if v in PREFER_CLEAR_ALLOW:
        return v
    return PREFER_CLEAR_NONE


def _high_value_is_manual(config_dir: str) -> bool:
    """高价值活动：活动开启时间若明显晚于 04:00（如 18:30），视为维护后手动推，拦自动活动扫荡。"""
    data = _read_config_json(config_dir)
    # 常见字段：活动开始/推图时间 HH:MM 或 HHmm
    candidates = [
        data.get("hoard_ap_high_value_time"),
        data.get("activity_sweep_start_time"),
        data.get("activity_open_time"),
        data.get("event_start_time"),
    ]
    for raw in candidates:
        if raw is None or str(raw).strip() == "":
            continue
        s = str(raw).strip().replace("：", ":")
        hh = mm = None
        try:
            if ":" in s:
                parts = s.split(":")
                hh, mm = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            elif s.isdigit() and len(s) in (3, 4):
                s = s.zfill(4)
                hh, mm = int(s[:2]), int(s[2:])
        except Exception:
            continue
        if hh is None:
            continue
        # 04:00 之后较远（≥6 点）→ 手动；凌晨活动仍可自动
        minutes = hh * 60 + int(mm or 0)
        if minutes >= 6 * 60:
            return True
    return False


def filter_events_for_hoard(
    events: List[Dict[str, Any]],
    config_dir: str,
    hoard_enabled: bool = True,
) -> List[Dict[str, Any]]:
    """从即将执行的事件列表里剔除囤体接管项 / 优先清体拦截项。

    - 囤体关闭：不按相位压日常（立刻释放调度）
    - 主页「优先清体」三选一：即使未开囤体也拦截其它耗体扫荡
    """
    if not events:
        return events

    cfg_on = bool(hoard_enabled) and _hoard_enabled_from_config(
        config_dir, fallback=bool(hoard_enabled)
    )
    prefer = _prefer_clear_mode(config_dir)
    prefer_allow = set(PREFER_CLEAR_ALLOW.get(prefer) or ())
    high_manual = bool(
        prefer == PREFER_CLEAR_HIGH_VALUE and _high_value_is_manual(config_dir)
    )

    state = None
    phase = ""
    try:
        state = load_state(config_dir)
        phase = str(getattr(state, "phase", "") or "")
    except Exception:
        state = None
        phase = ""

    # 囤体活跃压制（开关开 + 活跃相位；状态损坏 Aborted 时对 owned 也收紧拦截）
    hoard_active = bool(cfg_on and (is_active_phase(phase) or phase == PHASE_ABORTED))
    spend_guard = bool(
        cfg_on
        and phase in (PHASE_SPEND_READY, PHASE_DONE)
        and bool(getattr(state, "plan", None) if state is not None else None)
    )

    # 无囤体活跃、也无优先清体 → 原样放行
    if not hoard_active and not prefer and not spend_guard:
        return events

    out: List[Dict[str, Any]] = []
    blocked: List[str] = []
    for ev in events:
        name = ev.get("func_name") or ev.get("current_task") or ""
        if name in ALWAYS_ALLOW_FUNCS:
            out.append(ev)
            continue
        # 优先清体：拦其它耗体（高价值+晚开 → 连 activity_sweep 也拦，改手动）
        if prefer and name in HOARD_SPEND_BLOCK_FUNCS:
            if high_manual:
                blocked.append(str(name))
                continue
            if name not in prefer_allow:
                blocked.append(str(name))
                continue
        if hoard_active and name in HOARD_OWNED_FUNCS:
            # 优先清体放行的扫荡，即使在囤体 OWNED 里，也允许调度自己跑（用户显式点了主页开关）
            if prefer and name in prefer_allow and not high_manual:
                out.append(ev)
                continue
            blocked.append(str(name))
            continue
        if spend_guard and name in HOARD_SPEND_BLOCK_FUNCS:
            if prefer and name in prefer_allow and not high_manual:
                out.append(ev)
                continue
            blocked.append(str(name))
            continue
        out.append(ev)
    # 不在这里打 logger（scheduler 无 self.logger）；执行器启动时会再记一笔
    if blocked:
        try:
            # 可选：写一行 state notes，方便 UI/排障
            if blocked and state is not None:
                note = "blocked:" + ",".join(sorted(set(blocked)))
                if not state.notes or state.notes[-1] != note:
                    state.notes = (state.notes or [])[-20:] + [note]
                    from module.hoard_ap.state import save_state

                    save_state(config_dir, state)
        except Exception:
            pass
    return out


# 囤体 executor 内部调用扫荡/商店时置位，避免「相位保护」把自己掐死。
# 三层隔离（无全局变量，防跨账号串扰）：
#   1) thread-local depth（同线程内套娃）
#   2) baas._hoard_ap_internal（同账号实例）
#   3) 磁盘旗标文件（子模块只看 should_skip 时也能放行）
_tls = threading.local()
_FLAG_NAME = "hoard_ap_internal.flag"


def _flag_paths(baas=None) -> list:
    dirs = []
    if baas is not None:
        for attr in ("config_path",):
            try:
                d = getattr(baas, attr, None)
                if d:
                    dirs.append(str(d))
            except Exception:
                pass
        try:
            cs = getattr(baas, "config_set", None)
            d = getattr(cs, "config_dir", None) if cs is not None else None
            if d:
                dirs.append(str(d))
        except Exception:
            pass
    try:
        d = getattr(_tls, "config_dir", None)
        if d:
            dirs.append(str(d))
    except Exception:
        pass
    # 去重
    out, seen = [], set()
    for d in dirs:
        if d and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _write_flag(baas=None) -> None:
    for d in _flag_paths(baas):
        try:
            p = os.path.join(d, _FLAG_NAME)
            with open(p, "w", encoding="utf-8") as f:
                f.write("1")
        except Exception:
            pass


def _clear_flag(baas=None) -> None:
    for d in _flag_paths(baas):
        try:
            p = os.path.join(d, _FLAG_NAME)
            if os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass


def _flag_on(config_dir: str = "", baas=None) -> bool:
    cands = []
    if config_dir:
        cands.append(config_dir)
    cands.extend(_flag_paths(baas))
    for d in cands:
        try:
            if d and os.path.isfile(os.path.join(str(d), _FLAG_NAME)):
                return True
        except Exception:
            pass
    return False


def begin_hoard_internal(baas=None, config_dir: str = "") -> None:
    _tls.depth = int(getattr(_tls, "depth", 0) or 0) + 1
    if config_dir:
        _tls.config_dir = config_dir
    if baas is not None:
        try:
            baas._hoard_ap_internal = int(getattr(baas, "_hoard_ap_internal", 0) or 0) + 1
        except Exception:
            pass
        if not config_dir:
            try:
                cd = getattr(baas, "config_path", None) or getattr(
                    getattr(baas, "config_set", None), "config_dir", ""
                )
                if cd:
                    _tls.config_dir = cd
            except Exception:
                pass
    _write_flag(baas)


def end_hoard_internal(baas=None) -> None:
    _tls.depth = max(0, int(getattr(_tls, "depth", 0) or 0) - 1)
    if baas is not None:
        try:
            baas._hoard_ap_internal = max(
                0, int(getattr(baas, "_hoard_ap_internal", 0) or 0) - 1
            )
        except Exception:
            pass
    if int(getattr(_tls, "depth", 0) or 0) <= 0:
        _clear_flag(baas)
        try:
            if baas is not None:
                baas._hoard_ap_internal = 0
        except Exception:
            pass


def is_hoard_internal(baas=None, config_dir: str = "") -> bool:
    if int(getattr(_tls, "depth", 0) or 0) > 0:
        return True
    if baas is not None:
        try:
            if int(getattr(baas, "_hoard_ap_internal", 0) or 0) > 0:
                return True
        except Exception:
            pass
    if _flag_on(config_dir or "", baas):
        return True
    return False


def should_skip_task(func_name: str, config_dir: str, baas=None) -> bool:
    """模块入口二次校验：是否跳过该 func。

    - restart 永远不跳过
    - 囤体内部调用放行
    - 囤体关闭：不按相位拦（释放调度）
    - 主页优先清体：拦其它耗体扫荡（可单独生效）
    """
    if not func_name or func_name in ALWAYS_ALLOW_FUNCS:
        return False
    if is_hoard_internal(baas, config_dir or ""):
        return False

    prefer = _prefer_clear_mode(config_dir)
    prefer_allow = set(PREFER_CLEAR_ALLOW.get(prefer) or ())
    high_manual = bool(
        prefer == PREFER_CLEAR_HIGH_VALUE and _high_value_is_manual(config_dir)
    )
    if prefer and func_name in HOARD_SPEND_BLOCK_FUNCS:
        if high_manual:
            return True
        if func_name not in prefer_allow:
            return True

    cfg_on = _hoard_enabled_from_config(config_dir, fallback=False)
    if not cfg_on:
        return False
    try:
        phase = load_state(config_dir).phase
    except Exception:
        return False
    owned = set(HOARD_OWNED_FUNCS) | {
        "cafe_reward_claim",
        "cafe_collect",
        "tactical_challenge_shop",
    }
    if (is_active_phase(phase) or phase == PHASE_ABORTED) and func_name in owned:
        if prefer and func_name in prefer_allow and not high_manual:
            return False
        return True
    if phase in (PHASE_SPEND_READY, PHASE_DONE) and func_name in HOARD_SPEND_BLOCK_FUNCS:
        if prefer and func_name in prefer_allow and not high_manual:
            return False
        return True
    return False


def should_skip_cafe_collect(config_dir: str) -> bool:
    """咖啡厅小时奖励：囤体启用且活跃时禁止 cafe_reward 内部 collect。

    不走 HOARD_OWNED_FUNCS（否则会连邀请/摸头整包踢出队列）。
    """
    if not _hoard_enabled_from_config(config_dir, fallback=False):
        return False
    try:
        phase = load_state(config_dir).phase
    except Exception:
        return False
    return is_active_phase(phase)


def list_owned_funcs() -> List[str]:
    return sorted(HOARD_OWNED_FUNCS)
