"""迟到启动 / 漏跑：按「仍同一花体点」把未完成步骤挪到现在之后，收窄时间窗。

规则：
1. 已花体点不变（target_date + spend_time）。
2. when < now 且尚未在 execution_log 成功执行的步骤 → when 改到 now+缓冲，并尽量保持相对顺序。
3. 已执行成功的 action（按账本）从待办里跳过（step_index 前移）。
4. 产出 duty 说明：可不管 / 需开机值守 / 必须在线清体 的时间段。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _parse(s: Any) -> Optional[datetime]:
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    t = str(s).strip().replace("T", " ")
    for n, fmt in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M")):
        try:
            return datetime.strptime(t[:n], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str(s))
    except ValueError:
        return None


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


# 这些动作错过了也可用「补做」立刻跑
CATCHUP_ACTIONS = {
    "claim_task",
    "claim_task_daily_only",
    "free_buy",
    "claim_group",
    "claim_jjc",
    "buy_tubes",
    "claim_mail",
    "claim_cafe",
    "use_ap_card",
    "ensure_headroom",
    "clear_ap",
}

# 必须人在 / 脚本在线
CRITICAL_ACTIONS = {
    "clear_ap",
    "ensure_headroom",
    "buy_tubes",
    "spend_ready",
    "claim_mail",
}


def replan_steps(
    steps: Sequence[Dict[str, Any]],
    *,
    now: Optional[datetime] = None,
    done_actions: Optional[Sequence[str]] = None,
    step_index: int = 0,
    buffer_minutes: int = 0,
) -> Tuple[List[Dict[str, Any]], int, List[str]]:
    """返回 (新 steps, 新 step_index, 变更说明)。

    迟到登录：过点未做的领取/清体按原顺序立刻补做（不再 +3 分钟后才开始），
    且不得用「做过一次 claim_task」跳过同日另一批领取。
    """
    now = now or datetime.now().replace(second=0, microsecond=0)
    done = list(done_actions or [])
    notes: List[str] = []
    out: List[Dict[str, Any]] = []
    # 过点补做从「现在」起排，间隔数秒保持顺序
    cursor = now + timedelta(minutes=max(0, int(buffer_minutes)))

    # 从 step_index 起处理；之前的保留
    prefix = [dict(s) for s in steps[: max(0, step_index)]]
    rest = [dict(s) for s in steps[max(0, step_index) :]]

    new_index = len(prefix)
    skipped = 0

    def _step_done_key(s: Dict[str, Any]) -> str:
        """用于账本去重的键：动作 + 游戏日 + 细分，避免 03:50 领日程跳过 04:00 领登陆。"""
        action = str(s.get("action") or "")
        when = _parse(s.get("when"))
        day = when.strftime("%Y-%m-%d") if when else ""
        meta = s.get("meta") or {}
        part = str(meta.get("task_part") or meta.get("jjc_dynamic") or "")
        # 清体/领邮按目标区分
        tgt = meta.get("target_ap")
        extra = str(tgt) if tgt is not None else ""
        note = str(s.get("note") or "")
        if "主堆收工" in note:
            extra = "main_clear0"
        elif "花体日" in note and action == "clear_ap":
            extra = "spend_clear"
        elif "礼包" in note:
            extra = "free_room"
        return f"{action}|{day}|{part}|{extra}"

    # done 也转成可消耗的 key 列表（兼容旧账本纯 action 名）
    done_keys = []
    for d in done:
        ds = str(d)
        if "|" in ds:
            done_keys.append(ds)
        else:
            # 旧格式：仅动作名——只允许跳过「全局唯一」类，禁止 claim_* / clear_ap
            if ds in ("buy_tubes",):
                done_keys.append(ds)
            # claim_task/group/jjc/free_buy/clear 旧格式一律不跳过（防迟到漏领）
    done = done_keys

    for s in rest:
        action = str(s.get("action") or "")
        key = _step_done_key(s)
        # 精确键命中才跳过；旧纯 action 仅 buy_tubes
        skip_this = False
        if key in done:
            done.remove(key)
            skip_this = True
        elif action in done and action == "buy_tubes":
            done.remove(action)
            skip_this = True
        if skip_this:
            skipped += 1
            notes.append(f"已执行过，跳过：{key}")
            continue

        when = _parse(s.get("when"))
        if when is None:
            out.append(s)
            continue
        if when < now - timedelta(minutes=2):
            if action == "spend_ready":
                old = _fmt(when)
                s = dict(s)
                s["note"] = (s.get("note") or "") + f"（原定 {old}，现已迟到，请尽快花体）"
                s["when"] = _fmt(max(when, now))
                s["late"] = True
                notes.append(f"到点花体已过点（原 {old}），请尽快处理")
                out.append(s)
            elif action in CATCHUP_ACTIONS or action in CRITICAL_ACTIONS:
                old = _fmt(when)
                # 同批补做挤在同一分钟内（相差数秒），避免被拆成 2/4/6 分钟后才跑
                new_when = cursor
                cursor = cursor + timedelta(seconds=5)
                s = dict(s)
                s["when"] = _fmt(new_when)
                s["note"] = (s.get("note") or "") + f"（补做：原定 {old}）"
                s["late"] = True
                notes.append(f"{action} 原定 {old} → 补做 {_fmt(new_when)}")
                out.append(s)
            else:
                # wait/hold/notify：缩到现在
                s = dict(s)
                s["when"] = _fmt(now)
                s["late"] = True
                out.append(s)
        else:
            out.append(s)
            if when > cursor:
                cursor = when + timedelta(seconds=15)

    if skipped:
        notes.append(f"按执行账本跳过 {skipped} 项")
    return prefix + out, new_index, notes


def _cluster_windows(
    times: List[datetime],
    *,
    pad_before_min: int = 10,
    pad_after_min: int = 10,
    merge_gap_min: int = 40,
) -> List[Tuple[datetime, datetime]]:
    """把离散时刻收成若干「必须在线」窗口。"""
    if not times:
        return []
    ts = sorted(times)
    windows: List[Tuple[datetime, datetime]] = []
    cur0 = ts[0] - timedelta(minutes=pad_before_min)
    cur1 = ts[0] + timedelta(minutes=pad_after_min)
    for t in ts[1:]:
        a = t - timedelta(minutes=pad_before_min)
        b = t + timedelta(minutes=pad_after_min)
        if a <= cur1 + timedelta(minutes=merge_gap_min):
            cur1 = max(cur1, b)
        else:
            windows.append((cur0, cur1))
            cur0, cur1 = a, b
    windows.append((cur0, cur1))
    return windows


def build_duty_sections(
    steps: Sequence[Dict[str, Any]],
    *,
    spend_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> Dict[str, List[str]]:
    """生成值守说明：窗口 + 建议盯梢点，不罗列每条清体全文。"""
    now = now or datetime.now().replace(second=0, microsecond=0)

    # 关键批次：主堆 03:50/04:00、花体日 03:50/04:00、花体
    batch_keys = {
        "clear_ap",
        "ensure_headroom",
        "buy_tubes",
        "claim_mail",
        "claim_cafe",
        "claim_task",
        "claim_group",
        "claim_jjc",
        "free_buy",
        "spend_ready",
    }
    key_times: List[datetime] = []
    supervise_points: List[datetime] = []
    for s in steps:
        when = _parse(s.get("when"))
        if not when:
            continue
        action = str(s.get("action") or "")
        if action in ("notify", "wait", "hold"):
            continue
        if action in batch_keys:
            key_times.append(when)
        # 建议盯梢：整点批的代表时刻（:50 / :00）
        if action in ("claim_cafe", "clear_ap", "claim_mail", "claim_jjc", "buy_tubes", "free_buy"):
            if when.minute in (0, 50) or action in ("claim_cafe", "claim_mail", "clear_ap"):
                supervise_points.append(when.replace(second=0, microsecond=0))

    # 按「日 + 时段」聚成 03:40~04:00 这类窗
    windows = _cluster_windows(key_times, pad_before_min=10, pad_after_min=10, merge_gap_min=25)

    summary: List[str] = []
    must_on: List[str] = []
    # 必须开启：尽量合并成一条连续窗（从最早到花体/最晚）
    if windows:
        a0 = min(w[0] for w in windows)
        b0 = max(w[1] for w in windows)
        if spend_at and spend_at > b0:
            b0 = spend_at
        summary.append(f"必须保持开启：{_fmt(a0)}～{_fmt(b0)}")
        for a, b in windows:
            must_on.append(f"{_fmt(a)} ～ {_fmt(b)}")
    # 建议盯梢：取关键点前 1 分钟与整点，去重短写 mm-dd HH:MM
    seen = set()
    sup_lines = []
    for t in sorted(set(supervise_points)):
        # 只留 :50 / :00 / 领邮前哨
        if t.minute not in (0, 48, 49, 50, 55, 59):
            # 也允许计划里真正的关键点
            if t.minute not in (0, 50):
                continue
        k = _fmt(t)
        if k in seen:
            continue
        seen.add(k)
        sup_lines.append(k)
    # 若无 :50/:00，退回全部关键点去重
    if not sup_lines:
        for t in sorted(set(key_times)):
            k = _fmt(t)
            if k not in seen:
                seen.add(k)
                sup_lines.append(k)
    if sup_lines:
        summary.append("建议在线监督（确认执行无误）：" + "、".join(sup_lines[:6]))

    if spend_at:
        # 花体 + 终点由 UI 拼终点三件套；这里只写时刻
        summary.append(f"花体时刻（请本人在）：{_fmt(spend_at)}")

    if key_times:
        earliest = min(key_times)
        if earliest > now + timedelta(hours=1):
            summary.append(f"此窗口前可关脚本：～ {_fmt(earliest - timedelta(minutes=20))}")
    if not summary:
        summary.append("当前无待办关键节点；算完计划后这里会列出值守窗口。")

    return {
        "summary": summary,
        "must_on": must_on[:12],
        "should_on": [f"  {x}" for x in (sup_lines[:12] if sup_lines else [])],
        "can_off": [],
    }


def _compute_done_key(s: Dict[str, Any]) -> str:
    """动作|日|小时段|细分 — 与 executor 记账必须同一算法。

    补做后 step.when 会变成「现在」，若用 when 算键会对不上账本里的原定时间。
    优先：meta.done_key > 备注「原定 YYYY-MM-DD HH:MM」> when。
    """
    import re as _re
    meta = s.get("meta") or {}
    if meta.get("done_key"):
        return str(meta.get("done_key"))
    action = str(s.get("action") or "")
    note = str(s.get("note") or "")
    # 优先原定时间：planned_when > 备注原定 > when（when 可能被展示成完成时刻）
    when = _parse(meta.get("planned_when")) or _parse(s.get("when"))
    m = _re.search(r"原定\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", note)
    if m:
        when = _parse(m.group(1)) or when
    day = when.strftime("%Y-%m-%d") if when else ""
    bucket = "??:??"
    if when:
        if when.hour == 3 and when.minute >= 40:
            bucket = "03:50"
        elif when.hour == 4 and when.minute <= 20:
            bucket = "04:00"
        else:
            bucket = f"{when.hour:02d}:{when.minute:02d}"
    part = str(meta.get("task_part") or "")
    extra = ""
    # 语义键：同类步骤只做一次，不因补做改 when 而重复
    if meta.get("scan_only") or "识别邮箱" in note:
        if meta.get("after_daily") or "日替后" in note or "供竞技场" in note:
            extra = "scan_after_daily"
        elif meta.get("after_cafe") or "咖啡" in note:
            extra = "scan_after_cafe"
        else:
            extra = "scan_only"
    elif "主堆收工" in note:
        extra = "main_clear0"
    elif "花体日" in note and action == "clear_ap":
        extra = "spend_clear"
    elif "按计划领邮" in note or meta.get("planned_mail_claim"):
        # 不同领取批次用 claim_when / bucket 区分，避免一键跳过全部领邮
        cw = str(meta.get("claim_when") or bucket)
        extra = f"planned_mail_claim@{cw}"
    elif "礼包" in note:
        extra = "free_room"
    elif meta.get("jjc_dynamic") or action == "claim_jjc":
        extra = "jjc_dynamic"
    elif meta.get("target_ap") is not None and action in ("clear_ap", "ensure_headroom"):
        extra = "t" + str(meta.get("target_ap"))
    return f"{action}|{day}|{bucket}|{part}|{extra}"


def _any_done_key(done: List[str], suffix: str, day_k: str = "") -> bool:
    """账本里是否出现过含 suffix（且可选含 day_k）的 done_key。"""
    for dk in list(done):
        if suffix in str(dk) and (not day_k or day_k in str(dk)):
            return True
    return False


def _mark_step_done(s: Dict[str, Any], key: str, reason: str) -> Dict[str, Any]:
    """把步骤标记为已完成（保留在时间轴打✓）。"""
    s = dict(s)
    md = dict(s.get("meta") or {})
    md["done_ok"] = True
    md["done_key"] = key
    # 锁死原定时间：后续重算不得改 when 展示
    if not md.get("planned_when"):
        md["planned_when"] = s.get("when")
    # 若已有 done_at/display_when 则保留；没有也不要用 now 顶替
    s["meta"] = md
    s["done_ok"] = True
    # 内部备注不进用户文案（UI 已不再展示「补做：key」）
    return s


def _filter_done_steps(
    steps: List[Dict[str, Any]], done: List[str], now: datetime
) -> List[Dict[str, Any]]:
    """已做步骤：保留在时间轴并打 done_ok，执行时跳过（不再从列表删除）。"""
    done_set = set(done)
    remaining: List[Dict[str, Any]] = []
    for s in steps:
        action = str(s.get("action") or "")
        if action in ("notify", "wait", "hold"):
            # 过点说明直接丢弃，减少挡路
            when = _parse(s.get("when"))
            if when and when < now - timedelta(minutes=2):
                continue
            remaining.append(s)
            continue
        key = _compute_done_key(s)
        note_s = str(s.get("note") or "")
        meta_s = s.get("meta") or {}
        day_k = key.split("|")[1] if "|" in key else ""
        if key in done_set:
            done_set.discard(key)
            remaining.append(_mark_step_done(s, key, f"已执行过，保留✓：{key}"))
            continue
        # 语义去重：当日已做过 scan / main_clear0 / jjc，标记完成但不删
        if action == "claim_mail" and (meta_s.get("scan_only") or "识别邮箱" in note_s):
            if _any_done_key(done, "scan_after_daily", day_k) or _any_done_key(done, "scan_after_cafe", day_k) or _any_done_key(done, "scan_only", day_k):
                remaining.append(_mark_step_done(s, key, f"当日已识别过邮箱，保留✓：{key}"))
                continue
        if action == "clear_ap" and "主堆收工" in note_s:
            if _any_done_key(done, "main_clear0", day_k):
                remaining.append(_mark_step_done(s, key, f"主堆收工已完成，保留✓：{key}"))
                continue
        if action == "claim_jjc":
            if _any_done_key(done, "jjc_dynamic", day_k) or "claim_jjc" in done_set:
                remaining.append(_mark_step_done(s, key, f"竞技场已执行过，保留✓：{key}"))
                continue
        # 旧账本纯 buy_tubes
        if action == "buy_tubes" and action in done_set:
            done_set.discard(action)
            remaining.append(_mark_step_done(s, key, "已执行过，保留✓：buy_tubes"))
            continue
        remaining.append(s)
    return remaining


def _dedupe_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """同 done_key（动作+游戏日+时段+细分）的重复步骤合并为一条。

    完成态以账本为准：若重复里有一个已完成 ✓，保留该条（时间冻结）；
    全部未完成则保留最早一条，避免同一时刻同动作 ✓/× 并存。
    """
    out: List[Dict[str, Any]] = []
    first_at: Dict[str, int] = {}
    for s in steps:
        key = _compute_done_key(s)
        md = s.get("meta") or {}
        is_done = bool(md.get("done_ok") or s.get("done_ok"))
        i = first_at.get(key)
        if i is None:
            first_at[key] = len(out)
            out.append(s)
            continue
        if is_done:
            prev = out[i]
            prev_md = prev.get("meta") or {}
            if not (prev_md.get("done_ok") or prev.get("done_ok")):
                out[i] = s  # 完成态覆盖未完成副本
        # 其余重复副本丢弃
    return out


def _schedule_catchup(
    remaining: List[Dict[str, Any]], now: datetime, notes: List[str]
) -> List[Dict[str, Any]]:
    """过点步骤：按原相对顺序立刻补做（已打✓的保持原时间，不补做）。"""
    cursor = now
    out: List[Dict[str, Any]] = []
    for s in remaining:
        action = str(s.get("action") or "")
        when = _parse(s.get("when"))
        md0 = s.get("meta") or {}
        if (isinstance(md0, dict) and md0.get("done_ok")) or s.get("done_ok"):
            out.append(s)
            continue
        if when is None:
            out.append(s)
            continue
        if when < now - timedelta(minutes=1):
            # 咖啡只允许主堆 03:50；过 04:00 一律不补领（可领额度已重置/已领过）
            if action == "claim_cafe":
                if now.hour > 3 or (now.hour == 3 and now.minute >= 55) or when.hour >= 4:
                    notes.append(f"跳过咖啡补做（原 {_fmt(when)}；仅 03:50 满领一次）")
                    continue
            note0 = str(s.get("note") or "")
            # 主堆 03:50「清位领旧邮 / 主堆前领取旧邮」过 04:00 绝不能补——会把囤货掏空
            if action == "claim_mail" and (
                "主堆前领取旧邮" in note0
                or ("领完旧邮" in note0 and "scan_only" not in str((s.get("meta") or {})))
            ):
                # scan_only 识别步骤 meta 有 scan_only=True，可补
                meta0 = s.get("meta") or {}
                if not meta0.get("scan_only"):
                    notes.append(f"跳过领旧邮补做（原 {_fmt(when)}；过点后邮箱是囤货）")
                    continue
            if action == "clear_ap" and (
                "领完旧邮" in note0
                or "空出" in note0 and "旧邮" in note0
                or "主堆 03:50：清到" in note0 and "旧邮" in note0
            ):
                notes.append(f"跳过主堆前清位领邮（原 {_fmt(when)}；过点后不掏邮箱）")
                continue
            if action == "spend_ready":
                # 到点花体已过点：不再平移重排，也不补做清体。只提示，并标 expired。
                s = dict(s)
                md = dict(s.get("meta") or {})
                md["expired"] = True
                md["expired_reason"] = "spend_window_passed"
                md["planned_when"] = md.get("planned_when") or _fmt(when)
                s["meta"] = md
                s["note"] = (
                    f"已超过花体时刻（原定 {_fmt(when)}），请本人自行花体；"
                    f"系统不再自动清体/重排后续囤体步骤"
                )
                s["when"] = _fmt(when)  # 保持原时刻，不改到 now
                s["late"] = True
                s["mode"] = "manual"
                notes.append(
                    f"已超过花体时刻（原 {_fmt(when)}），拒绝自动重排，请自行花体"
                )
                out.append(s)
            elif action == "clear_ap" and (
                (s.get("meta") or {}).get("spend_day_clear")
                or "花体日" in note0
                or "花体到点" in note0
            ):
                # 仅拦「花体日到点清体」；主堆收工清 0 仍允许补做
                notes.append(f"跳过花体后清体补做（原 {_fmt(when)}）")
                continue
            elif action in CATCHUP_ACTIONS or action in CRITICAL_ACTIONS:
                s = dict(s)
                s["when"] = _fmt(cursor)
                s["note"] = (s.get("note") or "") + f"（补做：原定 {_fmt(when)}）"
                s["late"] = True
                notes.append(f"{action} 原定 {_fmt(when)} → 补做 {_fmt(cursor)}")
                out.append(s)
                cursor = cursor + timedelta(seconds=5)
            else:
                continue  # 丢弃过点 notify
        else:
            out.append(s)
            if when > cursor:
                cursor = when + timedelta(seconds=5)
    return out


def _finalize_replan(
    plan: Dict[str, Any],
    out: List[Dict[str, Any]],
    notes: List[str],
    done: List[str],
    now: datetime,
) -> Tuple[Dict[str, Any], int, Dict[str, List[str]]]:
    """冻结已完成步骤时间、重算值守段、定位起始下标。"""
    plan = dict(plan)
    # 已完成步骤：when 固定为 display_when/done_at/planned_when，禁止被后续逻辑改掉
    frozen_out: List[Dict[str, Any]] = []
    for s in out:
        s = dict(s)
        md = dict(s.get("meta") or {})
        if md.get("done_ok") or s.get("done_ok"):
            if not md.get("planned_when"):
                md["planned_when"] = s.get("when")
            # 展示时间优先实际完成
            show = md.get("display_when") or md.get("done_at") or md.get("planned_when") or s.get("when")
            # 不把 s["when"] 改成 now；保持 planned 或 done
            if md.get("planned_when"):
                s["when"] = md.get("planned_when")
            # display_when 单独承载完成时刻
            if md.get("done_at") and not md.get("display_when"):
                md["display_when"] = md.get("done_at")
            s["meta"] = md
            s["done_ok"] = True
        frozen_out.append(s)
    out = frozen_out
    # 局部排 pending 步骤：reproject 改了领邮 when，不排会时间倒退。
    # done 步骤保持原位置（时间轴稳定），只对相邻 pending 按 when 排序。
    try:
        from datetime import datetime as _dt

        def _k(s):
            w = _parse(s.get("when"))
            return w if w is not None else _dt.max

        result = []
        pending = []
        for s in out:
            if (s.get("meta") or {}).get("done_ok") or s.get("done_ok"):
                if pending:
                    result.extend(sorted(pending, key=_k))
                    pending = []
                result.append(s)
            else:
                pending.append(s)
        if pending:
            result.extend(sorted(pending, key=_k))
        out = result
    except Exception:
        pass
    plan["steps"] = out
    spend = _parse(plan.get("spend_at"))
    # 值守只看未完成
    pending = [
        s for s in out
        if not ((s.get("meta") or {}).get("done_ok") or s.get("done_ok"))
        and str(s.get("action") or "") not in ("notify", "wait", "hold")
    ]
    duty = build_duty_sections(pending or out, spend_at=spend, now=now)
    plan["duty"] = duty
    plan["replan_notes"] = notes  # 仅内部
    plan["replanned_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    # summary 注入 replan_at，供时间轴插入「更新计划」
    sm = dict(plan.get("summary") or {})
    if notes or done:
        sm["replan_at"] = plan["replanned_at"]
        sm["replanned_at"] = plan["replanned_at"]
    plan["summary"] = sm
    # 从第一条未完成步骤开始；已完成保留在轴上打✓
    start_idx = 0
    for i, s in enumerate(out):
        if (s.get("meta") or {}).get("done_ok") or s.get("done_ok"):
            continue
        if str(s.get("action") or "") in ("notify", "wait", "hold"):
            continue
        start_idx = i
        break
    else:
        start_idx = max(0, len(out))
    return plan, start_idx, duty


def apply_replan_to_state_plan(
    plan: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
    done_actions: Optional[Sequence[str]] = None,
    step_index: int = 0,
) -> Tuple[Dict[str, Any], int, List[str], Dict[str, List[str]]]:
    """迟到重算。

    关键：不信任可能偏大的 step_index。
    从完整 steps 按 done_key 去掉已做，再把过点未做按原顺序排到现在执行。
    这样 04:01 登录仍会先领小组/任务/JJC，最后才主堆清 0。
    """
    now = now or datetime.now().replace(second=0, microsecond=0)
    steps = [dict(s) for s in (plan.get("steps") or [])]
    done = list(done_actions or [])
    notes: List[str] = []

    remaining = _filter_done_steps(steps, done, now)
    out = _schedule_catchup(remaining, now, notes)
    out = _dedupe_steps(out)
    plan, start_idx, duty = _finalize_replan(plan, out, notes, done, now)
    return plan, start_idx, notes, duty


def _bag_claim_at(bag: Dict[str, Any], now: datetime) -> Optional[datetime]:
    """单包计划领取时刻：到期前 6 分钟；已过点则 now。"""
    try:
        rh = float(bag.get("remain_hours"))
    except Exception:
        return None
    if rh < 0:
        return None
    # 已过期 / 马上没了：立刻
    if rh <= 0.02:
        return now
    expire = now + timedelta(hours=rh)
    claim_at = expire - timedelta(minutes=6)
    if claim_at < now:
        return now
    return claim_at.replace(second=0, microsecond=0)


def _is_pending_mail_driven_step(s: Dict[str, Any]) -> bool:
    """未完成、且应由邮箱剩余时间驱动的步骤。"""
    md = s.get("meta") or {}
    if md.get("done_ok") or s.get("done_ok"):
        return False
    # 纯识别不重投影领取时刻
    if md.get("scan_only"):
        return False
    action = str(s.get("action") or "")
    note = str(s.get("note") or "")
    if md.get("planned_mail_claim"):
        return True
    if action == "claim_mail":
        return True
    if action == "clear_ap" and (
        md.get("planned_mail_claim")
        or "领计划邮" in note
        or "空出" in note and "邮" in note
    ):
        return True
    return False


def _mail_bag_id(b: Dict[str, Any], i: int) -> str:
    return f"{b.get('amount')}|{b.get('remain_hours')}|{b.get('remain_text')}|{i}"


def _load_live_mail_bags(inventory_snapshot: Any, now: datetime) -> List[Dict[str, Any]]:
    """可领包收集：优先 project_display（不到1h 内计时/粗小时回推），留有剩余且有面额的。"""
    bags: List[Dict[str, Any]] = []
    try:
        from module.hoard_ap.inventory import project_display

        disp = project_display(inventory_snapshot, now=now)
        bags = [dict(b) for b in (disp.get("mail_bags") or []) if isinstance(b, dict)]
    except Exception:
        raw = getattr(inventory_snapshot, "mail_bags", None) or []
        bags = [dict(b) for b in raw if isinstance(b, dict)]

    live: List[Dict[str, Any]] = []
    for b in bags:
        try:
            rh = float(b.get("remain_hours"))
        except Exception:
            continue
        if rh < 0:
            continue
        amt = int(b.get("amount") or 0)
        if amt <= 0:
            continue
        ca = _bag_claim_at(b, now)
        if ca is None:
            continue
        bb = dict(b)
        bb["_claim_at"] = ca
        bb["_amt"] = amt
        live.append(bb)
    return live


def _match_bags_for_step(
    md: Dict[str, Any],
    note: str,
    groups: Dict[str, List[Dict[str, Any]]],
    group_keys: List[str],
    used_bag_ids: set,
) -> List[Dict[str, Any]]:
    """给单个领邮步骤匹配包裹：优先按面额对上，退到总量，再无金额吃最早短倒计时批。"""
    import re as _re

    # 目标金额列表
    amounts: List[int] = []
    raw_am = md.get("claim_amounts")
    if isinstance(raw_am, list) and raw_am:
        try:
            amounts = [int(x) for x in raw_am if int(x) > 0]
        except Exception:
            amounts = []
    if not amounts:
        # 从 note 抠 50@0.1h、663@0.1h
        for m in _re.finditer(r"(\d+)\s*@", note):
            try:
                amounts.append(int(m.group(1)))
            except Exception:
                pass

    matched: List[Dict[str, Any]] = []
    if amounts:
        need = list(amounts)
        # 先在各批里按金额贪心匹配
        for gk in group_keys:
            for b in groups[gk]:
                if b["_id"] in used_bag_ids:
                    continue
                if b["_amt"] in need:
                    matched.append(b)
                    need.remove(b["_amt"])
            if not need:
                break
        # 若金额对不齐，退回：用最早一批足够总量的包
        if need:
            matched = []
            need_sum = sum(amounts)
            acc = 0
            for gk in group_keys:
                for b in groups[gk]:
                    if b["_id"] in used_bag_ids:
                        continue
                    matched.append(b)
                    acc += b["_amt"]
                    if acc >= need_sum:
                        break
                if acc >= need_sum:
                    break
    else:
        # 无金额：领邮步骤吃最早一批尚未占用的短倒计时包
        # 跳过仍很长的 6 天包（>=48h）除非只剩它们
        short_first = []
        long_rest = []
        for gk in group_keys:
            for b in groups[gk]:
                if b["_id"] in used_bag_ids:
                    continue
                try:
                    rh = float(b.get("remain_hours") or 0)
                except Exception:
                    rh = 0
                if rh >= 48:
                    long_rest.append(b)
                else:
                    short_first.append(b)
        pool = short_first or long_rest
        if not pool:
            return []
        # 同一领取分钟的一批
        first_key = pool[0]["_claim_at"].strftime("%Y-%m-%d %H:%M")
        matched = [b for b in pool if b["_claim_at"].strftime("%Y-%m-%d %H:%M") == first_key]
    return matched


def _apply_reproject_to_step(
    s: Dict[str, Any],
    matched: List[Dict[str, Any]],
    now: datetime,
    used_bag_ids: set,
) -> Optional[Tuple[str, str, str]]:
    """把匹配结果写回单个步骤；时间没变也占包（防下一步抢同一批）。

    返回 (old_norm, new_norm, detail)；未变返回 None。
    """
    import re as _re

    action = str(s.get("action") or "")
    new_when_dt = min(b["_claim_at"] for b in matched)
    # clear_ap 略早于领邮 1 分钟，方便空位
    if action == "clear_ap":
        new_when_dt = max(now, new_when_dt - timedelta(minutes=1))
    new_when = new_when_dt.strftime("%Y-%m-%d %H:%M")
    old_when = str(s.get("when") or "").strip()
    # 归一比较
    old_norm = old_when.replace("T", " ")[:16]
    new_norm = new_when[:16]
    if old_norm == new_norm:
        for b in matched:
            used_bag_ids.add(b["_id"])
        return None

    md = dict(s.get("meta") or {})
    note = str(s.get("note") or "")
    if not md.get("planned_when") and old_when:
        md["planned_when"] = old_when
    md["reprojected_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    md["reprojected_from"] = old_when
    md["claim_when"] = new_when
    if matched and not md.get("claim_amounts"):
        md["claim_amounts"] = [int(b["_amt"]) for b in matched]
    detail = "、".join(
        f"{b['_amt']}@{float(b.get('remain_hours') or 0):.1f}h" for b in matched[:8]
    )
    # 更新 note 时间戳 + 明细摘要（尽量轻改）
    note2 = _re.sub(
        r"\d{2}-\d{2} \d{2}:\d{2}",
        new_when_dt.strftime("%m-%d %H:%M"),
        note,
        count=1,
    )
    if "按计划领取" in note2 or "领计划邮" in note2 or action == "claim_mail":
        # 刷新括号内明细
        if "（" in note2 and "）" in note2:
            note2 = _re.sub(r"（[^）]*）", f"（{detail}）", note2, count=1)
        elif detail and "按计划领取" in note2:
            note2 = note2.rstrip() + f"（{detail}）"
    s["when"] = new_when
    s["note"] = note2
    s["meta"] = md
    for b in matched:
        used_bag_ids.add(b["_id"])
    return old_norm, new_norm, detail


def reproject_mail_steps_from_inventory(
    plan: Dict[str, Any],
    inventory_snapshot: Any,
    now: Optional[datetime] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """按最新邮箱明细，重投影未完成领邮相关步骤的 when。

    与「把所有领邮都改成最晚一包时间」不同：
    - 用 project_display 后的 remain（含不到1h 内计时）
    - 按包裹分批（同一领取分钟一批）
    - 优先用 meta.claim_amounts 对上具体包
    - scan_only / 已完成步骤不动
    """
    now = now or datetime.now().replace(second=0, microsecond=0)
    plan = dict(plan or {})
    steps = [dict(s) for s in (plan.get("steps") or [])]
    notes: List[str] = []

    live = _load_live_mail_bags(inventory_snapshot, now)
    if not live:
        return plan, notes

    # 按领取分钟分批
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for b in live:
        key = b["_claim_at"].strftime("%Y-%m-%d %H:%M")
        groups.setdefault(key, []).append(b)
    group_keys = sorted(groups.keys())

    pending_idx = [i for i, s in enumerate(steps) if _is_pending_mail_driven_step(s)]
    if not pending_idx:
        return plan, notes

    # 给 live 稳定 id
    for i, b in enumerate(live):
        b["_id"] = _mail_bag_id(b, i)

    used_bag_ids = set()
    changed = 0
    for si in pending_idx:
        s = steps[si]
        md = dict(s.get("meta") or {})
        note = str(s.get("note") or "")
        matched = _match_bags_for_step(md, note, groups, group_keys, used_bag_ids)
        if not matched:
            continue
        res = _apply_reproject_to_step(s, matched, now, used_bag_ids)
        if res is None:
            continue
        steps[si] = s
        changed += 1
        old_norm, new_norm, detail = res
        action = str(s.get("action") or "")
        notes.append(
            f"{action} {old_norm or '—'}→{new_norm}（{detail or '邮箱重投影'}）"
        )

    if changed:
        plan["steps"] = steps
        stamp = now.strftime("%Y-%m-%d %H:%M:%S")
        plan["replanned_at"] = stamp
        sm = dict(plan.get("summary") or {})
        sm["replan_at"] = stamp
        sm["replanned_at"] = stamp
        plan["summary"] = sm
        notes.insert(0, f"邮箱时间已重投影 {changed} 步（按剩余时间，到期前6分）")
    return plan, notes


def _pending_claim_amount_multiset(steps: List[Dict[str, Any]]) -> List[int]:
    """未完成领邮步骤已占用的面额列表（可重复）。"""
    import re as _re

    occupied: List[int] = []
    for s in steps:
        if not _is_pending_mail_driven_step(s):
            continue
        if str(s.get("action") or "") == "clear_ap":
            # 清体步骤的 claim_amounts 与后续领邮成对，避免双计
            continue
        md = s.get("meta") or {}
        raw = md.get("claim_amounts")
        got = False
        if isinstance(raw, list) and raw:
            for x in raw:
                try:
                    v = int(x)
                except Exception:
                    continue
                if v > 0:
                    occupied.append(v)
                    got = True
        if got:
            continue
        note = str(s.get("note") or "")
        for m in _re.finditer(r"(?<![.\d])(\d{1,4})\s*@", note):
            try:
                v = int(m.group(1))
            except Exception:
                continue
            if 1 <= v <= 999:
                occupied.append(v)
                got = True
        if got:
            continue
        m = _re.search(r"[+＋]\s*(\d{1,4})", note)
        if m:
            try:
                occupied.append(int(m.group(1)))
            except Exception:
                pass
    return occupied


def _take_uncovered_bags(
    live: List[Dict[str, Any]], occupied: List[int]
) -> List[Dict[str, Any]]:
    """从 live 包中去掉已被步骤占用的面额，返回仍无步骤的包。"""
    need = list(occupied)
    out: List[Dict[str, Any]] = []
    for b in live:
        amt = int(b.get("_amt") or b.get("amount") or 0)
        if amt <= 0:
            continue
        if amt in need:
            need.remove(amt)
            continue
        out.append(b)
    return out


def _spend_window_blocks_insert(plan: Dict[str, Any], now: datetime) -> bool:
    """到点花体已到/已过：拒绝自动插清体领邮（那是本人花体时间）。"""
    spend_at = _parse(plan.get("spend_at"))
    if spend_at is not None and now >= spend_at - timedelta(minutes=1):
        return True
    for s in plan.get("steps") or []:
        if str(s.get("action") or "") != "spend_ready":
            continue
        md = s.get("meta") or {}
        if md.get("done_ok") or s.get("done_ok") or md.get("expired"):
            return True
        sw = _parse(s.get("when"))
        if sw is not None and now >= sw - timedelta(minutes=1):
            return True
    return False


def _load_live_bags_and_ap(
    inventory_snapshot: Any, now: datetime, current_ap: Optional[int]
) -> Tuple[List[Dict[str, Any]], int]:
    """从库存快照读可领包（带 _claim_at/_amt/_rh）与当前体力。"""
    bags: List[Dict[str, Any]] = []
    ap_now = current_ap
    try:
        from module.hoard_ap.inventory import project_display

        disp = project_display(inventory_snapshot, now=now)
        bags = [dict(b) for b in (disp.get("mail_bags") or []) if isinstance(b, dict)]
        if ap_now is None:
            try:
                ap_now = int(disp.get("current_ap"))
            except Exception:
                ap_now = None
    except Exception:
        raw = getattr(inventory_snapshot, "mail_bags", None) or []
        bags = [dict(b) for b in raw if isinstance(b, dict)]
    if ap_now is None:
        try:
            ap_now = int(getattr(inventory_snapshot, "current_ap", 0) or 0)
        except Exception:
            ap_now = 0

    live: List[Dict[str, Any]] = []
    for b in bags:
        try:
            rh = float(b.get("remain_hours"))
        except Exception:
            continue
        if rh < 0:
            continue
        amt = int(b.get("amount") or 0)
        if amt <= 0:
            continue
        ca = _bag_claim_at(b, now)
        if ca is None:
            continue
        bb = dict(b)
        bb["_claim_at"] = ca
        bb["_amt"] = amt
        bb["_rh"] = rh
        live.append(bb)
    return live, int(ap_now or 0)


def _build_residue_claim_steps(
    groups: Dict[str, List[Dict[str, Any]]], now: datetime, hard: int, ap_sim: int
) -> List[Dict[str, Any]]:
    """按领取分钟分批生成「清体（如需）+领邮」补排步骤。"""
    new_steps: List[Dict[str, Any]] = []
    for key in sorted(groups.keys()):
        group = groups[key]
        when_dt = min(b["_claim_at"] for b in group)
        if when_dt < now:
            when_dt = now
        when_s = when_dt.strftime("%Y-%m-%d %H:%M")
        amts = [int(b["_amt"]) for b in group]
        need = min(sum(amts), hard)
        if need <= 0:
            continue
        detail = "、".join(
            f"{b['_amt']}@{float(b.get('_rh') or 0):.1f}h" for b in group[:8]
        )
        target = max(0, hard - need)
        # 角色位不够：先插清体
        if ap_sim > target:
            drop = ap_sim - target
            clear_when = (when_dt - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
            if (when_dt - timedelta(minutes=1)) < now:
                clear_when = now.strftime("%Y-%m-%d %H:%M")
            new_steps.append(
                {
                    "when": clear_when,
                    "action": "clear_ap",
                    "mode": "auto",
                    "amount": int(drop),
                    "note": (
                        f"残余邮自动补排 {when_dt.strftime('%m-%d %H:%M')}："
                        f"清到 {target}，空出 {need} 领邮（{detail}）"
                    ),
                    "meta": {
                        "target_ap": int(target),
                        "planned_mail_claim": True,
                        "claim_when": when_s,
                        "claim_amounts": list(amts),
                        "auto_injected": True,
                        "injected_from_inventory": True,
                    },
                }
            )
            ap_sim = target
        new_steps.append(
            {
                "when": when_s,
                "action": "claim_mail",
                "mode": "auto",
                "amount": int(need),
                "note": (
                    f"残余邮自动补排 {when_dt.strftime('%m-%d %H:%M')}："
                    f"按计划领取 +{need}（{detail}｜设备端为一键全领）"
                ),
                "meta": {
                    "planned_mail_claim": True,
                    "claim_when": when_s,
                    "claim_amounts": list(amts),
                    "auto_injected": True,
                    "injected_from_inventory": True,
                },
            }
        )
        # 领入角色
        ap_sim = min(hard, ap_sim + need)
    return new_steps


def _merge_injected_steps(
    steps: List[Dict[str, Any]], new_steps: List[Dict[str, Any]], now: datetime
) -> List[Dict[str, Any]]:
    """不整体重排已完成与未完成的相对大结构：只把新步骤插到
    「第一条 when>=新when 的未完成」前。"""
    out = list(steps)
    for ns in sorted(new_steps, key=lambda s: _parse(s.get("when")) or now):
        nwhen = _parse(ns.get("when")) or now
        insert_at = len(out)
        for i, s in enumerate(out):
            md = s.get("meta") or {}
            if md.get("done_ok") or s.get("done_ok"):
                continue
            sw = _parse(s.get("when"))
            if sw is None:
                continue
            if sw >= nwhen:
                insert_at = i
                break
        out.insert(insert_at, ns)
    return out


def ensure_mail_claim_steps_from_inventory(
    plan: Dict[str, Any],
    inventory_snapshot: Any,
    now: Optional[datetime] = None,
    *,
    current_ap: Optional[int] = None,
    hard_cap: int = 999,
) -> Tuple[Dict[str, Any], List[str]]:
    """邮箱里还有包、但计划已无对应未完成领邮时，按剩余时间插入领取步骤。

    典型场景：主堆邮已领完打✓，OCR 又扫到残余 60/184，原 reproject 因
    pending 领邮为空直接 return，页面只剩 04:00 日常，永远不会再去邮箱。

    到点花体已到/已过：不再自动插「清体+领邮」（那是本人花体时间，禁止按清体去向乱清）。
    """
    now = now or datetime.now().replace(second=0, microsecond=0)
    plan = dict(plan or {})
    steps = [dict(s) for s in (plan.get("steps") or [])]
    notes: List[str] = []

    # 花体已到点：拒绝自动插清体领邮
    if _spend_window_blocks_insert(plan, now):
        return plan, notes

    live, ap_now = _load_live_bags_and_ap(inventory_snapshot, now, current_ap)
    if not live:
        return plan, notes

    occupied = _pending_claim_amount_multiset(steps)
    uncovered = _take_uncovered_bags(live, occupied)
    if not uncovered:
        return plan, notes

    # 按领取分钟分批
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for b in uncovered:
        key = b["_claim_at"].strftime("%Y-%m-%d %H:%M")
        groups.setdefault(key, []).append(b)

    hard = int(hard_cap or 999)
    new_steps = _build_residue_claim_steps(groups, now, hard, max(0, int(ap_now or 0)))
    if not new_steps:
        return plan, notes

    plan["steps"] = _merge_injected_steps(steps, new_steps, now)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    plan["replanned_at"] = stamp
    sm = dict(plan.get("summary") or {})
    sm["replan_at"] = stamp
    sm["replanned_at"] = stamp
    plan["summary"] = sm
    total_mail = sum(int(b["_amt"]) for b in uncovered)
    notes.append(
        f"残余邮自动补排 {len(new_steps)} 步（未覆盖约 {total_mail} 体）"
    )
    for ns in new_steps[:4]:
        notes.append(f"+{ns.get('action')}@{str(ns.get('when'))[5:16]}")
    return plan, notes
