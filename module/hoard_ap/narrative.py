"""把 HoardPlan 渲染成短说明（配置页常驻）。

精简口径：
- 下一动作
- 完整执行时间轴（已完成用实际完成时间；重算不改已完成时间）
- 已完成 / 未完成之间可插入「更新计划」
值守四行与已完成清单由 UI 外层拼装。
"""

from __future__ import annotations

import re as _re
from datetime import datetime
from typing import Any, List, Optional

from module.hoard_ap.constants import (
    ACTION_BUY_TUBES,
    ACTION_CLAIM_CAFE,
    ACTION_CLAIM_MAIL,
    ACTION_CLAIM_GROUP,
    ACTION_CLAIM_JJC,
    ACTION_CLAIM_TASK,
    ACTION_CLEAR_AP,
    ACTION_ENSURE_HEADROOM,
    ACTION_FREE_BUY,
    ACTION_HOLD,
    ACTION_NOTIFY,
    ACTION_SPEND_READY,
    ACTION_USE_AP_CARD,
    ACTION_WAIT,
    JJC_BUY_30,
    JJC_BUY_30_60,
    JJC_BUY_NONE,
    STRATEGY_SIMPLE,
    STRATEGY_SIMPLE_PLUS,
    STRATEGY_XIUXIAN,
)
from module.hoard_ap.planner import HoardPlan, PlanStep

STRATEGY_CN = {
    STRATEGY_SIMPLE: "懒人",
    STRATEGY_SIMPLE_PLUS: "宽松",
    STRATEGY_XIUXIAN: "勤奋",
}

JJC_CN = {
    JJC_BUY_NONE: "不买",
    JJC_BUY_30: "30",
    JJC_BUY_30_60: "30+60",
}

ACTION_CN = {
    ACTION_WAIT: "等待自回",
    ACTION_NOTIFY: "需你操作",
    ACTION_BUY_TUBES: "买体",
    ACTION_FREE_BUY: "礼包10体",
    ACTION_CLAIM_TASK: "领任务体",
    ACTION_CLAIM_GROUP: "领小组",
    ACTION_CLAIM_JJC: "竞技场商店",
    ACTION_CLAIM_CAFE: "咖啡领奖",
    ACTION_CLAIM_MAIL: "领邮",
    ACTION_USE_AP_CARD: "体力礼包",
    ACTION_CLEAR_AP: "清体",
    ACTION_ENSURE_HEADROOM: "清出空位",
    ACTION_HOLD: "挂机等待",
    ACTION_SPEND_READY: "到点花体",
}

_SKIP_IN_TIMELINE = {ACTION_NOTIFY, ACTION_HOLD, ACTION_WAIT}


def _fmt(dt: datetime) -> str:
    return dt.strftime("%m-%d %H:%M")


