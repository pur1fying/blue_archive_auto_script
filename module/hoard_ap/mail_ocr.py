"""邮箱限时体力 OCR / 解析。

在邮箱界面识别：
- 每条限时体力包的数量（20 / 30 / 60 / 100 / 120 …）
- 剩余时间（如 23:15:02 / 18小时 / 领取期限18小时）
- 是否库存已满提示（仅日志）

结果写入 inventory.mail_bags + 总量 mail_ap。
纯函数 parse 不依赖设备；scan_mail_ap 需要运行中的 baas self。
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class MailBagScan:
    amount: int
    remain_hours: float
    remain_text: str = ""
    source: str = "ocr"
    # 游戏只显示「不到1小时」时为 True；精确倒计时靠 inventory 内计时
    under_1h: bool = False
    # 粗粒度：仅知道 ≥N 小时（如「18小时」），用于决定 10 分钟巡检
    coarse_hours: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# 常见体力包面额；也接受 1~999 的其它数
_KNOWN_AMOUNTS = {10, 20, 30, 40, 50, 60, 80, 90, 100, 120, 150, 200, 240, 300, 360}

_AMOUNT_PATTERNS = [
    re.compile(r"(?:行动力|体力|AP)\s*[×xX+]?\s*(\d{1,3})", re.I),
    re.compile(r"[×xX]\s*(\d{1,3})"),
    re.compile(r"(\d{2,3})\s*(?:行动力|体力)"),
    re.compile(r"(?<![0-9.,])(20|30|40|50|60|80|90|100|120|150|200|240|300|360)(?![0-9])"),
    re.compile(r"(?<![0-9.,/])(\d{1,3})(?![0-9.,/])"),
]

_TIME_PATTERNS = [
    # 23:15:02 or 23:15
    re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?::(\d{2}))?"),
    # 领取期限18小时 / 剩余18时 / 18小时
    re.compile(r"(?:领取期限|剩余)?\s*(\d{1,2})\s*小?时"),
    re.compile(r"(\d{1,2})\s*h\b", re.I),
]

# 顶栏杂讯：体力/钻石/邮箱计数，不当成包
_NOISE_LINE = re.compile(
    r"(邮箱|未领取|领取记录|来自|收信日期|收件日期|一键领取|道具|降序|"
    r"库存已满|最多可保存|一次最多|阿洛娜|邮件将会|领取期限)"
)


def _parse_remain_hours(text: str) -> Tuple[float, str, bool, bool]:
    """返回 (hours, matched_text, under_1h, coarse_hours)。

    国服邮箱常见：
    - 「不到1小时 / 不足1小时 / 1小时以内」→ under_1h=True，hours 记 0.99（仅占位）
    - 「18小时 / 领取期限18小时」→ coarse，只有整点
    - 少数服有 HH:MM:SS → 精确，coarse=False
    """
    if not text:
        return -1.0, "", False, False
    t = text.replace("：", ":")
    # 「不到1小时」族
    m = re.search(
        r"(不到\s*1\s*小?时|不足\s*1\s*小?时|1\s*小?时\s*以?内|少于\s*1\s*小?时|"
        r"剩余\s*不到|未满\s*1\s*小?时|<\s*1\s*h|under\s*1\s*h)",
        t,
        re.I,
    )
    if m:
        return 0.99, m.group(0), True, False
    # 「领取期限N天 / N天」→ 按 24h*N 粗算（小组体力常见 6 天）
    m = re.search(r"(?:领取期限)?\s*(\d{1,2})\s*天", t)
    if m:
        days = int(m.group(1))
        if 1 <= days <= 30:
            return float(days * 24), m.group(0), False, True
    # 优先「领取期限N小时」
    m = re.search(r"领取期限\s*(\d{1,2})\s*小?时", t)
    if m:
        return float(m.group(1)), m.group(0), False, True
    m = _TIME_PATTERNS[0].search(t)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        ss = int(m.group(3) or 0)
        if hh <= 48 and mm < 60 and ss < 60:
            hours = hh + mm / 60.0 + ss / 3600.0
            # 有分秒 → 精确
            coarse = mm == 0 and ss == 0 and (m.group(3) is None)
            return hours, m.group(0), False, coarse
    m = re.search(r"(?:剩余)?\s*(\d{1,2})\s*小?时", t)
    if m:
        return float(m.group(1)), m.group(0), False, True
    m = _TIME_PATTERNS[2].search(t)
    if m:
        return float(m.group(1)), m.group(0), False, True
    return -1.0, "", False, False


def _parse_amount(text: str) -> int:
    if not text:
        return 0
    # 货币/非体力：40,000 信用点、金币等
    if re.search(r"信用|金币|点券|青辉石|钻石|円|萬|万|gold|credit|pyroxene|基金", text, re.I):
        return 0
    if re.search(r"\d{1,3}[,，]\d{3}", text):  # 40,000
        return 0
    # 日期/顶栏噪音
    if re.search(r"\d{4}\s*年|收信日期|收件日期|\d+\s*/\s*\d+", text):
        # 仍允许 x20
        m = re.search(r"[×xX]\s*(\d{1,3})", text)
        if m:
            v = int(m.group(1))
            if 1 <= v <= 999:
                return v
        return 0
    # x20 / ×20 优先
    m = re.search(r"[×xX]\s*(\d{1,3})", text)
    if m:
        v = int(m.group(1))
        if 1 <= v <= 999:
            return v
    # 纯数字行：常见面额；大包不认裸数字（防 40000 截断）
    if re.fullmatch(r"\d{1,3}", text.strip()):
        v = int(text.strip())
        return v if v in _KNOWN_AMOUNTS or 10 <= v <= 360 else 0
    m = re.search(r"(?:行动力|体力|AP)\s*[×xX+]?\s*(\d{1,3})", text, re.I)
    if m:
        v = int(m.group(1))
        if 10 <= v <= 999:
            return v
    for pat in _AMOUNT_PATTERNS[:-1]:  # 跳过最宽泛的末条
        m = pat.search(text)
        if not m:
            continue
        try:
            v = int(m.group(1))
        except Exception:
            continue
        if v in _KNOWN_AMOUNTS or (10 <= v <= 360):
            return v
    return 0


def _is_noise_amount_context(text: str) -> bool:
    """顶栏 999/240、2/200、钻石数等。"""
    if not text:
        return True
    if re.search(r"\d+\s*/\s*\d+", text):
        return True
    if re.search(r"\d{1,3},\d{3}", text):  # 95,019
        return True
    if _NOISE_LINE.search(text) and _parse_amount(text) <= 0:
        return True
    return False


def _normalize_ocr_payload(resp: Any) -> List[Dict[str, Any]]:
    """把 baas ocr 返回值统一成 [{text, position?}, ...]。

    baas ocr.ocr() 实际返回 response.text（JSON 字符串），常见：
      {"str_res":"...", "text_list":[{"text":"...","position":[[x,y],...]}, ...], "time":...}
    """
    items: List[Dict[str, Any]] = []

    def _from_obj(obj: Any) -> None:
        if obj is None:
            return
        if isinstance(obj, str):
            s = obj.strip()
            if not s:
                return
            # JSON 字符串
            if s.startswith("{") or s.startswith("["):
                try:
                    _from_obj(json.loads(s))
                    return
                except Exception:
                    pass
            # 整段 str_res：按行拆
            if "\n" in s:
                for ln in s.splitlines():
                    ln = ln.strip()
                    if ln:
                        items.append({"text": ln})
                return
            items.append({"text": s})
            return
        if isinstance(obj, dict):
            if "text_list" in obj and isinstance(obj["text_list"], list):
                for it in obj["text_list"]:
                    _from_obj(it)
                return
            if "str_res" in obj and isinstance(obj["str_res"], str):
                # 优先 text_list；无则用 str_res
                if not any(True for _ in []):
                    pass
            t = obj.get("text") or obj.get("rec_text") or obj.get("label")
            if t:
                pos = obj.get("position") or obj.get("box") or obj.get("points")
                items.append({"text": str(t).strip(), "position": pos})
                return
            for k in ("texts", "data", "result", "results", "lines"):
                if k in obj:
                    _from_obj(obj[k])
            if "str_res" in obj and isinstance(obj["str_res"], str) and not items:
                _from_obj(obj["str_res"])
            return
        if isinstance(obj, (list, tuple)):
            # paddle: [[box], (text, score)]
            if (
                len(obj) >= 2
                and isinstance(obj[0], (list, tuple))
                and isinstance(obj[1], (list, tuple))
                and obj[1]
            ):
                items.append({"text": str(obj[1][0]).strip(), "position": obj[0]})
                return
            if len(obj) >= 2 and isinstance(obj[1], str):
                items.append({"text": obj[1].strip(), "position": obj[0] if obj else None})
                return
            for it in obj:
                _from_obj(it)
            return

    _from_obj(resp)
    # 去空
    out = []
    for it in items:
        t = (it.get("text") or "").strip()
        if t:
            out.append({"text": t, "position": it.get("position")})
    return out


def _center_y(position: Any) -> Optional[float]:
    if not position:
        return None
    try:
        # [[x,y],...]
        if isinstance(position, (list, tuple)) and position:
            if isinstance(position[0], (list, tuple)) and len(position[0]) >= 2:
                ys = [float(p[1]) for p in position if isinstance(p, (list, tuple)) and len(p) >= 2]
                return sum(ys) / len(ys) if ys else None
            if len(position) >= 2 and isinstance(position[0], (int, float)):
                return float(position[1])
    except Exception:
        return None
    return None


def _center_x(position: Any) -> Optional[float]:
    if not position:
        return None
    try:
        if isinstance(position, (list, tuple)) and position:
            if isinstance(position[0], (list, tuple)) and len(position[0]) >= 2:
                xs = [float(p[0]) for p in position if isinstance(p, (list, tuple)) and len(p) >= 2]
                return sum(xs) / len(xs) if xs else None
            if len(position) >= 2 and isinstance(position[0], (int, float)):
                return float(position[0])
    except Exception:
        return None
    return None


def _amount_from_text(t: str) -> int:
    """从单个 OCR 文本块提取体力面额；噪音/分数/越界一律 0。"""
    if not t or _is_noise_amount_context(t) and not re.search(r"[×xX]\s*\d+", t):
        if not re.search(r"[×xX]\s*\d+", t or ""):
            # 仍允许纯数字面额
            if not re.fullmatch(r"\d{1,3}", (t or "").strip()):
                if _is_noise_amount_context(t or ""):
                    return 0
    if re.search(r"\d+\s*/\s*\d+", t):
        return 0
    a = _parse_amount(t)
    if a <= 0:
        m = re.search(r"[×xX]\s*(\d{1,3})", t)
        if m:
            a = int(m.group(1))
    if a <= 0 and re.fullmatch(r"\d{1,3}", t.strip()):
        a = int(t.strip())
    if 1 <= a <= 999:
        return a
    return 0


def _collect_amount_and_time_points(positioned: List[Dict[str, Any]]) -> tuple:
    """分别收集「面额点」与「期限点」（都带坐标）。"""
    amounts: List[Dict[str, Any]] = []
    times: List[Dict[str, Any]] = []
    for r in positioned:
        t = r["text"]
        h, ttxt, u1h, coarse = _parse_remain_hours(t)
        if h >= 0:
            times.append(
                {
                    "cy": float(r["cy"]),
                    "cx": float(r["cx"] or 0),
                    "hours": float(h),
                    "ttxt": ttxt or t,
                    "u1h": bool(u1h),
                    "coarse": bool(coarse),
                    "used": False,
                }
            )
        a = _amount_from_text(t)
        if a > 0:
            # 右侧更像面额图标旁数字
            amounts.append(
                {
                    "cy": float(r["cy"]),
                    "cx": float(r["cx"] or 0),
                    "amount": int(a),
                    "used": False,
                }
            )
    return amounts, times


def _merge_same_row_amounts(amounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """同一行多个数字：优先保留更像体力的（10/20/30/50/60/100/120… 与大包）。

    按 y 聚 amount，同行只留一个最佳。
    """
    amounts.sort(key=lambda z: (z["cy"], z["cx"]))
    merged_amts: List[Dict[str, Any]] = []
    for a in amounts:
        if merged_amts and abs(a["cy"] - merged_amts[-1]["cy"]) <= 22:
            prev = merged_amts[-1]
            # 同行：取更靠右，且若一边是 10 一边是 50/100/30 优先大面额
            prefer_a = a["amount"]
            prefer_p = prev["amount"]
            known = {10, 20, 30, 40, 50, 60, 80, 90, 100, 120, 150, 200, 240, 300, 360}
            score_a = (2 if prefer_a in known else 0) + (1 if prefer_a >= 30 else 0) + a["cx"] / 2000.0
            score_p = (2 if prefer_p in known else 0) + (1 if prefer_p >= 30 else 0) + prev["cx"] / 2000.0
            # 50 vs 10：明显留 50
            if prefer_a >= 30 and prefer_p <= 10:
                merged_amts[-1] = a
            elif prefer_p >= 30 and prefer_a <= 10:
                pass
            elif score_a >= score_p:
                merged_amts[-1] = a
        else:
            merged_amts.append(a)
    return merged_amts


def _match_amount_time_pairs(
    amounts: List[Dict[str, Any]], times: List[Dict[str, Any]]
) -> List[MailBagScan]:
    """面额点×期限点按 y 最近一对一匹配（|dy|≤110）。"""
    bags_pos: List[MailBagScan] = []
    # 每个 amount 找最近的未用 time
    for a in sorted(amounts, key=lambda z: z["cy"]):
        best_i = -1
        best_d = 1e9
        for i, tm in enumerate(times):
            if tm["used"]:
                continue
            dy = abs(tm["cy"] - a["cy"])
            if dy < best_d:
                best_d = dy
                best_i = i
        if best_i < 0 or best_d > 110:
            continue
        tm = times[best_i]
        tm["used"] = True
        a["used"] = True
        bags_pos.append(
            MailBagScan(
                amount=int(a["amount"]),
                remain_hours=float(tm["hours"]),
                remain_text=str(tm["ttxt"]),
                under_1h=bool(tm["u1h"]),
                coarse_hours=bool(tm["coarse"] or (tm["hours"] >= 1 and ":" not in str(tm["ttxt"]))),
            )
        )

    # 未匹配的 time：向下/上找未用 amount
    for tm in times:
        if tm["used"]:
            continue
        best_i = -1
        best_d = 1e9
        for i, a in enumerate(amounts):
            if a.get("used"):
                continue
            dy = abs(tm["cy"] - a["cy"])
            if dy < best_d:
                best_d = dy
                best_i = i
        if best_i < 0 or best_d > 110:
            continue
        a = amounts[best_i]
        a["used"] = True
        tm["used"] = True
        bags_pos.append(
            MailBagScan(
                amount=int(a["amount"]),
                remain_hours=float(tm["hours"]),
                remain_text=str(tm["ttxt"]),
                under_1h=bool(tm["u1h"]),
                coarse_hours=bool(tm["coarse"]),
            )
        )
    return bags_pos


def _parse_bags_by_position(positioned: List[Dict[str, Any]]) -> List[MailBagScan]:
    """有坐标路径：收集 → 同行合并 → 一对一匹配 → 去重。"""
    amounts, times = _collect_amount_and_time_points(positioned)
    amounts = _merge_same_row_amounts(amounts)
    bags_pos = _match_amount_time_pairs(amounts, times)
    if bags_pos:
        return _dedupe_bags(bags_pos)
    return []


def _parse_bags_by_sequence(rows: List[Dict[str, Any]]) -> List[MailBagScan]:
    """无坐标 / 坐标失败：顺序扫描文本行配对 面额×期限。"""
    bags: List[MailBagScan] = []
    texts = [r["text"] for r in rows]
    if len(texts) == 1 and len(texts[0]) > 80:
        nested = _normalize_ocr_payload(texts[0])
        if len(nested) > 1:
            return parse_mail_ocr_items(nested)

    used = set()
    for i, line in enumerate(texts):
        if i in used:
            continue
        hours, ttxt, _u1h, _coarse = _parse_remain_hours(line)
        amount = _amount_from_text(line)
        if amount > 0 and hours >= 0:
            bags.append(
                MailBagScan(
                    amount=amount,
                    remain_hours=hours,
                    remain_text=ttxt,
                    under_1h=bool(_u1h),
                    coarse_hours=bool(_coarse),
                )
            )
            used.add(i)
            continue
        if hours >= 0 and amount <= 0:
            for j in range(max(0, i - 2), min(len(texts), i + 4)):
                if j in used or j == i:
                    continue
                a = _amount_from_text(texts[j])
                if 1 <= a <= 999:
                    bags.append(
                        MailBagScan(
                            amount=a,
                            remain_hours=hours,
                            remain_text=ttxt,
                            under_1h=bool(_u1h),
                            coarse_hours=bool(_coarse),
                        )
                    )
                    used.add(i)
                    used.add(j)
                    break
            continue
        if amount > 0 and hours < 0:
            for j in list(range(i - 1, max(-1, i - 4), -1)) + list(
                range(i + 1, min(len(texts), i + 4))
            ):
                if j in used or j < 0:
                    continue
                h2, t2, u2, c2 = _parse_remain_hours(texts[j])
                if h2 >= 0:
                    bags.append(
                        MailBagScan(
                            amount=amount,
                            remain_hours=h2,
                            remain_text=t2,
                            under_1h=bool(u2),
                            coarse_hours=bool(c2),
                        )
                    )
                    used.add(i)
                    used.add(j)
                    break
    return _dedupe_bags(bags)


def parse_mail_ocr_items(items: Sequence[Dict[str, Any]]) -> List[MailBagScan]:
    """基于文本 + 可选坐标解析体力包。

    有坐标时：分别收集「面额点」与「期限点」，按 y 最近且一对一匹配。
    避免顶栏 50@22 被邻行 10 抢走、或 50 被读成 10。
    """
    if not items:
        return []

    rows = []
    for it in items:
        text = re.sub(r"\s+", " ", str(it.get("text") or "").strip())
        if not text:
            continue
        cy = _center_y(it.get("position"))
        cx = _center_x(it.get("position"))
        rows.append({"text": text, "cy": cy, "cx": cx})

    positioned = [r for r in rows if r["cy"] is not None]

    if len(positioned) >= max(3, len(rows) // 3):
        bags_pos = _parse_bags_by_position(positioned)
        if bags_pos:
            return bags_pos

    # ---- 无坐标 / 坐标失败：顺序扫描 ----
    return _parse_bags_by_sequence(rows)


def parse_mail_ocr_lines(lines: List[str]) -> List[MailBagScan]:
    """兼容旧接口：纯文本行列表。"""
    items = []
    for ln in lines or []:
        items.extend(_normalize_ocr_payload(ln))
    if not items:
        items = [{"text": str(ln)} for ln in (lines or []) if str(ln).strip()]
    return parse_mail_ocr_items(items)


def _dedupe_bags(bags: List[MailBagScan]) -> List[MailBagScan]:
    """多页滑动重叠去重。

    关键：小包（<200）可以有多封同面额（两个 50、两个 10）。
    - 小包：仅当剩余时间差 <0.4h 才合并（同页重复 OCR）
    - 大包（≥200，咖啡溢出）：时间差 ≤2h 或同面额只留 1 个
    - 禁止把 22h 与 23h 的小包并成一封，也禁止把两封真·50 并成一封
    """
    raw = [b for b in bags if b.amount > 0 and b.remain_hours >= 0]
    if not raw:
        return []

    out: List[MailBagScan] = []
    for b in sorted(raw, key=lambda x: (x.amount, x.remain_hours)):
        merged = False
        for i, o in enumerate(out):
            if o.amount != b.amount:
                continue
            rh_diff = abs(float(o.remain_hours) - float(b.remain_hours))
            if b.amount >= 200:
                # 大包：滑页重叠
                if rh_diff <= 2.0:
                    if b.remain_hours < o.remain_hours:
                        out[i] = b
                    merged = True
                    break
            else:
                # 小包：只去几乎同一时刻的重复识别
                if rh_diff < 0.4:
                    if b.remain_hours < o.remain_hours:
                        out[i] = b
                    merged = True
                    break
        if not merged:
            out.append(b)

    # 大包同面额最终只留 remain 最短 1 个
    by_amt: Dict[int, List[int]] = {}
    for i, b in enumerate(out):
        by_amt.setdefault(int(b.amount), []).append(i)
    drop = set()
    for amt, idxs in by_amt.items():
        if amt < 200 or len(idxs) <= 1:
            continue
        best = min(idxs, key=lambda i: out[i].remain_hours)
        for i in idxs:
            if i != best:
                drop.add(i)
    if drop:
        out = [b for i, b in enumerate(out) if i not in drop]
    return out


def detect_inventory_full(lines: List[str]) -> bool:
    text = " ".join(lines or [])
    keys = ("库存已满", "邮箱已满", "无法领取", "空间不足", "道具已满")
    return any(k in text for k in keys)


def bags_total(bags: List[MailBagScan]) -> int:
    return sum(b.amount for b in bags)


def _ocr_page(self, img) -> List[Dict[str, Any]]:
    """单页 OCR → items。

    全图 OCR + 顶部分带补扫合并：顶栏第一封（50/10）常被全图漏掉。
    """
    ocr = getattr(self, "ocr", None)
    lang = getattr(self, "ocr_language", None) or "zh-cn"
    if ocr is None or img is None:
        return []
    items: List[Dict[str, Any]] = []
    try:
        if hasattr(ocr, "ocr"):
            resp = ocr.ocr(lang, img, None, 1)
            items = list(_normalize_ocr_payload(resp) or [])
        # 无论全图是否有结果，都补扫列表上半区（顶栏第一封）
        if hasattr(ocr, "ocr_for_single_line"):
            h = int(getattr(img, "shape", [720])[0] or 720)
            w = int(getattr(img, "shape", [720, 1280])[1] or 1280)
            regions = []
            # 顶部密集：40~360
            y = 40
            while y < min(h - 80, 420):
                regions.append((y, 12, min(y + 95, h - 30), w - 12))
                y += 48
            # 中下较疏
            while y < h - 80:
                regions.append((y, 16, min(y + 110, h - 30), w - 16))
                y += 70
            seen_t = set(str(it.get("text") or "") for it in items)
            for (y1, x1, y2, x2) in regions:
                try:
                    crop = img[y1:y2, x1:x2]
                    r = ocr.ocr_for_single_line(
                        lang, crop, None, "", 0, None, getattr(self, "logger", None)
                    )
                    t = _single_line_text(r)
                    if t and t not in seen_t:
                        seen_t.add(t)
                        items.append(
                            {
                                "text": t,
                                "position": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                            }
                        )
                except Exception:
                    continue
    except Exception as e:
        try:
            self.logger.warning("[囤体] 邮箱OCR单页失败: %s" % e)
        except Exception:
            pass
    return items


def _swipe_mail_list(self) -> None:
    """邮箱列表上滑一页（露出更多邮件）。"""
    try:
        # 列表中部上滑
        if hasattr(self, "swipe"):
            self.swipe(640, 520, 640, 220, duration=0.35, post_sleep_time=0.55)
            return
    except Exception:
        pass
    try:
        if hasattr(self, "u2_swipe"):
            self.u2_swipe(640, 520, 640, 220, duration=0.35, post_sleep_time=0.55)
            return
    except Exception:
        pass
    try:
        ctrl = getattr(self, "control", None)
        if ctrl is not None and hasattr(ctrl, "swipe"):
            ctrl.swipe(640, 520, 640, 220)
            time.sleep(0.55)
    except Exception:
        pass


def _back_to_main(self) -> None:
    try:
        if hasattr(self, "to_main_page"):
            self.to_main_page()
            return
    except Exception:
        pass
    # 右上角关闭
    try:
        self.click(1236, 39, wait_over=True)
        time.sleep(0.3)
    except Exception:
        pass


def scan_mail_ap(self) -> Dict[str, Any]:
    """设备侧：进邮箱 → 多页 OCR → 解析 → 回主页。"""
    result: Dict[str, Any] = {
        "ok": False,
        "bags": [],
        "total": 0,
        "inventory_full": False,
        "raw_lines": [],
        "error": "",
        "pages": 0,
    }
    try:
        from module.mail import to_mail
    except Exception as e:
        result["error"] = "import mail failed: %s" % e
        return result

    try:
        try:
            self.to_main_page()
        except Exception:
            pass
        to_mail(self)
        time.sleep(0.9)
        # 识别阶段禁止一键领取。顶栏第一封进邮箱就在最上，不要下拉/上滑打乱。

        all_items: List[Dict[str, Any]] = []
        all_texts: List[str] = []
        page_bag_lists: List[List[MailBagScan]] = []
        max_pages = 6
        stable = 0
        prev_sig = ""
        prev_unique_n = 0
        no_growth = 0

        for page in range(max_pages):
            try:
                self.latest_img_array = self.get_screenshot_array()
            except Exception:
                pass
            img = getattr(self, "latest_img_array", None)
            if img is None:
                result["error"] = "no screenshot"
                break
            items = _ocr_page(self, img)
            result["pages"] = page + 1
            for it in items:
                t = it.get("text") or ""
                if t:
                    all_texts.append(t)
                # 标注页码，避免跨页坐标糊在一起时丢顶栏包
                it2 = dict(it)
                it2["_page"] = page
                all_items.append(it2)
            # 每页独立解析，再总去重——比「全量 items 一次 parse」更不容易吞顶栏
            page_bags = parse_mail_ocr_items(items)
            page_bag_lists.append(list(page_bags))
            sig = "|".join("%s@%.1f" % (b.amount, b.remain_hours) for b in page_bags)
            if sig and sig == prev_sig:
                stable += 1
            else:
                stable = 0
            prev_sig = sig or prev_sig
            merged_so_far: List[MailBagScan] = []
            for pb in page_bag_lists:
                merged_so_far.extend(pb)
            uniq_now = _dedupe_bags(merged_so_far)
            grew = len(uniq_now) > prev_unique_n
            if (not grew) and page > 0:
                no_growth += 1
            else:
                no_growth = 0
            prev_unique_n = max(prev_unique_n, len(uniq_now))
            # 连续两页完全相同，或连续两页去重后不增长 → 停
            if stable >= 2 and page > 0:
                break
            if no_growth >= 2 and page > 0:
                break
            if page >= max_pages - 1:
                break
            # 首页就一个都没有：仍滑一次（可能 OCR 失败）；之后空页停
            if page > 0 and not page_bags and no_growth >= 1:
                break
            _swipe_mail_list(self)
            time.sleep(0.45)

        # 优先：分页解析合并；失败再全量 / 纯文本
        bags: List[MailBagScan] = []
        for pb in page_bag_lists:
            bags.extend(pb)
        bags = _dedupe_bags(bags)
        if not bags:
            bags = parse_mail_ocr_items(all_items)
        if not bags:
            bags = parse_mail_ocr_lines(all_texts)
        bags = _mark_under_1h_flags(bags)
        # 过滤：无剩余时间的「面额」多半是货币误识
        bags = [b for b in bags if b.amount > 0 and b.remain_hours >= 0]
        # 单包 >360 且无期限文案的丢掉
        bags = [
            b for b in bags
            if b.amount <= 360 or (b.remain_text and b.amount <= 999)
        ]

        result["raw_lines"] = all_texts[:80]
        result["inventory_full"] = detect_inventory_full(all_texts)
        result["bags"] = [b.to_dict() for b in bags]
        result["total"] = bags_total(bags)
        result["ok"] = True
        try:
            self.logger.info(
                "[囤体] 邮箱OCR total=%s bags=%s pages=%s full=%s sample=%s"
                % (
                    result["total"],
                    len(bags),
                    result["pages"],
                    result["inventory_full"],
                    [b.to_dict() for b in bags[:8]],
                )
            )
        except Exception:
            pass
        return result
    except Exception as e:
        result["error"] = str(e)
        return result
    finally:
        # 无论成败都尽量回主页，避免停在邮箱
        try:
            _back_to_main(self)
        except Exception:
            pass


def _extract_texts(resp: Any) -> List[str]:
    """兼容旧调用。"""
    return [it["text"] for it in _normalize_ocr_payload(resp) if it.get("text")]


def _single_line_text(resp: Any) -> str:
    if resp is None:
        return ""
    if isinstance(resp, str):
        s = resp.strip()
        if s.startswith("{") or s.startswith("["):
            items = _normalize_ocr_payload(s)
            return items[0]["text"] if items else s
        return s
    items = _normalize_ocr_payload(resp)
    return items[0]["text"] if items else ""



def _mark_under_1h_flags(bags: List[MailBagScan]) -> List[MailBagScan]:
    for b in bags:
        t = str(b.remain_text or "")
        if re.search(r"不到|不足|以内|未满|少于", t):
            b.under_1h = True
            if b.remain_hours < 0 or b.remain_hours > 1.0:
                b.remain_hours = 0.99
        elif b.remain_hours >= 0 and b.remain_hours <= 1.0 and (":" not in t):
            # 「1小时」整点也可能快进不到1h，不强制
            pass
        # 纯「N小时」无冒号 → coarse
        if re.search(r"\d+\s*小?时", t) and ":" not in t and not b.under_1h:
            b.coarse_hours = True
    return bags

def apply_scan_to_inventory(config_dir: str, scan: Dict[str, Any]) -> int:
    """把扫描结果写入 inventory（明细+总量），返回 total。

    保护规则（审计修复）：
    - 零识别（bags 为空）绝不覆盖台账，尤其不能清空人工明细，原样返回当前总量；
    - 人工明细（source=manual）优先：同面额包以人工纠正值为准，识别结果只
      替换旧的识别来源明细，不会悄悄丢掉用户手改的条目。
    """
    from module.hoard_ap.inventory import load_inventory, save_inventory, merge_mail_bags_with_timer
    import json
    import os

    inv = load_inventory(config_dir)
    old_bags = list(inv.mail_bags or [])
    old_total = int(inv.mail_ap or 0) or sum(
        int(b.get("amount") or 0) for b in old_bags
    )

    bags = scan.get("bags") or []
    norm = []
    for b in bags:
        if hasattr(b, "to_dict"):
            d = b.to_dict()
        elif isinstance(b, dict):
            d = dict(b)
        else:
            continue
        # 默认主堆囤货：剩余 ≥2h 或大包，禁止被临期 0.2h 误领
        try:
            rh = float(d.get("remain_hours") if d.get("remain_hours") is not None else -1)
        except Exception:
            rh = -1.0
        amt = int(d.get("amount") or 0)
        if not d.get("role"):
            if rh >= 2.0 or (amt >= 200 and rh >= 1.0):
                d["role"] = "stack_for_claim"
        # 识别来源标记：只有人工明细受覆盖保护
        d.setdefault("source", "ocr")
        norm.append(d)

    if not norm:
        # 零识别：页面打开≠识别可信。不动台账，返回当前总量。
        return int(old_total)

    manual_old = [
        dict(b) for b in old_bags if str(b.get("source") or "") == "manual"
    ]
    old_ocr = [b for b in old_bags if str(b.get("source") or "") != "manual"]

    # 识别结果只替换旧的识别来源明细；仅合并 under_1h 计时锚点
    merged = merge_mail_bags_with_timer(old_ocr, norm)
    # 若 merge 因面额对不齐丢包，回退本次 norm
    if sum(int(b.get("amount") or 0) for b in merged) <= 0:
        merged = list(norm)
    if len(merged) < len(norm):
        # 优先保留本次识别全量
        merged = list(norm)

    # 人工明细优先：扫描到的包若能对上人工纠正包（同面额，或剩余时间
    # 接近——用户改面额后面额对不上，只能靠时间近似配对），信任人工版本，
    # 避免同一包既按人工值又按识别值双算。
    def _same_bag(mb: Dict[str, Any], sb: Dict[str, Any]) -> bool:
        try:
            ma = int(mb.get("amount") or 0)
        except Exception:
            ma = 0
        try:
            sa = int(sb.get("amount") or 0)
        except Exception:
            sa = 0
        try:
            mr = float(mb.get("remain_hours") if mb.get("remain_hours") is not None else -1)
        except Exception:
            mr = -1.0
        try:
            sr = float(sb.get("remain_hours") if sb.get("remain_hours") is not None else -1)
        except Exception:
            sr = -1.0
        # 面额相等还需剩余时间接近（≤0.4h）或都未知才判同包，
        # 避免两封剩余时间不同的同面额邮件被误并为 1 封
        if ma > 0 and ma == sa:
            if mr < 0 and sr < 0:
                return True
            if 0 <= mr < 48 and 0 <= sr < 48 and abs(mr - sr) <= 0.4:
                return True
            return False
        # 面额不等但剩余时间接近（用户改面额后对不上，靠时间近似配对）
        return 0 <= mr < 48 and 0 <= sr < 48 and abs(mr - sr) <= 1.5

    out: List[Dict[str, Any]] = []
    pool = list(merged)
    for mb in manual_old:
        for i, b in enumerate(pool):
            if _same_bag(mb, b):
                pool.pop(i)
                break
        mb.setdefault("source", "manual")
        out.append(mb)
    out.extend(pool)

    total = sum(int(b.get("amount") or 0) for b in out)
    if total <= 0:
        total = int(scan.get("total") or 0)
    inv.mail_ap = int(total)
    inv.mail_bags = list(out)
    inv.mail_scanned_at = datetime.now().isoformat(sep=" ", timespec="seconds")
    if not inv.snapped_at:
        inv.snapped_at = inv.mail_scanned_at
    save_inventory(config_dir, inv)
    # 同步一份到 config 旁路，供表单/计划读
    try:
        side = os.path.join(config_dir or ".", "hoard_ap_mail_last_scan.json")
        with open(side, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total": int(total),
                    "bags": out,
                    "scanned_at": inv.mail_scanned_at,
                    "manual_kept": len(manual_old),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception:
        pass
    return int(total)
