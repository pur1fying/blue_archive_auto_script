# -*- coding: utf-8 -*-
"""神名文字（SecretStone）刷取计算。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# 升星 / 专武 相邻阶碎片消耗（5星 = 专1）
# rank 序列：S1 S2 S3 S4 S5(=Z1) Z2 Z3 Z4
RANK_ORDER = ["S1", "S2", "S3", "S4", "S5", "Z2", "Z3", "Z4"]
COST_EDGE = {
    ("S1", "S2"): 30,
    ("S2", "S3"): 80,
    ("S3", "S4"): 100,
    ("S4", "S5"): 120,  # 4→5星（=专1）
    ("S5", "Z2"): 120,  # 专1→专2
    ("Z2", "Z3"): 180,
    ("Z3", "Z4"): 200,
}

COST_HELP_CN = (
    "1星升到2星：30碎。2星升到3星：80碎。3星升到4星：100碎。4星升到5星：120碎。"
    "专1升到专2：120碎。专2升到专3：180碎。专3升到专4：200碎。"
)


def load_secretstone_table(path: Optional[str] = None) -> Dict[str, Any]:
    if path:
        p = Path(path)
    else:
        p = Path(__file__).resolve().parent / "data" / "secretstone_stages_cn.json"
    return json.loads(p.read_text(encoding="utf-8"))


def normalize_punct(text: str) -> str:
    s = str(text or "")
    table = str.maketrans(
        {
            "，": ",",
            "；": ";",
            "：": ":",
            "（": "(",
            "）": ")",
            "－": "-",
            "—": "-",
            "–": "-",
            "　": " ",
        }
    )
    return s.translate(table)


def _parse_rank_token(tok: str) -> Optional[str]:
    """'3' / 'Z3' / 'z4' / '专3' / 'S5' → 规范 rank。"""
    t = str(tok or "").strip().upper().replace(" ", "")
    if not t:
        return None
    t = t.replace("专武", "Z").replace("专", "Z")
    if t.startswith("S") and t[1:].isdigit():
        n = int(t[1:])
        if 1 <= n <= 5:
            return f"S{n}"
        return None
    if t.startswith("Z") and t[1:].isdigit():
        n = int(t[1:])
        if n == 1:
            return "S5"  # 专1 = 5星
        if 2 <= n <= 4:
            return f"Z{n}"
        return None
    if t.isdigit():
        n = int(t)
        if 1 <= n <= 5:
            return f"S{n}"
        return None
    return None


def rank_index(rank: str) -> int:
    try:
        return RANK_ORDER.index(rank)
    except ValueError:
        return -1


def fragments_needed(cur: str, goal: str) -> int:
    """从 cur 升到 goal 所需碎片（不含已有）。goal 必须 >= cur。"""
    i = rank_index(cur)
    j = rank_index(goal)
    if i < 0 or j < 0 or j <= i:
        return 0
    total = 0
    for k in range(i, j):
        a, b = RANK_ORDER[k], RANK_ORDER[k + 1]
        total += int(COST_EDGE.get((a, b), 0))
    return total


def parse_student_spec(chunk: str) -> Optional[Dict[str, Any]]:
    """单段：学生名字,当前-目标,已有碎片
    例：星野,3-Z4,1  /  白子,Z2-Z4,50  /  优香,2-5,0
    """
    raw = normalize_punct(chunk).strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) < 2:
        return None
    name = parts[0]
    if not name:
        return None
    rng = parts[1]
    owned = 0
    if len(parts) >= 3 and parts[2] != "":
        try:
            owned = max(0, int(float(parts[2])))
        except Exception:
            owned = 0
    if "-" not in rng:
        return None
    left, right = rng.split("-", 1)
    cur = _parse_rank_token(left)
    goal = _parse_rank_token(right)
    if not cur or not goal:
        return None
    if rank_index(goal) < rank_index(cur):
        cur, goal = goal, cur
    need_raw = fragments_needed(cur, goal)
    need = max(0, need_raw - owned)
    return {
        "name": name,
        "cur": cur,
        "goal": goal,
        "owned": owned,
        "need_raw": need_raw,
        "need": need,
        "raw": raw,
    }


def parse_student_list(text: str) -> List[Dict[str, Any]]:
    s = normalize_punct(text)
    # 学生之间 ;
    chunks = re.split(r"[;]+", s)
    out: List[Dict[str, Any]] = []
    for ch in chunks:
        spec = parse_student_spec(ch)
        if spec:
            out.append(spec)
    return out


def all_students(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    """stones 里全部学生（去重保序）。"""
    seen = set()
    out = []
    for st in table.get("stones") or []:
        name = str(st.get("student_name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(
            {
                "name": name,
                "student_id": st.get("student_id"),
                "stone_key": st.get("id"),
                "stone_name": st.get("name"),
                "path": st.get("student_path") or "",
            }
        )
    return out


def match_students(table: Dict[str, Any], query: str, *, limit: int = 40) -> List[Dict[str, Any]]:
    """单字/多字：整段作为子串匹配学生名（区分大小写无关的拉丁，中文直接包含）。"""
    q = str(query or "").strip()
    students = all_students(table)
    if not q:
        return students[:limit]
    q_l = q.lower()
    hits = []
    for s in students:
        name = s["name"]
        if q in name or q_l in name.lower():
            hits.append(s)
    # 单字命中很多时仍全返回（截断 limit）
    return hits[:limit]


def stages_for_student(table: Dict[str, Any], student_name: str) -> List[Dict[str, Any]]:
    name = str(student_name or "").strip()
    out = []
    for st in table.get("stages") or []:
        for fd in st.get("fixed_drops") or []:
            if str(fd.get("student_name") or "") != name:
                continue
            out.append(
                {
                    "stage_id": st.get("id"),
                    "apply_token": st.get("apply_token") or (str(st.get("id")) + "-"),
                    "name": st.get("name") or st.get("id"),
                    "ap_cost": int(st.get("ap_cost") or 20),
                    "chance": float(fd.get("chance") or 0.4),
                    "expected": float(fd.get("expected") or fd.get("chance") or 0.4),
                    "amount": float(fd.get("amount") or 1),
                    "stone_key": fd.get("stone_key"),
                    "difficulty": st.get("difficulty") or "hard",
                }
            )
            break
    # 稳定排序：area/stage
    def sk(x):
        sid = str(x.get("stage_id") or "")
        m = re.match(r"h?(\d+)-(\d+)", sid)
        if m:
            return (int(m.group(1)), int(m.group(2)), sid)
        return (999, 999, sid)

    out.sort(key=sk)
    return out


def build_apply_text(stages: Sequence[Dict[str, Any]], *, default_runs: int = 3) -> str:
    parts = []
    for st in stages:
        tok = str(st.get("apply_token") or "")
        if not tok.endswith("-"):
            tok = tok + "-"
        parts.append(f"{tok}{int(default_runs)}")
    return ",".join(parts)



def students_with_mainline(table: Dict[str, Any]) -> set:
    """有主线困难掉落的学生名集合。"""
    names = set()
    for st in table.get("stages") or []:
        for fd in st.get("fixed_drops") or []:
            n = str(fd.get("student_name") or "").strip()
            if n:
                names.add(n)
    return names


def match_students_smart(
    table: Dict[str, Any],
    query: str,
    *,
    limit: int = 40,
) -> List[Dict[str, Any]]:
    """默认只列有主线掉落者；精确命中无掉落名时单独标出。"""
    q = str(query or "").strip()
    if not q:
        return []
    with_drop = students_with_mainline(table)
    all_s = all_students(table)
    q_l = q.lower()
    hits_drop = []
    hits_none = []
    for s in all_s:
        name = s["name"]
        if q not in name and q_l not in name.lower():
            continue
        row = dict(s)
        if name in with_drop:
            row["has_drop"] = True
            hits_drop.append(row)
        else:
            row["has_drop"] = False
            hits_none.append(row)
    return (hits_drop + hits_none)[:limit]


def format_stone_plan_text(
    *,
    name: str,
    need: int,
    stages: Sequence[Dict[str, Any]],
    drop_mult: float,
    runs_all: int,
    n_stages: int,
    best_daily: float,
    act2: int,
    act3: int,
    detailed: bool = False,
) -> str:
    """神名结果：紧凑版（倍率改这里）。"""
    lines = []
    lines.append(f"【{name}】还需 {need} 碎")
    if not stages:
        lines.append("  主线困难暂无该学生掉落。")
        return "\n".join(lines)
    for s in stages:
        sid = s.get("stage_id") or s.get("id") or "?"
        if detailed:
            lines.append(
                f"  · {sid}  "
                f"{float(s.get('chance') or 0)*100:.0f}% / 次  "
                f"期望 {float(s.get('expected') or 0):.2f} 碎"
            )
        else:
            lines.append(f"  · {sid}")
    mult_txt = f"{float(drop_mult):g}倍"
    if need <= 0:
        lines.append("碎片已够，无需再刷。")
    elif runs_all < 0:
        lines.append("无法估算次数（掉落期望为 0）。")
    else:
        act_tail = ""
        if act2 is not None and int(act2) >= 0:
            act_tail = (
                f"若不重置，约需要 {act2} 个 2 倍活动或 {act3} 个 3 倍活动。"
            )
        lines.append(
            f"当前 {mult_txt} 下，单图每天满次数约 {best_daily:.2f} 碎。"
            f"总需刷约{runs_all}次 x {max(1, int(n_stages))}。"
            + act_tail
        )
    return "\n".join(lines)


def estimate_student_plan(
    table: Dict[str, Any],
    spec: Dict[str, Any],
    *,
    default_runs: int = 3,
    drop_mult: float = 1.0,
) -> Dict[str, Any]:
    """单名学生：关卡列表 + 期望刷次 + 活动估算。"""
    name = spec["name"]
    stages = stages_for_student(table, name)
    need = int(spec.get("need") or 0)
    drop_mult = max(0.01, float(drop_mult or 1.0))

    exp_per_cycle = sum(float(s.get("expected") or 0) for s in stages) * drop_mult
    best = None
    for s in stages:
        e = float(s.get("expected") or 0) * drop_mult
        ap = max(1, int(s.get("ap_cost") or 20))
        score = e / ap if ap else 0
        if best is None or score > best[0]:
            best = (score, s, e)

    runs_all = 0
    if need <= 0:
        runs_all = 0
    elif exp_per_cycle <= 0:
        runs_all = -1
    else:
        import math
        runs_all = int(math.ceil(need / exp_per_cycle))

    apply_text = build_apply_text(stages, default_runs=default_runs)

    per_stage_event_runs = 9
    n_stages = max(1, len(stages))

    def activities_for_mult(m: float) -> int:
        if need <= 0:
            return 0
        if not stages:
            return -1
        import math
        exp_one_event = 0.0
        for s in stages:
            exp_one_event += float(s.get("expected") or 0) * m * per_stage_event_runs
        if exp_one_event <= 0:
            return -1
        return int(math.ceil(need / exp_one_event))

    act2 = activities_for_mult(2.0)
    act3 = activities_for_mult(3.0)
    import math
    act2_reset = int(math.ceil(act2 / 2)) if act2 > 0 else act2
    act3_reset = int(math.ceil(act3 / 2)) if act3 > 0 else act3

    daily_full = 3
    best_daily = 0.0
    if best:
        best_daily = float(best[2]) * daily_full
    elif stages:
        best_daily = (
            max(float(s.get("expected") or 0) for s in stages) * drop_mult * daily_full
        )

    copy_text = format_stone_plan_text(
        name=name,
        need=need,
        stages=stages,
        drop_mult=drop_mult,
        runs_all=runs_all,
        n_stages=n_stages,
        best_daily=best_daily,
        act2=act2,
        act3=act3,
        detailed=False,
    )
    copy_text_detailed = format_stone_plan_text(
        name=name,
        need=need,
        stages=stages,
        drop_mult=drop_mult,
        runs_all=runs_all,
        n_stages=n_stages,
        best_daily=best_daily,
        act2=act2,
        act3=act3,
        detailed=True,
    )

    return {
        "spec": spec,
        "stages": stages,
        "need": need,
        "apply_text": apply_text,
        "runs_per_stage": runs_all,
        "exp_per_cycle": exp_per_cycle,
        "activities_2x": act2,
        "activities_3x": act3,
        "activities_2x_reset": act2_reset,
        "activities_3x_reset": act3_reset,
        "best_daily": best_daily,
        "copy_text": copy_text,
        "copy_text_detailed": copy_text_detailed,
    }



def plan_many(
    table: Dict[str, Any],
    text: str,
    *,
    default_runs: int = 3,
    drop_mult: float = 1.0,
) -> Dict[str, Any]:
    specs = parse_student_list(text)
    plans = [
        estimate_student_plan(table, sp, default_runs=default_runs, drop_mult=drop_mult)
        for sp in specs
    ]
    # 合并 apply：同关次数取 max
    from collections import OrderedDict

    merged: "OrderedDict[str, int]" = OrderedDict()
    for p in plans:
        for st in p.get("stages") or []:
            sid = str(st.get("stage_id") or "")
            tok = str(st.get("apply_token") or (sid + "-"))
            if not tok.endswith("-"):
                tok += "-"
            key = tok  # h7-3-
            # default_runs 或 runs_per_stage
            r = int(p.get("runs_per_stage") or default_runs)
            if r < 0:
                r = default_runs
            if r == 0:
                r = default_runs
            # 展示默认 3，估算次数另外写在文案；apply 用 default_runs 更符合「默认 3 次」
            r_use = int(default_runs)
            prev = merged.get(key, 0)
            merged[key] = max(prev, r_use)
    apply_parts = [f"{k}{v}" for k, v in merged.items()]
    apply_text = ",".join(apply_parts)
    blocks = [p.get("copy_text") or "" for p in plans]
    blocks_d = [
        p.get("copy_text_detailed") or p.get("copy_text") or "" for p in plans
    ]
    if not blocks:
        msg = (
            "还没有可解析的学生。格式：学生名字,当前-目标,已有碎片\n"
            "例：星野,3-Z4,1\n多学生用 ; 分隔。\n" + COST_HELP_CN
        )
        blocks = [msg]
        blocks_d = [msg]
    sep = "\n\n"
    return {
        "plans": plans,
        "apply_text": apply_text,
        "copy_text": sep.join(blocks),
        "copy_text_detailed": sep.join(blocks_d),
        "specs": specs,
    }
