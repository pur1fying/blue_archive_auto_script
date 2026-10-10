"""执行账本：记录实际何时做了哪步，供迟到重算与说明展示。"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# 损坏文件每进程只报一次，防止调度每 tick 刷屏
_CORRUPT_WARNED = set()

LOG_FILENAME = "hoard_ap_execution_log.json"

# 近况不展示的纯说明类
_LOG_SKIP_ACTIONS = frozenset({"notify", "wait", "hold"})


@dataclass
class ExecEntry:
    when: str
    action: str
    note: str = ""
    ok: bool = True
    step_index: int = -1
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecEntry":
        d = d or {}
        return cls(
            when=str(d.get("when") or ""),
            action=str(d.get("action") or ""),
            note=str(d.get("note") or ""),
            ok=bool(d.get("ok", True)),
            step_index=int(d.get("step_index") if d.get("step_index") is not None else -1),
            meta=dict(d.get("meta") or {}),
        )


def log_path(config_dir: str) -> str:
    return os.path.join(config_dir or ".", LOG_FILENAME)


def load_log(config_dir: str) -> List[ExecEntry]:
    path = log_path(config_dir)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("entries") if isinstance(data, dict) else data
        return [ExecEntry.from_dict(x) for x in (items or []) if isinstance(x, dict)]
    except Exception as e:
        # 执行记录丢 = 完成标记失效、可能重做，必须留痕（每进程只报一次）
        if path not in _CORRUPT_WARNED:
            _CORRUPT_WARNED.add(path)
            print(f"[hoard_ap] 执行日志文件损坏，按空日志处理: {path} ({e})")
        return []


def save_log(config_dir: str, entries: List[ExecEntry]) -> None:
    path = log_path(config_dir)
    os.makedirs(config_dir or ".", exist_ok=True)
    payload = {
        "updated_at": time.time(),
        "entries": [e.to_dict() for e in entries[-200:]],
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def append_exec(
    config_dir: str,
    action: str,
    note: str = "",
    ok: bool = True,
    step_index: int = -1,
    meta: Optional[Dict[str, Any]] = None,
    when: Optional[datetime] = None,
) -> None:
    # 纯说明不写账本
    act = str(action or "")
    if act in _LOG_SKIP_ACTIONS:
        return
    when = when or datetime.now()
    entries = load_log(config_dir)
    entries.append(
        ExecEntry(
            when=when.isoformat(sep=" ", timespec="seconds"),
            action=act,
            note=note,
            ok=ok,
            step_index=step_index,
            meta=dict(meta or {}),
        )
    )
    save_log(config_dir, entries)


def done_actions(config_dir: str) -> List[str]:
    """返回已成功步骤的键。

    优先 `meta.done_key`（动作|日|细分）；无则退回纯 action（仅兼容旧日志）。
    """
    out: List[str] = []
    for e in load_log(config_dir):
        if not e.ok:
            continue
        meta = e.meta or {}
        key = str(meta.get("done_key") or "").strip()
        if key:
            out.append(key)
        else:
            out.append(e.action)
    return out


def format_log_section(config_dir: str, limit: int = 12) -> str:
    """精简已完成清单：时间 + 动作中文 + 可选剩余体力。"""
    entries = load_log(config_dir)
    filtered = [e for e in entries if e.action not in _LOG_SKIP_ACTIONS]
    if not filtered:
        return "（尚无执行记录）"
    action_cn = {
        "clear_ap": "清体",
        "claim_mail": "领邮",
        "claim_cafe": "咖啡领奖",
        "claim_task": "领任务体",
        "claim_group": "领小组",
        "claim_jjc": "竞技场商店",
        "buy_tubes": "买体",
        "free_buy": "礼包10体",
        "use_ap_card": "体力礼包",
        "ensure_headroom": "清出空位",
        "spend_ready": "到点花体",
    }
    lines = []
    for e in filtered[-limit:]:
        mark = "✓" if e.ok else "×"
        when = (e.when or "")[:16].replace("T", " ")  # YYYY-MM-DD HH:MM
        # 再压成 mm-dd HH:MM
        try:
            from datetime import datetime as _dt
            w = _dt.strptime(when[:16], "%Y-%m-%d %H:%M")
            when_s = w.strftime("%m-%d %H:%M")
        except Exception:
            when_s = when
        name = action_cn.get(e.action, e.action)
        extra = ""
        meta = e.meta or {}
        # 优先 meta 剩余体力
        for k in ("remain_ap", "ap_after", "current_ap", "final_ap"):
            if meta.get(k) is not None:
                try:
                    extra = f"  剩余体力：{int(meta.get(k))}"
                    break
                except Exception:
                    pass
        if not extra:
            # 从 note 里抠「余N体 / 剩N」
            import re as _re
            m = _re.search(r"(?:余|剩|剩余)\s*(\d+)\s*体", e.note or "")
            if m:
                extra = f"  剩余体力：{m.group(1)}"
            else:
                m2 = _re.search(r"→体(\d+)", e.note or "")
                if m2:
                    extra = f"  剩余体力：{m2.group(1)}"
        lines.append(f"  {mark} {when_s}  {name}{extra}".rstrip())
    return "\n".join(lines)


def clear_log(config_dir: str) -> None:
    """清空执行账本（重新计算计划时调用）。"""
    for name in (LOG_FILENAME, "hoard_ap_execution.jsonl"):
        p = os.path.join(config_dir or ".", name)
        try:
            if os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass
