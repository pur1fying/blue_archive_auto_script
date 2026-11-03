# -*- coding: utf-8 -*-
"""装备刷图纯函数计算器（不碰调度 / 设备）。支持 Schale v2 掉落表。"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# 页面展示顺序（用户指定）
SLOT_UI_ORDER: List[Tuple[str, str]] = [
    ("necklace", "项链"),
    ("watch", "手表"),
    ("charm", "护身符"),
    ("hairpin", "发夹"),
    ("badge", "徽章"),
    ("bag", "背包"),
    ("shoes", "鞋子"),
    ("gloves", "手套"),
    ("hat", "帽子"),
]

SLOT_CN = {k: v for k, v in SLOT_UI_ORDER}
SLOT_CN.update(
    {
        "hairpin": "发夹",  # 数据里也可能是发带
        "watch": "手表",
        "bag": "背包",
    }
)

NeedKey = Tuple[str, int]  # (slot, tier)


def load_stage_table(path: Optional[str] = None) -> Dict[str, Any]:
    if path:
        p = Path(path)
    else:
        p = Path(__file__).resolve().parent / "data" / "equip_stages_cn.json"
    return json.loads(p.read_text(encoding="utf-8"))


def equip_index(table: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {e["id"]: e for e in table.get("equips") or [] if e.get("id")}


def parse_tier_list(text: str) -> List[int]:
    """'9,8' / '9，8' / '9 8' → [9, 8]（去重保序，仅 1–20）。"""
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r"[,，\s/、]+", raw)
    out: List[int] = []
    seen = set()
    for p in parts:
        p = p.strip().upper().lstrip("TｔT")
        if not p:
            continue
        try:
            n = int(p)
        except ValueError:
            continue
        if n < 1 or n > 20:
            continue
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def needs_from_simple(
    slot_tiers: Dict[str, Sequence[int]],
    *,
    each: int = 1,
) -> Dict[NeedKey, int]:
    """简单模式：每个填写的 T 阶默认缺口 each 件（设计图/成品都算）。"""
    out: Dict[NeedKey, int] = {}
    for slot, tiers in (slot_tiers or {}).items():
        slot = str(slot or "").strip().lower()
        if not slot:
            continue
        for t in tiers or []:
            try:
                ti = int(t)
            except Exception:
                continue
            if ti < 1:
                continue
            key = (slot, ti)
            out[key] = int(out.get(key, 0)) + max(1, int(each))
    return out


def need_map(
    owned: Dict[str, int],
    target: Dict[str, int],
) -> Dict[str, int]:
    """兼容旧接口：缺口 = max(0, target - owned)。"""
    keys = set(owned) | set(target)
    out: Dict[str, int] = {}
    for k in keys:
        gap = int(target.get(k, 0) or 0) - int(owned.get(k, 0) or 0)
        if gap > 0:
            out[k] = gap
    return out


def _eq_meta(eq: Dict[str, Dict[str, Any]], equip_key: str) -> Optional[Dict[str, Any]]:
    info = eq.get(equip_key)
    if info:
        return info
    # 容错：有时只有 equip_id
    return None


def expected_by_slot_tier(
    stage: Dict[str, Any],
    eq: Dict[str, Dict[str, Any]],
) -> Dict[NeedKey, float]:
    """把 expected_by_equip 折成 (slot, tier) 期望（gear + blueprint 都计入该阶）。"""
    out: Dict[NeedKey, float] = {}
    exp_map = stage.get("expected_by_equip") or {}
    if not exp_map:
        # 兼容 v1 drops 权重表
        drops = stage.get("drops") or {}
        for eid, w in drops.items():
            info = eq.get(eid) or {}
            slot = str(info.get("slot") or "")
            tier = int(info.get("tier") or 0)
            if not slot or tier <= 0:
                continue
            out[(slot, tier)] = out.get((slot, tier), 0.0) + float(w or 0)
        return out

    for ek, ev in exp_map.items():
        info = _eq_meta(eq, str(ek)) or {}
        slot = str(info.get("slot") or "")
        kind = str(info.get("kind") or "")
        tier = int(info.get("tier") or 0)
        try:
            val = float(ev or 0)
        except Exception:
            val = 0.0
        if val <= 0 or not slot:
            continue
        if kind == "universal_blueprint":
            # 万能图：不计入某一固定 T，副产里单独展示
            continue
        if tier <= 0:
            continue
        if kind in ("blueprint", "gear", ""):
            key = (slot, tier)
            out[key] = out.get(key, 0.0) + val
    return out


def stage_fixed_expected_by_slot_tier(
    stage: Dict[str, Any],
    eq: Dict[str, Dict[str, Any]],
) -> Dict[NeedKey, float]:
    """仅 chance==1 的固定掉落折算（用于「确定掉落」策略加权）。"""
    out: Dict[NeedKey, float] = {}
    for row in stage.get("fixed_drops") or []:
        try:
            chance = float(row.get("chance", 1.0) or 1.0)
        except Exception:
            chance = 1.0
        if abs(chance - 1.0) > 1e-9:
            continue
        ek = str(row.get("equip_key") or "")
        info = _eq_meta(eq, ek) or {}
        slot = str(info.get("slot") or "")
        tier = int(info.get("tier") or 0)
        kind = str(info.get("kind") or "")
        if not slot or tier <= 0 or kind == "universal_blueprint":
            continue
        try:
            exp = float(row.get("expected") or 0) or (
                chance * float(row.get("amount") or 1)
            )
        except Exception:
            exp = 0.0
        if exp <= 0:
            continue
        key = (slot, tier)
        out[key] = out.get(key, 0.0) + exp
    return out


def label_need(slot: str, tier: int) -> str:
    cn = SLOT_CN.get(slot, slot)
    return f"T{tier}{cn}"


def label_equip_key(
    eq: Dict[str, Dict[str, Any]],
    ek: str,
    *,
    with_design_suffix: bool = False,
) -> str:
    """展示名：T阶+部位；万能→「部位万能」。默认不写「设计图」。"""
    info = eq.get(ek) or {}
    slot = str(info.get("slot") or "")
    tier = int(info.get("tier") or 0)
    kind = str(info.get("kind") or "")
    cn = SLOT_CN.get(slot, info.get("slot_cn") or slot or ek)
    if kind == "universal_blueprint":
        return f"{cn}万能"
    if kind == "blueprint":
        base = f"T{tier}{cn}"
        return f"{base}设计图" if with_design_suffix else base
    if tier > 0:
        return f"T{tier}{cn}"
    return str(info.get("name") or ek)


def is_universal_key(eq: Dict[str, Dict[str, Any]], ek: str) -> bool:
    info = eq.get(ek) or {}
    if str(info.get("kind") or "") == "universal_blueprint":
        return True
    return str(ek).endswith("_univ") or "万能" in str(info.get("name") or "")


def _filter_stages(
    stages: List[Dict[str, Any]],
    *,
    include_normal: bool = True,
    include_hard: bool = True,
) -> List[Dict[str, Any]]:
    out = []
    for st in stages:
        diff = str(st.get("difficulty") or "").lower()
        code = st.get("difficulty_code")
        is_hard = diff == "hard" or code == 1 or str(st.get("id") or "").startswith("h")
        if is_hard and not include_hard:
            continue
        if (not is_hard) and not include_normal:
            continue
        out.append(st)
    return out


def _normalize_needs(needs: Any, eq: Dict[str, Dict[str, Any]]) -> Dict[NeedKey, float]:
    """归一 needs → NeedKey：支持 (slot, tier) 新键与 equip_id 旧键。"""
    need_st: Dict[NeedKey, float] = {}
    if not needs:
        return need_st
    sample_key = next(iter(needs.keys()))
    if isinstance(sample_key, tuple):
        for k, v in needs.items():
            if not isinstance(k, tuple) or len(k) != 2:
                continue
            slot, tier = str(k[0]), int(k[1])
            if float(v) > 0:
                need_st[(slot, int(tier))] = float(v)
    else:
        # 旧 equip_key / 自定义 id
        for k, v in needs.items():
            if float(v or 0) <= 0:
                continue
            info = eq.get(str(k)) or {}
            slot = str(info.get("slot") or "")
            tier = int(info.get("tier") or 0)
            if slot and tier > 0:
                key = (slot, tier)
                need_st[key] = need_st.get(key, 0.0) + float(v)
            else:
                # 无法映射则跳过
                pass
    return need_st


def _tier_weight(tier: int, strategy: str) -> float:
    if strategy == "high_random":
        return 1.0 + max(0, tier - 1) * 0.55
    # 低级确定：低 T 略加权
    return 1.0 + max(0, 10 - tier) * 0.12


def _stage_score(
    st: Dict[str, Any],
    rem: Dict[NeedKey, float],
    eq: Dict[str, Dict[str, Any]],
    strategy: str,
    drop_mult: float,
) -> Tuple[float, Dict[NeedKey, float], Dict[str, float]]:
    """单关对当前缺口的得分：期望掉落×权重/体力。"""
    ap = max(1, int(st.get("ap_cost") or 10))
    per_st = expected_by_slot_tier(st, eq)
    fixed_st = stage_fixed_expected_by_slot_tier(st, eq)
    # equip_key 期望（已含表内 expected，再乘掉落倍率）
    per_ek: Dict[str, float] = {}
    for ek, ev in (st.get("expected_by_equip") or {}).items():
        try:
            per_ek[str(ek)] = float(ev or 0) * drop_mult
        except Exception:
            pass
    if not per_ek and st.get("drops"):
        for eid, w in (st.get("drops") or {}).items():
            per_ek[str(eid)] = float(w or 0) * drop_mult / 3.0

    useful = 0.0
    per_need: Dict[NeedKey, float] = {}
    for key, rem_v in rem.items():
        if rem_v <= 0:
            continue
        slot, tier = key
        exp = float(per_st.get(key, 0.0)) * drop_mult
        if exp <= 0:
            continue
        if strategy == "low_fixed":
            fix = float(fixed_st.get(key, 0.0)) * drop_mult
            # 确定掉落为主，随机部分降权
            exp_eff = fix + max(0.0, exp - fix) * 0.25
        else:
            exp_eff = exp
        per_need[key] = exp_eff
        gap_boost = 1.0 + min(rem_v, 30.0) / 15.0
        # 靠前部位优先（项链→…→帽子），同部位高 T 在 high_random 已加权
        try:
            slot_i = next(i for i, (s, _) in enumerate(SLOT_UI_ORDER) if s == slot)
        except StopIteration:
            slot_i = 20
        order_boost = 1.0 + max(0, 12 - slot_i) * 0.04
        useful += exp_eff * _tier_weight(tier, strategy) * gap_boost * order_boost

    if useful <= 0:
        return 0.0, per_need, per_ek
    # 低级策略额外奖励「固定掉落密度」
    if strategy == "low_fixed":
        fix_total = sum(fixed_st.values()) * drop_mult
        useful += fix_total * 0.15
    return useful / ap, per_need, per_ek


def _merge_stage_into_plan(
    plan: List[Dict[str, Any]],
    best: Dict[str, Any],
    runs_need: int,
    ap: int,
    covers_need: Dict[str, float],
    covers: Dict[str, float],
) -> None:
    """同 stage_id 合并次数；否则新增一行计划。"""
    sid = str(best.get("id") or "")
    token = str(best.get("apply_token") or (sid + "-"))
    for row in plan:
        if row["stage_id"] == sid:
            row["runs"] += runs_need
            row["ap_cost_total"] += runs_need * ap
            for k, v in covers.items():
                row["covers_ek"][k] = float(row["covers_ek"].get(k, 0.0)) + v
            for k, v in covers_need.items():
                row["covers"][k] = float(row["covers"].get(k, 0.0)) + v
            return
    plan.append(
        {
            "stage_id": sid,
            "name": best.get("name") or sid,
            "runs": runs_need,
            "ap_cost": ap,
            "ap_cost_total": runs_need * ap,
            "covers": covers_need,
            "covers_ek": covers,
            "apply_token": token,
            "difficulty": best.get("difficulty") or "",
            "summary_cn": best.get("summary_cn") or "",
            "byproducts_cn": best.get("byproducts_cn") or "",
            "random_pools": best.get("random_pools") or [],
            "fixed_drops": best.get("fixed_drops") or [],
            "expected_by_equip": best.get("expected_by_equip") or {},
        }
    )


def _greedy_pick_stages(
    stages: List[Dict[str, Any]],
    remaining: Dict[NeedKey, float],
    strategy: str,
    drop_mult: float,
    eq: Dict[str, Dict[str, Any]],
    max_stages: int,
    each_run_cap: int,
) -> List[Dict[str, Any]]:
    """贪心：每轮选最高分关卡、算 runs、扣缺口并合并计划。"""
    plan: List[Dict[str, Any]] = []
    guard = 0
    while remaining and len(plan) < max_stages and guard < 300:
        guard += 1
        best = None
        best_score = 0.0
        best_per: Dict[NeedKey, float] = {}
        best_ek: Dict[str, float] = {}
        for st in stages:
            sc, per, per_ek = _stage_score(st, remaining, eq, strategy, drop_mult)
            if sc > best_score:
                best_score = sc
                best = st
                best_per = per
                best_ek = per_ek
        if not best or best_score <= 0:
            break

        ap = max(1, int(best.get("ap_cost") or 10))
        runs_need = 1
        for key, exp in best_per.items():
            if exp <= 0 or key not in remaining:
                continue
            runs_need = max(runs_need, int(math.ceil(remaining[key] / exp)))
        runs_need = max(1, min(runs_need, each_run_cap))

        covers: Dict[str, float] = {}
        covers_need: Dict[str, float] = {}
        for key, exp in best_per.items():
            amt = exp * runs_need
            if amt <= 0:
                continue
            lk = label_need(key[0], key[1])
            covers_need[lk] = covers_need.get(lk, 0.0) + amt
            if key in remaining:
                remaining[key] -= amt
                if remaining[key] <= 1e-6:
                    remaining.pop(key, None)

        for ek, exp in best_ek.items():
            amt = exp * runs_need
            if amt <= 0:
                continue
            covers[ek] = covers.get(ek, 0.0) + amt

        _merge_stage_into_plan(plan, best, runs_need, ap, covers_need, covers)
    return plan


def recommend_stages(
    needs: Any,
    table: Optional[Dict[str, Any]] = None,
    *,
    prefer_3x: bool = True,  # 兼容旧参数；v2 用 drop_mult
    strategy: str = "high_random",
    include_normal: bool = True,
    include_hard: bool = True,
    drop_mult: float = 1.0,
    max_stages: int = 10,
    each_run_cap: int = 999,
) -> Dict[str, Any]:
    """根据缺口推荐关卡。

    needs:
      - Dict[NeedKey, int]  新版 (slot, tier)→件数
      - Dict[str, int]      旧版 equip_id→件数（尽量兼容）
    strategy:
      - high_random: 优先概率掉落的高级图
      - low_fixed:   优先确定掉落的低级图
    """
    table = table or load_stage_table()
    eq = equip_index(table)
    drop_mult = max(0.01, float(drop_mult or 1.0))

    # 归一 needs → NeedKey
    need_st = _normalize_needs(needs, eq)

    stages = _filter_stages(
        list(table.get("stages") or []),
        include_normal=include_normal,
        include_hard=include_hard,
    )
    # 无装备期望的关跳过
    stages = [
        s
        for s in stages
        if (s.get("expected_by_equip") or s.get("drops") or s.get("fixed_drops"))
    ]

    remaining = {k: float(v) for k, v in need_st.items() if float(v) > 0}
    strategy = (strategy or "high_random").strip().lower()
    if strategy not in ("high_random", "low_fixed"):
        strategy = "high_random"

    plan = _greedy_pick_stages(
        stages, remaining, strategy, drop_mult, eq, max_stages, each_run_cap
    )

    # 按策略排列：high_random 高级图在前，low_fixed 低级图在前
    # 两种策略选出的图与排列顺序不同
    try:
        def _plan_main_tier(r):
            best = 0
            for label in (r.get("covers") or {}):
                m = re.search(r'T(\d+)', str(label))
                if m:
                    best = max(best, int(m.group(1)))
            return best

        plan.sort(key=_plan_main_tier, reverse=(strategy == "high_random"))
    except Exception:
        pass

    total_ap = sum(int(r["ap_cost_total"]) for r in plan)
    apply_parts = []
    for r in plan:
        tok = str(r.get("apply_token") or "")
        # token 已是 14-1- / h14-1-，拼次数
        if tok.endswith("-"):
            apply_parts.append(f"{tok}{int(r['runs'])}")
        else:
            apply_parts.append(f"{tok}-{int(r['runs'])}")
    apply_text = ",".join(apply_parts)

    # 详情文案（默认精简；由 format_plan_text 统一渲染）
    copy_text = format_plan_text(
        plan,
        eq,
        drop_mult=drop_mult,
        strategy=strategy,
        total_ap=total_ap,
        remaining=remaining,
        need_st=need_st,
        include_univ=True,
        detailed=False,
    )

    return {
        "needs": {f"{s}:T{t}": v for (s, t), v in need_st.items()},
        "remaining": {f"{s}:T{t}": v for (s, t), v in remaining.items()},
        "plan": plan,
        "total_ap": total_ap,
        "apply_text": apply_text,
        "copy_text": copy_text,
        "detail_text": copy_text,
        "strategy": strategy,
        "drop_mult": drop_mult,
        "eq": eq,
    }


def format_byproducts(
    expected_by_equip: Dict[str, Any],
    eq: Dict[str, Dict[str, Any]],
    drop_mult: float,
    runs: int,
    *,
    top_n: int = 12,
    include_univ: bool = True,
) -> str:
    rows = []
    for ek, ev in (expected_by_equip or {}).items():
        ek = str(ek)
        if not include_univ and is_universal_key(eq, ek):
            continue
        try:
            total = float(ev or 0) * drop_mult * max(1, int(runs))
        except Exception:
            continue
        if total < 0.05:
            continue
        rows.append((total, label_equip_key(eq, ek)))
    rows.sort(key=lambda x: -x[0])
    if not rows:
        return ""
    return "，".join(f"{name}≈{val:.2f}" for val, name in rows[:top_n])


def _pool_summary_compact(p: Dict[str, Any], eq: Dict[str, Dict[str, Any]]) -> str:
    sm = str(p.get("summary_cn") or "").strip()
    if sm:
        # 去掉前缀「随机：」若有
        return sm
    tc = float(p.get("trigger_chance") or 0) * 100
    bits = []
    for it in p.get("items") or []:
        tier = it.get("tier")
        slot_cn = it.get("slot_cn") or SLOT_CN.get(str(it.get("slot") or ""), "")
        pin = float(it.get("p_in_pool") or 0) * 100
        bits.append(f"T{tier}{slot_cn}{pin:.2f}%")
    if not bits:
        return ""
    return f"{tc:g}%掉落：{'，'.join(bits)}"


def _fixed_prob_compact(
    st_or_row: Dict[str, Any],
    eq: Dict[str, Dict[str, Any]],
    *,
    include_univ: bool = True,
) -> str:
    bits = []
    for row in st_or_row.get("fixed_drops") or []:
        ek = str(row.get("equip_key") or "")
        if not ek:
            continue
        if not include_univ and is_universal_key(eq, ek):
            continue
        try:
            ch = float(row.get("chance", 1) or 1)
            am = float(row.get("amount") or 1)
        except Exception:
            continue
        lab = label_equip_key(eq, ek)
        if abs(ch - 1.0) < 1e-9:
            bits.append(f"{lab}×{am:g}必掉")
        else:
            bits.append(f"{lab} {ch*100:.1f}%")
    return "，".join(bits)


def format_plan_text(
    plan: List[Dict[str, Any]],
    eq: Dict[str, Dict[str, Any]],
    *,
    drop_mult: float = 1.0,
    strategy: str = "high_random",
    total_ap: int = 0,
    remaining: Optional[Dict[NeedKey, float]] = None,
    need_st: Optional[Dict[NeedKey, float]] = None,
    include_univ: bool = True,
    detailed: bool = False,
) -> str:
    """精简/详细计划文案。"""
    lines: List[str] = []
    strat_cn = (
        "高级图概率掉落"
        if strategy == "high_random"
        else "低级图确定掉落"
    )
    lines.append(f"【装备刷图建议 · {strat_cn}】")
    if drop_mult and abs(float(drop_mult) - 1.0) > 1e-9:
        lines.append(f"掉落倍率：×{float(drop_mult):g}")
    if not need_st:
        lines.append("还没有填写缺口：在简单模式各部位框里填所缺 T 阶，如 9,8。")
        return "\n".join(lines)
    if not plan:
        lines.append("当前筛选下没有能覆盖缺口的关卡，可勾选困难图或调整倍率/策略。")
        return "\n".join(lines)


    # 白话摘要（第一眼）
    n_st = len(plan)
    lines.append(
        f"摘要：约 {int(total_ap)} 体力 · {n_st} 张图 · {strat_cn}"
        + (f" · ×{float(drop_mult):g}" if abs(float(drop_mult) - 1.0) > 1e-9 else "")
    )

    for r in plan:
        runs = int(r.get("runs") or 1)
        ap_total = int(r.get("ap_cost_total") or runs * int(r.get("ap_cost") or 10))
        lines.append(f"· {r.get('stage_id')}  ×{runs} {ap_total}体")
        by = format_byproducts(
            r.get("expected_by_equip") or {},
            eq,
            drop_mult,
            runs,
            include_univ=include_univ,
        )
        if by:
            lines.append(f"  约可获得：{by}")
        if detailed:
            fp = _fixed_prob_compact(r, eq, include_univ=include_univ)
            if fp:
                lines.append(fp)
            pools = []
            for p in r.get("random_pools") or []:
                s = _pool_summary_compact(p, eq)
                if s:
                    pools.append(s)
            if pools:
                lines.append("；".join(pools))
    lines.append(f"合计约 {int(total_ap)} 体力（期望估算）。")
    if remaining:
        left = "、".join(
            f"{label_need(s, t)}还缺≈{v:.1f}" for (s, t), v in remaining.items()
        )
        if left:
            lines.append(f"仍可能不够：{left}")
    return "\n".join(lines)


def build_stage_detail_blocks(
    plan: List[Dict[str, Any]],
    eq: Dict[str, Dict[str, Any]],
    drop_mult: float,
    *,
    include_univ: bool = True,
    detailed: bool = True,
) -> List[str]:
    text = format_plan_text(
        plan,
        eq,
        drop_mult=drop_mult,
        total_ap=sum(int(r.get("ap_cost_total") or 0) for r in plan),
        include_univ=include_univ,
        detailed=detailed,
        need_st={("x", 1): 1},  # force non-empty path
        strategy="high_random",
    )
    return text.splitlines()


_RUN_TOKEN_RE = re.compile(
    r"(?P<hard>[hH])?(?P<a>\d+)\s*[-_]\s*(?P<s>\d+)\s*[-_]?\s*(?P<n>\d+)?",
)


def parse_run_spec(text: str) -> List[Tuple[str, int]]:
    """解析 '14-1-15,h14-1-3,15-1-' → [('14-1',15),('h14-1',3),('15-1',1)]。"""
    raw = str(text or "").strip()
    if not raw:
        return []
    raw = raw.replace("，", ",").replace(" ", "")
    out: List[Tuple[str, int]] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        m = _RUN_TOKEN_RE.fullmatch(part) or _RUN_TOKEN_RE.match(part)
        if not m:
            # 尝试 apply_token 形式 14-1-
            m2 = re.fullmatch(r"([hH])?(\d+)[-_](\d+)[-_]?", part)
            if not m2:
                continue
            hard, a, s = m2.group(1), m2.group(2), m2.group(3)
            sid = f"h{a}-{s}" if hard else f"{a}-{s}"
            out.append((sid, 1))
            continue
        hard = m.group("hard")
        a, s = m.group("a"), m.group("s")
        n = m.group("n")
        runs = int(n) if n else 1
        runs = max(1, min(runs, 9999))
        sid = f"h{a}-{s}" if hard else f"{a}-{s}"
        out.append((sid.lower() if sid.startswith("h") else sid, runs))
    # 合并同关
    merged: Dict[str, int] = {}
    order: List[str] = []
    for sid, n in out:
        if sid not in merged:
            order.append(sid)
            merged[sid] = 0
        merged[sid] += n
    return [(sid, merged[sid]) for sid in order]


def estimate_from_run_text(
    text: str,
    table: Optional[Dict[str, Any]] = None,
    *,
    drop_mult: float = 1.0,
    include_univ: bool = True,
    detailed: bool = False,
) -> Dict[str, Any]:
    """按长条框里的关卡×次数，汇总期望产出（精简默认）。"""
    table = table or load_stage_table()
    eq = equip_index(table)
    drop_mult = max(0.01, float(drop_mult or 1.0))
    specs = parse_run_spec(text)
    by_id = {str(s.get("id")): s for s in table.get("stages") or []}
    totals: Dict[str, float] = {}
    lines = ["【按当前次数估算】"]
    if not specs:
        lines.append("尚未识别到关卡次数。可写：14-1-15,h14-1-3")
        return {"totals": {}, "copy_text": "\n".join(lines), "specs": []}

    for sid, runs in specs:
        st = by_id.get(sid)
        if st is None:
            lines.append(f"· {sid} ×{runs}：表中无此关，已跳过")
            continue
        ap = max(1, int(st.get("ap_cost") or 10))
        ap_total = ap * int(runs)
        exp_map = st.get("expected_by_equip") or {}
        lines.append(f"· {sid}  ×{runs} {ap_total}体")
        part_bits = []
        for ek, ev in exp_map.items():
            ek = str(ek)
            if not include_univ and is_universal_key(eq, ek):
                continue
            try:
                amt = float(ev or 0) * drop_mult * runs
            except Exception:
                continue
            if amt < 0.01:
                continue
            totals[ek] = totals.get(ek, 0.0) + amt
            part_bits.append((amt, label_equip_key(eq, ek)))
        part_bits.sort(key=lambda x: -x[0])
        if part_bits:
            lines.append(
                "  约可获得："
                + "，".join(f"{n}≈{a:.2f}" for a, n in part_bits[:12])
            )
        if detailed:
            fp = _fixed_prob_compact(st, eq, include_univ=include_univ)
            if fp:
                lines.append(fp)
            pools = []
            for p in st.get("random_pools") or []:
                s = _pool_summary_compact(p, eq)
                if s:
                    pools.append(s)
            if pools:
                lines.append("；".join(pools))
    return {
        "totals": totals,
        "specs": specs,
        "copy_text": "\n".join(lines),
        "eq": eq,
    }


def apply_tokens_to_mainline_string(text: str) -> str:
    """从长条框提取普通关，转成 mainlinePriority：14-1-15,15-2-3。"""
    specs = parse_run_spec(text)
    parts = []
    for sid, runs in specs:
        if str(sid).startswith("h"):
            continue
        # sid = 14-1
        parts.append(f"{sid}-{int(runs)}")
    return ",".join(parts)


def apply_tokens_to_hard_string(text: str) -> str:
    """困难关 → hardPriority（不带 h 前缀）：14-1-3。"""
    specs = parse_run_spec(text)
    parts = []
    for sid, runs in specs:
        s = str(sid)
        if not s.startswith("h"):
            continue
        body = s[1:]  # 14-1
        parts.append(f"{body}-{int(runs)}")
    return ",".join(parts)
