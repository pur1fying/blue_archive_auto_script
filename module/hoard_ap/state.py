"""囤体运行时状态：相位、计划缓存、邮箱台账、冲突判断。

状态落在 config 目录 `hoard_ap_state.json`，避免污染主 config dataclass 的高频写。
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# 损坏文件每进程只报一次，防止调度每 tick 刷屏
_CORRUPT_WARNED = set()

from module.hoard_ap.constants import (
    CONFLICT_TABLE,
    HOARD_ACTIVE_PHASES,
    HOARD_OWNED_FUNCS,
    PHASE_ABORTED,
    PHASE_ARMED,
    PHASE_CLEAR,
    PHASE_DONE,
    PHASE_HOLD,
    PHASE_IDLE,
    PHASE_PRE_OVERFLOW,
    PHASE_SPEND_READY,
    PHASE_STACK,
)


STATE_FILENAME = "hoard_ap_state.json"


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _fmt_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat(sep=" ", timespec="seconds")


@dataclass
class MailLedgerEntry:
    amount: int
    overflow_at: str  # iso
    expire_at: str
    source: str = ""
    claimed: bool = False
    remain_hours: float = -1.0  # OCR 写入时用；-1 表示未知

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MailLedgerEntry":
        return cls(
            amount=int(data.get("amount") or 0),
            overflow_at=str(data.get("overflow_at") or ""),
            expire_at=str(data.get("expire_at") or ""),
            source=str(data.get("source") or ""),
            claimed=bool(data.get("claimed") or False),
            remain_hours=float(data.get("remain_hours") if data.get("remain_hours") is not None else -1),
        )


@dataclass
class HoardRuntimeState:
    phase: str = PHASE_IDLE
    plan: Optional[Dict[str, Any]] = None
    step_index: int = 0
    mail_ledger: List[MailLedgerEntry] = field(default_factory=list)
    last_error: str = ""
    updated_at: float = 0.0
    armed_at: str = ""
    notes: List[str] = field(default_factory=list)
    # 任务页「每日」tab 校准坐标（用户点一次后记住）
    task_daily_tab_xy: Optional[List[int]] = None
    strategy_mode: str = ""  # lazy / diligent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "plan": self.plan,
            "step_index": self.step_index,
            "mail_ledger": [m.to_dict() for m in self.mail_ledger],
            "last_error": self.last_error,
            "updated_at": self.updated_at,
            "armed_at": self.armed_at,
            "notes": list(self.notes),
            "task_daily_tab_xy": list(self.task_daily_tab_xy) if self.task_daily_tab_xy else None,
            "strategy_mode": self.strategy_mode or "",
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoardRuntimeState":
        data = data or {}
        ledger = [
            MailLedgerEntry.from_dict(x)
            for x in (data.get("mail_ledger") or [])
            if isinstance(x, dict)
        ]
        xy = data.get("task_daily_tab_xy")
        if isinstance(xy, (list, tuple)) and len(xy) >= 2:
            xy_out = [int(xy[0]), int(xy[1])]
        else:
            xy_out = None
        return cls(
            phase=str(data.get("phase") or PHASE_IDLE),
            plan=data.get("plan"),
            step_index=int(data.get("step_index") or 0),
            mail_ledger=ledger,
            last_error=str(data.get("last_error") or ""),
            updated_at=float(data.get("updated_at") or 0),
            armed_at=str(data.get("armed_at") or ""),
            notes=list(data.get("notes") or []),
            task_daily_tab_xy=xy_out,
            strategy_mode=str(data.get("strategy_mode") or ""),
        )


def state_path_from_config_dir(config_dir: str) -> str:
    return os.path.join(config_dir, STATE_FILENAME)


def load_state(config_dir: str) -> HoardRuntimeState:
    path = state_path_from_config_dir(config_dir)
    if not os.path.exists(path):
        return HoardRuntimeState()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return HoardRuntimeState.from_dict(json.load(f))
    except Exception as e:
        # 状态损坏：绝不能按空状态(Idle)静默重跑——否则会重复执行已做的动作。
        # 返回 Aborted 相位：执行器拒绝执行、闸门对 owned func 收紧拦截，
        # 需人工介入或等下一轮自动重规划。
        if path not in _CORRUPT_WARNED:
            _CORRUPT_WARNED.add(path)
            print(f"[hoard_ap] 运行状态文件损坏，标记中止需人工介入: {path} ({e})")
        st = HoardRuntimeState()
        st.phase = PHASE_ABORTED
        st.last_error = f"状态文件损坏: {e}"
        return st


def save_state(config_dir: str, state: HoardRuntimeState) -> None:
    state.updated_at = time.time()
    path = state_path_from_config_dir(config_dir)
    os.makedirs(config_dir, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def is_active_phase(phase: str) -> bool:
    return phase in HOARD_ACTIVE_PHASES


def conflicts_with_hoard(func_name: str, phase: str) -> bool:
    """日常 func_name 在当前相位是否应被压制。"""
    if not is_active_phase(phase):
        return False
    if func_name in HOARD_OWNED_FUNCS:
        return True
    blocked: Set[str] = CONFLICT_TABLE.get(func_name, set())
    return phase in blocked


def phase_from_step_action(action: str) -> str:
    mapping = {
        "buy_tubes": PHASE_STACK,
        "free_buy": PHASE_STACK,
        "claim_task": PHASE_STACK,
        "claim_task_daily_only": PHASE_STACK,
        "claim_group": PHASE_STACK,
        "claim_jjc": PHASE_STACK,
        "claim_cafe": PHASE_STACK,
        "use_ap_card": PHASE_STACK,
        "ensure_headroom": PHASE_CLEAR,
        "clear_ap": PHASE_CLEAR,
        "hold": PHASE_HOLD,
        "spend_ready": PHASE_SPEND_READY,
        "notify": PHASE_ARMED,
        "wait": PHASE_ARMED,
        "record_overflow": PHASE_PRE_OVERFLOW,
        "claim_mail": PHASE_STACK,
    }
    return mapping.get(action, PHASE_ARMED)


def append_mail_ledger(
    state: HoardRuntimeState,
    amount: int,
    overflow_at: datetime,
    expire_at: datetime,
    source: str = "",
    remain_hours: float = -1.0,
) -> None:
    state.mail_ledger.append(
        MailLedgerEntry(
            amount=int(amount),
            overflow_at=_fmt_dt(overflow_at) or "",
            expire_at=_fmt_dt(expire_at) or "",
            source=source,
            claimed=False,
            remain_hours=float(remain_hours),
        )
    )


def pending_mail_total(state: HoardRuntimeState) -> int:
    return sum(m.amount for m in state.mail_ledger if not m.claimed)


def earliest_mail_deadline(state: HoardRuntimeState) -> Optional[datetime]:
    times = []
    for m in state.mail_ledger:
        if m.claimed:
            continue
        dt = _parse_dt(m.expire_at)
        if dt:
            times.append(dt)
    return min(times) if times else None


def replace_mail_ledger_from_scan(
    state: HoardRuntimeState,
    bags: List[Dict[str, Any]],
    now: Optional[datetime] = None,
) -> None:
    """用 OCR 扫到的邮箱限时体力包覆盖未领取台账。"""
    now = now or datetime.now()
    kept = [m for m in state.mail_ledger if m.claimed]
    for b in bags:
        amount = int(b.get("amount") or 0)
        if amount <= 0:
            continue
        remain_h = float(b.get("remain_hours") if b.get("remain_hours") is not None else -1)
        if remain_h < 0:
            remain_h = 24.0
        from datetime import timedelta

        expire = now + timedelta(hours=remain_h)
        kept.append(
            MailLedgerEntry(
                amount=amount,
                overflow_at=_fmt_dt(now) or "",
                expire_at=_fmt_dt(expire) or "",
                source=str(b.get("source") or "ocr"),
                claimed=False,
                remain_hours=remain_h,
            )
        )
    state.mail_ledger = kept