def _parse_when(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip().replace("T", " ")
    for n, fmt in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M")):
        try:
            return datetime.strptime(s[:n], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _human_delta(seconds: float) -> str:
    if seconds < 0:
        return "已过点"
    seconds = int(seconds)
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    parts = []
    if d:
        parts.append(f"{d}天")
    if h:
        parts.append(f"{h}时")
    if m or not parts:
        parts.append(f"{m}分")
    return "".join(parts)


def _step_when(step: Any) -> Optional[datetime]:
    if isinstance(step, PlanStep):
        return step.when
    if isinstance(step, dict):
        return _parse_when(step.get("when"))
    return None


def _step_get(step: Any, key: str, default=None):
    if isinstance(step, PlanStep):
        return getattr(step, key, default)
    if isinstance(step, dict):
        return step.get(key, default)
    return default


def _is_done(step: Any, summary: Optional[dict] = None) -> bool:
    if _step_get(step, "done_ok") or _step_get(step, "done"):
        return True
    md = _step_get(step, "meta") or {}
    if isinstance(md, dict) and md.get("done_ok"):
        return True
    dks = (summary or {}).get("done_keys") if isinstance(summary, dict) else None
    if not dks:
        return False
    try:
        from module.hoard_ap.replan import _compute_done_key as _cdk

        sk = (
            dict(step)
            if isinstance(step, dict)
            else {
                "when": getattr(step, "when", None),
                "action": getattr(step, "action", None),
                "note": getattr(step, "note", None),
                "meta": getattr(step, "meta", None) or {},
            }
        )
        return _cdk(sk) in set(dks)
    except Exception:
        return False


def _display_when(step: Any) -> Optional[datetime]:
    """已完成：只用 done_at/display_when；绝不因重算改成点计算的时间。"""
    md = _step_get(step, "meta") or {}
    done = False
    if _step_get(step, "done_ok") or _step_get(step, "done"):
        done = True
    if isinstance(md, dict) and md.get("done_ok"):
        done = True
    if isinstance(md, dict):
        if done:
            for key in ("display_when", "done_at", "planned_when"):
                pw = _parse_when(md.get(key))
                if pw is not None:
                    return pw
        else:
            pw = _parse_when(md.get("planned_when"))
            if pw is not None:
                return pw
    return _step_when(step)


def _short_note(note: str) -> str:
    note = (note or "").strip()
    note = note.replace("栏+", "体+").replace("栏位", "体力栏")
    for junk in (
        "硬顶999；",
        "硬顶999",
        "（目标≈980，硬顶999；",
        "目标≈980，",
        "花体日前按计划 0.2 领邮，主堆日 03:50 只负责堆邮）；",
        "花体日前按计划 0.2 领邮，主堆日 03:50 只负责堆邮；",
        "花体日前按计划 0.1 领邮，主堆日 03:50 只负责堆邮）；",
        "花体日前按计划 0.1 领邮，主堆日 03:50 只负责堆邮；",
        "（可进邮）",
        "可进邮",
    ):
        note = note.replace(junk, "")
    note = note.replace("主堆收工：", "")
    note = note.replace("登录体力", "登陆体力")
    note = note.replace("任务体力", "登陆体力")
    note = _re.sub(r"（补做：原定\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}）", "", note)
    note = _re.sub(r"原定\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}[，,]?", "", note)
    note = _re.sub(r"\s{2,}", " ", note).strip(" ；;")
    return note


def first_actionable_when(plan: HoardPlan, now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now()
    skip = {ACTION_NOTIFY, ACTION_HOLD, ACTION_WAIT, ACTION_SPEND_READY}
    for s in plan.steps:
        act = _step_get(s, "action")
        when = _step_when(s)
        if not when:
            continue
        if act not in skip:
            return when
    if plan.steps:
        w = _step_when(plan.steps[0])
        if w:
            return w
    return plan.spend_at


def render_plan_narrative(plan: HoardPlan, now: Optional[datetime] = None) -> str:
    now = now or datetime.now().replace(second=0, microsecond=0)
    summary = plan.summary or {}
    final_ap = summary.get("final_ap", "?")
    final_mail = summary.get("final_mail", "?")
    cafe_spend = summary.get("cafe_at_spend", 0)
    try:
        total_all = int(final_ap) + int(final_mail) + int(cafe_spend or 0)
    except Exception:
        total_all = "?"

    lines: List[str] = []

    # 下一动作 = 时间轴中最早的未完成步骤（按展示时间排序取最前，
    # 与时间轴严格一致，不依赖 steps 列表顺序）
    next_when = None
    next_name = ""
    _cands = []
    for s in plan.steps:
        act = _step_get(s, "action")
        if act in _SKIP_IN_TIMELINE:
            continue
        if _is_done(s, summary):
            continue
        w = _display_when(s)
        if w is None:
            continue
        _cands.append((w, s))
    if _cands:
        _cands.sort(key=lambda x: x[0])
        s = _cands[0][1]
        next_when = _cands[0][0]
        act = _step_get(s, "action")
        next_name = ACTION_CN.get(act, act)
        note0 = (_step_get(s, "note") or "").strip()
        if "主堆收工" in note0:
            next_name = "清体"
        elif "识别" in note0:
            next_name = "识别邮箱"

    if next_when is not None:
        lines.append(
            f"下一动作 {_fmt(next_when)}  {next_name or '—'}"
            f"（还有{_human_delta((next_when - now).total_seconds())}）"
        )
    else:
        lines.append("下一动作 —")

    # 若外层已拼精简值守头，则不再重复终点；否则补一行
    if not (isinstance(summary, dict) and summary.get("compact_head")):
        lines.append(
            f"花体 {_fmt(plan.spend_at)}（还有{_human_delta((plan.spend_at - now).total_seconds())}）"
            f"　终点约 体{final_ap} + 邮{final_mail} + 咖啡{cafe_spend} ＝ {total_all}"
        )

    # 收集时间轴条目
    items = []
    for s in plan.steps:
        act = _step_get(s, "action")
        if act in _SKIP_IN_TIMELINE:
            continue
        when = _display_when(s)
        note = _short_note(_step_get(s, "note") or "")
        name = ACTION_CN.get(act, act)
        ap = _step_get(s, "expect_ap")
        mail = _step_get(s, "expect_mail")
        meta = _step_get(s, "meta") or {}
        recipe = meta.get("clear_recipe") if isinstance(meta, dict) else None
        extra = ""
        if isinstance(recipe, list) and recipe and "步骤：" not in note:
            extra = "；步骤：" + " → ".join(str(x) for x in recipe)
        done = _is_done(s, summary)
        upd = ""
        if done and isinstance(meta, dict):
            ru = meta.get("replan_at")
            rw = _parse_when(ru)
            if rw is not None:
                upd = f"  〔更新计划 {_fmt(rw)}〕"
        milestone = bool(isinstance(meta, dict) and meta.get("milestone")) or (
            act == ACTION_SPEND_READY
        )
        items.append(
            {
                "when": when,
                "name": name,
                "ap": ap,
                "mail": mail,
                "note": note,
                "extra": extra,
                "done": done,
                "upd": upd,
                "milestone": milestone,
            }
        )

    # 时间轴按实际时间排序：已完成按完成时刻、未完成按计划时刻，
    # 避免「计划晚但实际早领」的领邮排到花体后面看着乱
    try:
        items.sort(key=lambda it: it["when"] if it["when"] is not None else datetime.max)
    except Exception:
        pass

    replan_at = None
    if isinstance(summary, dict):
        replan_at = _parse_when(
            summary.get("replan_at") or summary.get("replanned_at")
        )

    # 在「最后一个已完成」与「第一条未完成」之间插入更新计划
    cut = None
    if replan_at is not None and items:
        has_done = any(it["done"] for it in items)
        for i, it in enumerate(items):
            if not it["done"] and has_done and any(items[j]["done"] for j in range(i)):
                cut = i
                break

    lines.append("")
    lines.append("【完整执行时间轴】")
    n = 0
    if not items:
        lines.append("（无自动步骤）")
    else:
        for i, it in enumerate(items):
            if cut is not None and i == cut:
                n += 1
                lines.append(
                    f"{n}. 〔更新计划〕 {_fmt(replan_at)}  重新计算后的后续安排"
                )
            n += 1
            mark = "✓ " if it["done"] else ""
            # 里程碑（到点花体等）：单独标记，不混作普通执行步骤
            name = ("★里程碑 " if it.get("milestone") else "") + it["name"]
            body = f"{it['note']}{it['extra']}" if (it["note"] or it["extra"]) else ""
            lines.append(
                f"{n}. {mark}{_fmt(it['when']) if it['when'] else '—'}  {name}"
                f"  →体{it['ap']}/邮{it['mail']}"
                + (f"  {body}" if body else "")
                + (it.get("upd") or "")
            )

    human = []
    for s in plan.steps:
        act = _step_get(s, "action")
        mode = _step_get(s, "mode")
        note = _short_note(_step_get(s, "note") or "")
        when = _display_when(s)
        if act in (ACTION_SPEND_READY, ACTION_NOTIFY):
            continue
        if mode == "manual" or act == ACTION_USE_AP_CARD:
            human.append(
                f"· {_fmt(when) if when else '—'}  {ACTION_CN.get(act, act)}  {note}"
            )
    if human:
        lines.append("")
        lines.append("【需要你】")
        lines.extend(human[:6])

    if plan.warnings:
        lines.append("")
        lines.append("【注意】")
        for w in plan.warnings[:5]:
            lines.append("· " + str(w)[:80])

    return "\n".join(lines)
