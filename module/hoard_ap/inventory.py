"""现状快照：计算时落盘，打开页面按小时回推显示。

- 角色体力：min(soft_cap, snap + 10 * whole_hours)（仅 base<soft 时涨）
- 咖啡可领：min(cafe_cap, snap + (cafe_cap/24) * hours)
- 邮箱总量：不自动涨；mail_bags 保留 OCR 明细
- 今日已领：每日 04:00 复位；执行成功才置已领
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from module.hoard_ap.constants import AP_PER_HOUR, AP_SOFT_NATURAL_CAP, SERVER_DAY_RESET_HOUR

# 损坏文件每进程只报一次，防止调度每 tick 刷屏
_CORRUPT_WARNED = set()

INVENTORY_FILENAME = "hoard_ap_inventory.json"


@dataclass
class InventorySnapshot:
    snapped_at: str = ""  # iso
    current_ap: int = 0
    mail_ap: int = 0
    cafe_claimable: int = 0
    soft_cap: int = AP_SOFT_NATURAL_CAP
    cafe_cap: float = 740.0
    # 已领（执行后才 true；4:00 复位）
    task_claimed: bool = False
    lesson_claimed: bool = False  # 日程 50 部分
    jjc_claimed: bool = False
    group_claimed: bool = False
    free_buy_claimed: bool = False
    claimed_day_start: str = ""  # 当前已领所属的游戏日 04:00 iso
    # 邮箱明细（OCR / 手填）
    mail_bags: List[Dict[str, Any]] = field(default_factory=list)
    mail_scanned_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InventorySnapshot":
        data = data or {}
        bags = data.get("mail_bags") or []
        if not isinstance(bags, list):
            bags = []
        return cls(
            snapped_at=str(data.get("snapped_at") or ""),
            current_ap=int(data.get("current_ap") or 0),
            mail_ap=int(data.get("mail_ap") or 0),
            cafe_claimable=int(data.get("cafe_claimable") or 0),
            soft_cap=int(data.get("soft_cap") or AP_SOFT_NATURAL_CAP),
            cafe_cap=float(data.get("cafe_cap") or 740),
            task_claimed=bool(data.get("task_claimed") or False),
            lesson_claimed=bool(data.get("lesson_claimed") or False),
            jjc_claimed=bool(data.get("jjc_claimed") or False),
            group_claimed=bool(data.get("group_claimed") or False),
            free_buy_claimed=bool(data.get("free_buy_claimed") or False),
            claimed_day_start=str(data.get("claimed_day_start") or ""),
            mail_bags=[b for b in bags if isinstance(b, dict)],
            mail_scanned_at=str(data.get("mail_scanned_at") or ""),
        )


def _parse(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = s.replace("T", " ")
    for n, fmt in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M")):
        try:
            return datetime.strptime(s[:n], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def server_day_start(dt: datetime) -> datetime:
    b = dt.replace(hour=SERVER_DAY_RESET_HOUR, minute=0, second=0, microsecond=0)
    if dt < b:
        b -= timedelta(days=1)
    return b


def inventory_path(config_dir: str) -> str:
    return os.path.join(config_dir, INVENTORY_FILENAME)


def load_inventory(config_dir: str) -> InventorySnapshot:
    path = inventory_path(config_dir)
    if not os.path.isfile(path):
        return InventorySnapshot()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return InventorySnapshot.from_dict(json.load(f))
    except Exception as e:
        # 账本（已领标记/邮包）全丢 = 可能重复领，必须留痕（每进程只报一次）
        if path not in _CORRUPT_WARNED:
            _CORRUPT_WARNED.add(path)
            print(f"[hoard_ap] 库存账本文件损坏，按空账本重置: {path} ({e})")
        return InventorySnapshot()


def save_inventory(config_dir: str, snap: InventorySnapshot) -> None:
    path = inventory_path(config_dir)
    os.makedirs(config_dir or ".", exist_ok=True)
    # 原子写：写一半被打断会把整份库存（体力/邮箱/已领）读成空快照
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snap.to_dict(), f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def format_mail_bags_text(bags: List[Dict[str, Any]]) -> str:
    """人读：20×1(23h) + 30×1(22h)"""
    if not bags:
        return ""
    parts = []
    for b in bags:
        amt = int(b.get("amount") or 0)
        if amt <= 0:
            continue
        rh = b.get("remain_hours")
        if rh is None or float(rh) < 0:
            parts.append("%d" % amt)
        else:
            parts.append("%d(%.1fh)" % (amt, float(rh)))
    return " + ".join(parts)


def format_mail_bags_input(bags: List[Dict[str, Any]]) -> str:
    """表单可编辑格式：20@18,30@0.4；不到1h 内计时显示小数"""
    if not bags:
        return ""
    parts = []
    for b in bags:
        amt = int(b.get("amount") or 0)
        if amt <= 0:
            continue
        if b.get("under_1h") or str(b.get("timer_mode") or "") == "under_1h_internal":
            try:
                s = ("%.2f" % float(b.get("remain_hours") or 0.99)).rstrip("0").rstrip(".")
            except Exception:
                s = "0.99"
            parts.append("%d@%s" % (amt, s))
            continue
        rh = b.get("remain_hours")
        if rh is None or float(rh) < 0:
            parts.append("%d@23" % amt)
        else:
            s = ("%.1f" % float(rh)).rstrip("0").rstrip(".")
            parts.append("%d@%s" % (amt, s))
    return ",".join(parts)



def merge_mail_bags_with_timer(
    old_bags: List[Dict[str, Any]],
    new_bags: List[Dict[str, Any]],
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """合并 OCR 结果与内计时。

    规则：
    - 新识别到「不到1小时」且旧包尚无 under_1h_since：记下 under_1h_since=now，
      之后 remain_hours = 1.0 - (now - since)/3600（小数点内计时）。
    - 已在计时中：保留 since，用内计时更新 remain；OCR 仍显示不到1h 不重置 since。
    - 精确/粗粒度小时：直接用 OCR 值，清 under_1h_since。
    - 主堆囤货包可带 role=stack_for_claim（计划写入），合并时尽量按 amount 对齐保留。
    """
    now = now or datetime.now().replace(second=0, microsecond=0)
    old_by_amt: Dict[int, List[Dict[str, Any]]] = {}
    for b in old_bags or []:
        if not isinstance(b, dict):
            continue
        a = int(b.get("amount") or 0)
        old_by_amt.setdefault(a, []).append(dict(b))

    out: List[Dict[str, Any]] = []
    for nb in new_bags or []:
        if not isinstance(nb, dict):
            continue
        b = dict(nb)
        amt = int(b.get("amount") or 0)
        under = bool(b.get("under_1h"))
        t = str(b.get("remain_text") or "")
        if not under and re_search_under(t):
            under = True
            b["under_1h"] = True
        # 找同面额旧包（FIFO）
        prev = None
        lst = old_by_amt.get(amt) or []
        if lst:
            prev = lst.pop(0)
        if under:
            since_s = ""
            if prev and prev.get("under_1h_since"):
                since_s = str(prev.get("under_1h_since") or "")
            if not since_s:
                since_s = now.isoformat(sep=" ", timespec="seconds")
            b["under_1h"] = True
            b["under_1h_since"] = since_s
            t0 = _parse(since_s) or now
            elapsed = max(0.0, (now - t0).total_seconds() / 3600.0)
            # 首次看到不到1h：从 1.0 起算；已走 elapsed
            b["remain_hours"] = max(0.0, 1.0 - elapsed)
            b["timer_mode"] = "under_1h_internal"
        else:
            # 精确或粗小时
            b["under_1h"] = False
            b.pop("under_1h_since", None)
            if b.get("coarse_hours") or (
                isinstance(b.get("remain_hours"), (int, float))
                and float(b.get("remain_hours")) >= 1.0
                and ":" not in t
            ):
                b["timer_mode"] = "coarse_hours"
            else:
                b["timer_mode"] = "precise"
            if prev and prev.get("role"):
                b["role"] = prev.get("role")
            if not b.get("role"):
                try:
                    rhv = float(b.get("remain_hours") if b.get("remain_hours") is not None else -1)
                except Exception:
                    rhv = -1.0
                if rhv >= 2.0 or (amt >= 200 and rhv >= 1.0):
                    b["role"] = "stack_for_claim"
        if prev and prev.get("role") and not b.get("role"):
            b["role"] = prev.get("role")
        out.append(b)
    return out


def re_search_under(t: str) -> bool:
    return bool(re.search(r"不到|不足|以内|未满|少于", str(t or "")))


def project_display(
    snap: InventorySnapshot,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """打开页面时的显示值（含小时递增）。"""
    now = now or datetime.now().replace(second=0, microsecond=0)
    # 4:00 复位已领
    day = server_day_start(now)
    day_s = day.isoformat(sep=" ", timespec="seconds")
    task_c = snap.task_claimed
    lesson_c = snap.lesson_claimed
    jjc_c = snap.jjc_claimed
    group_c = snap.group_claimed
    free_c = snap.free_buy_claimed
    if snap.claimed_day_start != day_s:
        task_c = lesson_c = jjc_c = group_c = free_c = False

    t0 = _parse(snap.snapped_at) or now
    hours = max(0.0, (now - t0).total_seconds() / 3600.0)
    whole = int(hours)  # 整小时
    soft = max(0, int(snap.soft_cap))
    base = int(snap.current_ap)
    # 自然回复：仅当当前低于「角色体力上限(软顶)」时才按小时涨，涨到软顶为止。
    if soft > 0 and base < soft:
        ap = min(soft, base + int(whole * AP_PER_HOUR))
    else:
        ap = base
    cafe_cap = float(snap.cafe_cap or 740)
    per_h = cafe_cap / 24.0 if cafe_cap > 0 else 0.0
    cafe = float(snap.cafe_claimable) + hours * per_h
    cafe = int(round(min(cafe, cafe_cap)))

    bags = list(snap.mail_bags or [])
    scanned = _parse(snap.mail_scanned_at) or t0
    elapsed_h = max(0.0, (now - scanned).total_seconds() / 3600.0)
    bags_view = []
    mail_sum = 0
    for b in bags:
        bb = dict(b)
        # 内计时：不到1小时从 under_1h_since 起算
        if bb.get("under_1h") and bb.get("under_1h_since"):
            t_u = _parse(str(bb.get("under_1h_since"))) or scanned
            el_u = max(0.0, (now - t_u).total_seconds() / 3600.0)
            bb["remain_hours"] = max(0.0, 1.0 - el_u)
            bb["timer_mode"] = "under_1h_internal"
            if bb["remain_hours"] <= 0:
                continue
        else:
            rh = float(bb.get("remain_hours") if bb.get("remain_hours") is not None else -1)
            if rh >= 0:
                bb["remain_hours"] = max(0.0, rh - elapsed_h)
                if bb["remain_hours"] <= 0:
                    continue
        mail_sum += int(bb.get("amount") or 0)
        bags_view.append(bb)
    if bags_view:
        mail_ap = mail_sum
    elif bags:
        # 记录过明细但全部到期/领完 → 总量归零。
        # 绝不能回退旧 mail_ap，否则到期后旧合计「幽灵重现」。
        mail_ap = 0
    else:
        # 从未记录明细的旧版仅总量快照：保留总量估算
        mail_ap = max(0, int(snap.mail_ap))

    return {
        "current_ap": max(0, ap),
        "mail_ap": mail_ap,
        "mail_bags": bags_view,
        "mail_bags_text": format_mail_bags_text(bags_view),
        "cafe_claimable": max(0, cafe),
        "soft_cap": soft,
        "cafe_cap": cafe_cap,
        "task_claimed": task_c,
        "lesson_claimed": lesson_c,
        "jjc_claimed": jjc_c,
        "group_claimed": group_c,
        "free_buy_claimed": free_c,
        "hours_elapsed": hours,
        "snapped_at": snap.snapped_at,
        "mail_scanned_at": snap.mail_scanned_at,
    }


def snapshot_from_form(
    *,
    current_ap: int,
    mail_ap: int,
    cafe_claimable: int,
    soft_cap: int,
    cafe_cap: float,
    task_claimed: bool = False,
    lesson_claimed: bool = False,
    jjc_claimed: bool = False,
    group_claimed: bool = False,
    free_buy_claimed: bool = False,
    mail_bags: Optional[List[Dict[str, Any]]] = None,
    now: Optional[datetime] = None,
) -> InventorySnapshot:
    now = now or datetime.now().replace(second=0, microsecond=0)
    day = server_day_start(now)
    bags = list(mail_bags or [])
    return InventorySnapshot(
        snapped_at=now.isoformat(sep=" ", timespec="seconds"),
        current_ap=int(current_ap),
        mail_ap=int(mail_ap),
        cafe_claimable=int(cafe_claimable),
        soft_cap=int(soft_cap),
        cafe_cap=float(cafe_cap),
        task_claimed=bool(task_claimed),
        lesson_claimed=bool(lesson_claimed),
        jjc_claimed=bool(jjc_claimed),
        group_claimed=bool(group_claimed),
        free_buy_claimed=bool(free_buy_claimed),
        claimed_day_start=day.isoformat(sep=" ", timespec="seconds"),
        mail_bags=bags,
        mail_scanned_at=now.isoformat(sep=" ", timespec="seconds") if bags else "",
    )
