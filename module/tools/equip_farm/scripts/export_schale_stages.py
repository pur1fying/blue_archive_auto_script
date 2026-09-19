#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Schale DB 导出国服主线装备掉落表 + 神名文字掉落表。

仅用 stdlib（urllib + json），可重复跑、幂等覆盖输出 JSON。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data"))

URL_STAGES = "https://schaledb.brightsu.cn/data/cn/stages.min.json"
URL_EQUIPMENT = "https://schaledb.brightsu.cn/data/cn/equipment.min.json"
URL_GROUPS = "https://schaledb.brightsu.cn/data/groups.min.json"
URL_ITEMS = "https://schaledb.brightsu.cn/data/cn/items.min.json"
URL_STUDENTS = "https://schaledb.brightsu.cn/data/cn/students.min.json"
URL_SOURCE = "https://schaledb.brightsu.cn/stage/"

EXCLUDE_REWARD_TYPES = {"FirstClear", "ThreeStar"}
SLOT_CATS = {
    "Hat": ("hat", "帽子"),
    "Gloves": ("gloves", "手套"),
    "Shoes": ("shoes", "鞋子"),
    "Bag": ("bag", "包"),
    "Badge": ("badge", "徽章"),
    "Hairpin": ("hairpin", "发带"),
    "Charm": ("charm", "护身符"),
    "Watch": ("watch", "表"),
    "Necklace": ("necklace", "项链"),
}
SLOTS = [{"id": v[0], "cn": v[1]} for v in SLOT_CATS.values()]
MAX_GACHA_DEPTH = 5


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "equip-farm-export/2.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def as_map(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items()}
    raise TypeError(f"expected dict, got {type(data)}")


def parse_ap_cost(entry_cost: Any) -> int:
    """EntryCost 形如 [[5, 10]] → 10。"""
    if not entry_cost:
        return 0
    try:
        first = entry_cost[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            return int(first[1])
        if isinstance(first, (int, float)):
            return int(first)
    except (TypeError, ValueError, IndexError):
        pass
    return 0


def reward_amount(r: dict) -> float:
    amin = r.get("AmountMin")
    amax = r.get("AmountMax")
    if amin is not None and amax is not None:
        amin_f = float(amin)
        amax_f = float(amax)
        if amin_f != amax_f:
            return (amin_f + amax_f) / 2.0
        return amin_f
    if r.get("Amount") is not None:
        return float(r["Amount"])
    if amin is not None:
        return float(amin)
    if amax is not None:
        return float(amax)
    return 1.0


def reward_chance(r: dict) -> float:
    c = r.get("Chance")
    if c is None:
        return 1.0
    return float(c)


def round_p(x: float, nd: int = 6) -> float:
    return round(float(x), nd)


def pct_str(p: float) -> str:
    """0.225 → 22.5%；0.3333 → 33.33%。"""
    v = p * 100.0
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v))}%"
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return f"{s}%"


def stage_public_id(area: int, stage: int, difficulty: int) -> Tuple[str, str, str]:
    if int(difficulty) == 0:
        sid = f"{area}-{stage}"
        return sid, f"{sid}-", "normal"
    sid = f"h{area}-{stage}"
    return sid, f"{sid}-", "hard"


class EquipIndex:
    def __init__(self, equipment: Dict[str, Any]):
        self.raw = equipment
        self.by_id: Dict[int, dict] = {}
        self.key_of: Dict[int, str] = {}
        self.equips: Dict[str, dict] = {}
        self._build()

    def _kind_and_base_key(self, name: str, slot: str, tier: int) -> Tuple[str, str]:
        if "万能" in name:
            return "universal_blueprint", f"{slot}_univ"
        if "设计图" in name:
            return "blueprint", f"{slot}_bp_t{tier}"
        return "gear", f"{slot}_t{tier}"

    def _build(self) -> None:
        # 先按自然 id 生成 base key，冲突再后缀
        tentative: Dict[int, Tuple[str, dict]] = {}
        base_counts: Dict[str, List[int]] = defaultdict(list)
        for k, e in self.raw.items():
            cat = e.get("Category")
            if cat not in SLOT_CATS:
                continue
            eid = int(e["Id"])
            slot, slot_cn = SLOT_CATS[cat]
            name = e.get("Name") or f"equip_{eid}"
            tier = int(e.get("Tier") or 0)
            rarity = e.get("Rarity") or ""
            kind, base = self._kind_and_base_key(name, slot, tier)
            meta = {
                "equip_id": eid,
                "name": name,
                "slot": slot,
                "slot_cn": slot_cn,
                "tier": tier,
                "kind": kind,
                "rarity": rarity,
                "icon": e.get("Icon") or "",
                "category": cat,
            }
            tentative[eid] = (base, meta)
            base_counts[base].append(eid)

        key_assign: Dict[int, str] = {}
        for base, ids in base_counts.items():
            ids_sorted = sorted(ids)
            if len(ids_sorted) == 1:
                key_assign[ids_sorted[0]] = base
            else:
                for eid in ids_sorted:
                    key_assign[eid] = f"{base}_{eid}"

        for eid, (base, meta) in tentative.items():
            key = key_assign[eid]
            self.by_id[eid] = meta
            self.key_of[eid] = key
            self.equips[key] = {
                "id": key,
                "equip_id": meta["equip_id"],
                "name": meta["name"],
                "slot": meta["slot"],
                "slot_cn": meta["slot_cn"],
                "tier": meta["tier"],
                "kind": meta["kind"],
                "rarity": meta["rarity"],
            }

    def is_slot_equip(self, eid: int) -> bool:
        return int(eid) in self.by_id

    def get(self, eid: int) -> Optional[dict]:
        return self.by_id.get(int(eid))

    def key(self, eid: int) -> Optional[str]:
        return self.key_of.get(int(eid))


def expand_gacha_equipment(
    group_id: int,
    groups: Dict[str, Any],
    eq_index: EquipIndex,
    depth: int = 0,
    seen: Optional[set] = None,
) -> List[dict]:
    """递归展开 GachaGroup，只保留部位装备。返回 [{equip_id, weight, amount}, ...]。"""
    if seen is None:
        seen = set()
    if depth > MAX_GACHA_DEPTH:
        return []
    gid = int(group_id)
    if gid in seen:
        return []
    seen = set(seen)
    seen.add(gid)

    g = groups.get(str(gid))
    if not g:
        return []

    out: List[dict] = []
    for it in g.get("Items") or []:
        typ = it.get("Type")
        weight = float(it.get("Chance") or 0.0)
        if weight <= 0:
            # Schale 里部分 Recursive 池 Chance 全 0，跳过
            continue
        amt = reward_amount(it)
        if typ == "Equipment":
            eid = int(it["Id"])
            if eq_index.is_slot_equip(eid):
                out.append({"equip_id": eid, "weight": weight, "amount": amt})
        elif typ == "GachaGroup":
            nested = expand_gacha_equipment(int(it["Id"]), groups, eq_index, depth + 1, seen)
            for n in nested:
                out.append(
                    {
                        "equip_id": n["equip_id"],
                        "weight": weight * float(n["weight"]),
                        "amount": n["amount"],
                    }
                )
    return out


def normalize_pool_items(raw_items: List[dict], eq_index: EquipIndex) -> List[dict]:
    """合并同 equip_id 权重，并做池内归一化。"""
    merged: Dict[int, dict] = {}
    for it in raw_items:
        eid = int(it["equip_id"])
        if eid not in merged:
            merged[eid] = {
                "equip_id": eid,
                "weight": float(it["weight"]),
                "amount": float(it["amount"]),
            }
        else:
            merged[eid]["weight"] += float(it["weight"])
            # amount 取首次；同池一般一致
    total_w = sum(v["weight"] for v in merged.values())
    if total_w <= 0:
        return []
    items = []
    for eid in sorted(merged.keys()):
        v = merged[eid]
        meta = eq_index.get(eid)
        if not meta:
            continue
        key = eq_index.key(eid)
        p_norm = v["weight"] / total_w
        items.append(
            {
                "equip_key": key,
                "equip_id": eid,
                "weight": round_p(v["weight"], 6),
                "p_norm": round_p(p_norm, 6),
                "amount": v["amount"],
                "name": meta["name"],
                "slot": meta["slot"],
                "slot_cn": meta["slot_cn"],
                "tier": meta["tier"],
                "kind": meta["kind"],
            }
        )
    return items


def pool_label_cn(items: List[dict]) -> str:
    if not items:
        return "随机物品"
    slots = []
    seen = set()
    for it in items:
        sc = it["slot_cn"]
        if sc not in seen:
            seen.add(sc)
            slots.append(sc)
    kinds = {it["kind"] for it in items}
    if kinds <= {"blueprint", "universal_blueprint"} or any(
        it["kind"] == "blueprint" for it in items
    ):
        tail = "设计图"
    elif kinds == {"gear"}:
        tail = "成品"
    else:
        tail = "装备"
    slot_part = "/".join(slots)
    return f"随机物品（{slot_part}{tail}）"


def pool_summary_cn(trigger: float, items: List[dict]) -> str:
    parts = []
    for it in items:
        tier = it["tier"]
        sc = it["slot_cn"]
        kind = it["kind"]
        if kind == "universal_blueprint":
            label = f"{sc}万能"
        elif kind == "blueprint":
            label = f"T{tier}{sc}"
        else:
            label = f"T{tier}{sc}成品"
        parts.append(f"{label}{pct_str(it['p_in_pool'])}")
    return f"{pct_str(trigger)}掉落：{'，'.join(parts)}"


def build_stage_summary(
    public_id: str,
    fixed: List[dict],
    pools: List[dict],
    eq_index: EquipIndex,
) -> Tuple[str, str]:
    """返回 (summary_cn, byproducts_cn)。"""
    bits = []
    for f in fixed:
        meta = eq_index.get(f["equip_id"])
        name = meta["name"] if meta else f["equip_key"]
        ch = f["chance"]
        amt = f["amount"]
        if abs(ch - 1.0) < 1e-12:
            if abs(amt - 1.0) < 1e-12:
                bits.append(f"固定 {name}")
            else:
                bits.append(f"固定 {name}×{gformat(amt)}")
        else:
            bits.append(f"{pct_str(ch)} {name}" + (f"×{gformat(amt)}" if abs(amt - 1.0) > 1e-12 else ""))
    for p in pools:
        bits.append(p["summary_cn"])
    summary = f"{public_id}：" + ("；".join(bits) if bits else "无装备掉落")

    # 副产：全部 expected>0 的短句
    by_parts = []
    for f in fixed:
        meta = eq_index.get(f["equip_id"])
        if not meta:
            continue
        by_parts.append(f"{meta['name']}期望{gformat(f['expected'])}")
    for p in pools:
        for it in p["items"]:
            by_parts.append(f"{it['name']}期望{gformat(it['expected'])}")
    byproducts = "刷本图时副产：" + ("，".join(by_parts) if by_parts else "无")
    return summary, byproducts


def gformat(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return s


def _is_main_campaign(s: dict) -> bool:
    """主线战役判定：跳过 Stage='A' 等素材支线。"""
    if s.get("Category") != "Campaign":
        return False
    try:
        d = int(s.get("Difficulty"))
        int(s.get("Area"))
        int(s.get("Stage"))
    except (TypeError, ValueError):
        return False  # 跳过 Stage='A' 等素材支线
    return d in (0, 1)


def _process_gacha_reward(
    r: dict,
    groups: Dict[str, Any],
    eq_index: "EquipIndex",
    gacha_groups_out: Dict[str, dict],
    used_equip_keys: set,
    expected_by: Dict[str, float],
) -> Optional[dict]:
    """展开 GachaGroup 奖励为随机池条目；池内无部位装备返回 None。"""
    gid = int(r["Id"])
    raw = expand_gacha_equipment(gid, groups, eq_index)
    if not raw:
        return None  # 如 500100 无装备，跳过
    norm_items = normalize_pool_items(raw, eq_index)
    if not norm_items:
        return None
    # cache gacha_groups
    gacha_groups_out[str(gid)] = {
        "id": gid,
        "items": [
            {
                "equip_key": it["equip_key"],
                "equip_id": it["equip_id"],
                "weight": it["weight"],
                "p_norm": it["p_norm"],
            }
            for it in norm_items
        ],
    }
    trigger = reward_chance(r)
    pool_amt = reward_amount(r)
    pool_items = []
    summary_items = []
    for it in norm_items:
        p_in = float(it["p_norm"])
        # p_abs = 关卡 trigger × 池内归一概率（单抽命中语义）
        # expected = p_abs × 池内件数 × 关卡 Amount（Amount 视为抽取次数）
        item_amt = float(it["amount"])
        exp = trigger * p_in * item_amt * float(pool_amt)
        entry = {
            "equip_key": it["equip_key"],
            "equip_id": it["equip_id"],
            "name": it["name"],
            "slot_cn": it["slot_cn"],
            "tier": it["tier"],
            "p_in_pool": round_p(p_in),
            "p_abs": round_p(trigger * p_in),
            "amount": _num(item_amt * float(pool_amt)),
            "expected": round_p(exp),
        }
        pool_items.append(entry)
        expected_by[it["equip_key"]] += exp
        used_equip_keys.add(it["equip_key"])
        meta = eq_index.get(it["equip_id"])
        summary_items.append(
            {
                "tier": it["tier"],
                "slot_cn": it["slot_cn"],
                "kind": meta["kind"] if meta else "gear",
                "p_in_pool": round_p(p_in),
            }
        )

    label = pool_label_cn(summary_items)
    return {
        "group_id": gid,
        "trigger_chance": round_p(trigger),
        "amount": _num(pool_amt),
        "label_cn": label,
        "items": pool_items,
        "summary_cn": pool_summary_cn(trigger, summary_items),
    }


def _collect_stage_drops(
    st: dict,
    eq_index: "EquipIndex",
    groups: Dict[str, Any],
    gacha_groups_out: Dict[str, dict],
    used_equip_keys: set,
) -> tuple:
    """单关奖励 → (固定掉落, 随机池, 期望表)。"""
    fixed_drops: List[dict] = []
    random_pools: List[dict] = []
    expected_by: Dict[str, float] = defaultdict(float)

    for r in st.get("Rewards") or []:
        if r.get("RewardType") in EXCLUDE_REWARD_TYPES:
            continue
        typ = r.get("Type")
        if typ == "Equipment":
            eid = int(r["Id"])
            if not eq_index.is_slot_equip(eid):
                continue
            key = eq_index.key(eid)
            ch = reward_chance(r)
            amt = reward_amount(r)
            exp = ch * amt
            fixed_drops.append(
                {
                    "equip_key": key,
                    "equip_id": eid,
                    "chance": round_p(ch),
                    "amount": _num(amt),
                    "expected": round_p(exp),
                }
            )
            expected_by[key] += exp
            used_equip_keys.add(key)
        elif typ == "GachaGroup":
            pool = _process_gacha_reward(
                r, groups, eq_index, gacha_groups_out, used_equip_keys, expected_by
            )
            if pool:
                random_pools.append(pool)
    return fixed_drops, random_pools, expected_by


def _equip_export_sort_key(eq: dict):
    slot_order = {s["id"]: i for i, s in enumerate(SLOTS)}
    return (
        slot_order.get(eq["slot"], 99),
        eq["tier"],
        0 if eq["kind"] == "gear" else 1 if eq["kind"] == "blueprint" else 2,
        eq["equip_id"],
    )


def _build_equips_list(eq_index: "EquipIndex", used_equip_keys: set) -> List[dict]:
    """导出全部位装备目录；先校验 stages 用到的 key 都在。"""
    for k in used_equip_keys:
        if k not in eq_index.equips:
            raise RuntimeError(f"missing equip_key {k}")
    all_eq = list(eq_index.equips.values())
    all_eq.sort(key=_equip_export_sort_key)
    return all_eq


def build_equip_export(
    stages: Dict[str, Any],
    equipment: Dict[str, Any],
    groups: Dict[str, Any],
) -> dict:
    eq_index = EquipIndex(equipment)
    gacha_groups_out: Dict[str, dict] = {}
    used_equip_keys = set()
    stages_out: List[dict] = []

    campaign = [s for s in stages.values() if _is_main_campaign(s)]
    campaign.sort(key=lambda s: (int(s.get("Difficulty", 0)), int(s.get("Area", 0)), int(s.get("Stage", 0))))

    for st in campaign:
        area = int(st["Area"])
        stage_n = int(st["Stage"])
        diff = int(st["Difficulty"])
        public_id, apply_token, diff_name = stage_public_id(area, stage_n, diff)
        ap = parse_ap_cost(st.get("EntryCost"))

        fixed_drops, random_pools, expected_by = _collect_stage_drops(
            st, eq_index, groups, gacha_groups_out, used_equip_keys
        )

        # 合并 fixed 同 key? 保留多条（14-1 万能有固定 3 + chance 0.75×1）
        expected_round = {k: round_p(v) for k, v in sorted(expected_by.items())}
        summary_cn, byproducts_cn = build_stage_summary(
            public_id, fixed_drops, random_pools, eq_index
        )

        # 无任何装备则仍导出（主线完整性）；fixed/random 可空
        stages_out.append(
            {
                "id": public_id,
                "apply_token": apply_token,
                "stage_db_id": int(st["Id"]),
                "area": area,
                "stage": stage_n,
                "difficulty": diff_name,
                "difficulty_code": diff,
                "name": st.get("Name") or public_id,
                "ap_cost": ap,
                "times_mode": "1x",
                "fixed_drops": fixed_drops,
                "random_pools": random_pools,
                "expected_by_equip": expected_round,
                "byproducts_cn": byproducts_cn,
                "summary_cn": summary_cn,
            }
        )

    # equips 必须覆盖 stages 里出现的全部 equip_key；导出全部位装备目录更稳妥
    equips_list = _build_equips_list(eq_index, used_equip_keys)

    note = (
        "排除首通/三星；含固定装备与 GachaGroup 展开。expected=关卡Chance×池内归一概率×数量。"
        "概率数据来自 Schale DB。"
        "后续计算器约定：A) 用户输入各部位×T阶缺口；B) 策略1优先概率高级图(expected/ap，高T加权)，"
        "策略2优先 chance==1 固定掉落；C) 展示推荐关卡/主副产物/概率；"
        "D) 可复制 apply_token 串（如 14-1-,15-1-）；E) 脚注固定标明数据来源。"
    )

    return {
        "version": 2,
        "source": URL_SOURCE,
        "source_files": {
            "stages": URL_STAGES,
            "equipment": URL_EQUIPMENT,
            "groups": URL_GROUPS,
        },
        "note": note,
        "meta": {
            "exclude_reward_types": sorted(EXCLUDE_REWARD_TYPES),
            "skip_stage_alpha": True,
            "skip_stage_alpha_note": "Campaign 中 Stage 为字母（如 A）的素材支线不纳入主线装备表",
            "rules": {
                "kind": "名称含万能→universal_blueprint；含设计图→blueprint；否则 gear",
                "chance_default": 1.0,
                "gacha_norm": "pool weights normalized over Equipment items only",
                "gacha_skip_if_no_equipment": "如 500100 杂物池展开后无部位装备则整池跳过",
            },
        },
        "slots": SLOTS,
        "equips": equips_list,
        "gacha_groups": dict(sorted(gacha_groups_out.items(), key=lambda x: int(x[0]))),
        "stages": stages_out,
    }


def _num(x: float):
    if abs(x - round(x)) < 1e-9:
        return int(round(x))
    return round_p(x)


def build_secretstone_export(
    stages: Dict[str, Any],
    items: Dict[str, Any],
    students: Dict[str, Any],
) -> dict:
    """神名文字：物品 ↔ 学生 ↔ 主线关卡掉落（类同结构）。"""
    # students by Name
    stu_by_name: Dict[str, dict] = {}
    stu_by_id: Dict[int, dict] = {}
    for s in students.values():
        stu_by_name[s.get("Name") or ""] = s
        stu_by_id[int(s["Id"])] = s

    stones: Dict[int, dict] = {}
    for it in items.values():
        if it.get("Category") != "SecretStone":
            continue
        iid = int(it["Id"])
        name = it.get("Name") or ""
        student_name = name[:-5] if name.endswith("的神名文字") else ""
        st = stu_by_name.get(student_name)
        stones[iid] = {
            "id": f"ss_{iid}",
            "item_id": iid,
            "name": name,
            "student_id": int(st["Id"]) if st else None,
            "student_name": student_name or None,
            "student_path": (st.get("PathName") if st else None),
            "student_dev": (st.get("DevName") if st else None),
            "school": (st.get("School") if st else None),
            "icon": it.get("Icon") or "",
            "stage_drop_flags": it.get("StageDrop"),
        }

    stages_out: List[dict] = []
    used_ids = set()
    def _is_main_campaign(s: dict) -> bool:
        if s.get("Category") != "Campaign":
            return False
        try:
            d = int(s.get("Difficulty"))
            int(s.get("Area"))
            int(s.get("Stage"))
        except (TypeError, ValueError):
            return False
        return d in (0, 1)

    campaign = [s for s in stages.values() if _is_main_campaign(s)]
    campaign.sort(key=lambda s: (int(s.get("Difficulty", 0)), int(s.get("Area", 0)), int(s.get("Stage", 0))))

    for st in campaign:
        area = int(st["Area"])
        stage_n = int(st["Stage"])
        diff = int(st["Difficulty"])
        public_id, apply_token, diff_name = stage_public_id(area, stage_n, diff)
        ap = parse_ap_cost(st.get("EntryCost"))
        fixed = []
        expected_by: Dict[str, float] = defaultdict(float)

        for r in st.get("Rewards") or []:
            if r.get("RewardType") in EXCLUDE_REWARD_TYPES:
                continue
            if r.get("Type") != "Item":
                continue
            iid = int(r["Id"])
            if iid not in stones:
                continue
            ch = reward_chance(r)
            amt = reward_amount(r)
            exp = ch * amt
            key = stones[iid]["id"]
            fixed.append(
                {
                    "stone_key": key,
                    "item_id": iid,
                    "name": stones[iid]["name"],
                    "student_id": stones[iid]["student_id"],
                    "student_name": stones[iid]["student_name"],
                    "chance": round_p(ch),
                    "amount": _num(amt),
                    "expected": round_p(exp),
                }
            )
            expected_by[key] += exp
            used_ids.add(iid)

        if not fixed:
            continue

        bits = []
        for f in fixed:
            if abs(f["chance"] - 1.0) < 1e-12:
                bits.append(f"固定 {f['name']}×{gformat(f['amount'])}")
            else:
                bits.append(f"{pct_str(f['chance'])} {f['name']}")
        summary = f"{public_id}：" + "；".join(bits)
        stages_out.append(
            {
                "id": public_id,
                "apply_token": apply_token,
                "stage_db_id": int(st["Id"]),
                "area": area,
                "stage": stage_n,
                "difficulty": diff_name,
                "difficulty_code": diff,
                "name": st.get("Name") or public_id,
                "ap_cost": ap,
                "times_mode": "1x",
                "fixed_drops": fixed,
                "random_pools": [],
                "expected_by_stone": {k: round_p(v) for k, v in sorted(expected_by.items())},
                "summary_cn": summary,
            }
        )

    stones_list = [stones[i] for i in sorted(stones.keys())]
    # 仅 used 也可；保留全量便于查询学生映射
    note = (
        "神名文字（SecretStone）主线掉落；排除首通/三星。"
        "学生通过「{名字}的神名文字」与 students.Name 对齐。"
        "国服主线多为困难关固定概率掉落（常见 chance=0.4）。"
        f"数据来源：{URL_SOURCE}"
    )
    return {
        "version": 1,
        "source": URL_SOURCE,
        "source_files": {
            "stages": URL_STAGES,
            "items": URL_ITEMS,
            "students": URL_STUDENTS,
        },
        "note": note,
        "meta": {
            "exclude_reward_types": sorted(EXCLUDE_REWARD_TYPES),
            "rules": {
                "match_student": "物品名「X的神名文字」→ students.Name == X",
                "chance_default": 1.0,
            },
        },
        "stones": stones_list,
        "stages": stages_out,
        "stats": {
            "stone_count": len(stones_list),
            "stages_with_drops": len(stages_out),
            "unique_stones_dropped": len(used_ids),
        },
    }


def validate_equip(data: dict) -> List[str]:
    lines = []
    stages = data["stages"]
    lines.append(f"[1] stages 数量 = {len(stages)} （期望约 250 Campaign）")

    # FirstClear leak
    blob = json.dumps(stages, ensure_ascii=False)
    bad = "FirstClear" in blob or "ThreeStar" in blob
    lines.append(f"[2] 无 FirstClear/ThreeStar 泄漏: {'PASS' if not bad else 'FAIL'}")

    by_id = {s["id"]: s for s in stages}

    def check_stage(sid: str, preds: List[str]):
        s = by_id.get(sid)
        if not s:
            lines.append(f"[3] {sid}: MISSING")
            return
        ok = []
        ebe = s.get("expected_by_equip") or {}
        for p in preds:
            ok.append(p)
        lines.append(f"[3] {sid}: ap={s['ap_cost']} db={s['stage_db_id']} fixed={len(s['fixed_drops'])} pools={len(s['random_pools'])}")
        lines.append(f"    expected_keys={list(ebe.keys())}")
        lines.append(f"    summary={s['summary_cn'][:200]}")

    # 1-1
    s11 = by_id.get("1-1")
    if s11:
        keys = set(s11["expected_by_equip"])
        # T1 hat/gloves/shoes gear
        need = {"hat_t1", "gloves_t1", "shoes_t1"}
        ok = need <= keys
        lines.append(f"[3a] 1-1 T1 hat/gloves/shoes: {'PASS' if ok else 'FAIL'} got={sorted(keys)}")
        lines.append(f"     ap={s11['ap_cost']} db={s11['stage_db_id']} (expect 10 / 1011101)")
    else:
        lines.append("[3a] 1-1 MISSING")

    s_h11 = by_id.get("h1-1")
    if s_h11:
        keys = set(s_h11["expected_by_equip"])
        need = {"hat_t1", "charm_t1", "bag_t1"}
        ok = need <= keys
        lines.append(f"[3b] h1-1 hat/charm/bag: {'PASS' if ok else 'FAIL'} got={sorted(keys)}")
        lines.append(f"     ap={s_h11['ap_cost']} (expect 20)")
    else:
        lines.append("[3b] h1-1 MISSING")

    s141 = by_id.get("14-1")
    if s141:
        ebe = s141["expected_by_equip"]
        # charm bp t5 ~0.72, charm univ 5, pools 607002/609002/608002
        gids = {p["group_id"] for p in s141["random_pools"]}
        ok_g = {607002, 609002, 608002} <= gids
        lines.append(f"[3c] 14-1 pools 607002/609002/608002: {'PASS' if ok_g else 'FAIL'} gids={sorted(gids)}")
        # check one summary
        for p in s141["random_pools"]:
            if p["group_id"] == 609002:
                lines.append(f"     609002 summary: {p['summary_cn']}")
                lines.append(f"     trigger={p['trigger_chance']} items={[(i['equip_key'], i['p_in_pool'], i['expected']) for i in p['items']]}")
        # charm
        charm_bp = [k for k in ebe if k.startswith("charm_bp_t5")]
        charm_u = [k for k in ebe if k.startswith("charm_univ")]
        lines.append(f"     charm_bp_t5={[(k,ebe[k]) for k in charm_bp]} charm_univ={[(k,ebe[k]) for k in charm_u]}")
        lines.append(f"     full summary: {s141['summary_cn']}")
    else:
        lines.append("[3c] 14-1 MISSING")

    s163 = by_id.get("16-3")
    if s163:
        ebe = s163["expected_by_equip"]
        has_high = any(
            (eq_kind_from_key(k) in ("blueprint", "universal_blueprint") and tier_from_key(k, ebe, data) >= 4)
            or ("univ" in k)
            or ("_bp_t" in k and not k.endswith("_t1") and not k.endswith("_t2") and not k.endswith("_t3"))
            for k in ebe
        )
        # simpler: any blueprint tier>=4 or univ
        has_bp_or_univ = any("_bp_" in k or "_univ" in k for k in ebe)
        lines.append(f"[3d] 16-3 has blueprint/univ: {'PASS' if has_bp_or_univ else 'FAIL'} keys={sorted(ebe.keys())}")
    else:
        lines.append("[3d] 16-3 MISSING")

    # sum check
    max_err = 0.0
    bad_n = 0
    for s in stages:
        sm = sum(s["expected_by_equip"].values())
        sm2 = sum(f["expected"] for f in s["fixed_drops"]) + sum(
            it["expected"] for p in s["random_pools"] for it in p["items"]
        )
        err = abs(sm - sm2)
        max_err = max(max_err, err)
        if err >= 1e-6:
            bad_n += 1
    lines.append(f"[4] expected sum consistency: max_err={max_err:.3e} bad={bad_n} {'PASS' if bad_n==0 else 'FAIL'}")

    # equip coverage
    all_keys = set()
    for s in stages:
        all_keys |= set(s["expected_by_equip"])
    eq_keys = {e["id"] for e in data["equips"]}
    missing = sorted(all_keys - eq_keys)
    lines.append(f"[5] equips cover all keys: {'PASS' if not missing else 'FAIL'} missing={missing[:10]}")

    # apply_token
    bad_tok = []
    for s in stages:
        if s["difficulty_code"] == 0:
            expect = f"{s['area']}-{s['stage']}-"
        else:
            expect = f"h{s['area']}-{s['stage']}-"
        if s["apply_token"] != expect or s["id"] + "-" != s["apply_token"]:
            bad_tok.append((s["id"], s["apply_token"], expect))
    lines.append(f"[6] apply_token form: {'PASS' if not bad_tok else 'FAIL'} bad={bad_tok[:5]}")

    n_rand = sum(1 for s in stages if s["random_pools"])
    n_fixed_only = sum(1 for s in stages if s["fixed_drops"] and not s["random_pools"])
    n_empty = sum(1 for s in stages if not s["fixed_drops"] and not s["random_pools"])
    max_area = max(s["area"] for s in stages) if stages else 0
    lines.append(
        f"[7] stats: with_random_pools={n_rand}, fixed_only={n_fixed_only}, empty={n_empty}, max_area={max_area}, total={len(stages)}"
    )
    return lines


def eq_kind_from_key(k: str) -> str:
    if "_univ" in k:
        return "universal_blueprint"
    if "_bp_" in k:
        return "blueprint"
    return "gear"


def tier_from_key(k: str, ebe, data) -> int:
    for e in data["equips"]:
        if e["id"] == k:
            return int(e["tier"])
    return 0


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Fetching Schale DB …")
    stages = as_map(fetch_json(URL_STAGES))
    equipment = as_map(fetch_json(URL_EQUIPMENT))
    groups = as_map(fetch_json(URL_GROUPS))
    items = as_map(fetch_json(URL_ITEMS))
    students = as_map(fetch_json(URL_STUDENTS))
    print(
        f"  stages={len(stages)} equipment={len(equipment)} groups={len(groups)} "
        f"items={len(items)} students={len(students)}"
    )

    equip_data = build_equip_export(stages, equipment, groups)
    stone_data = build_secretstone_export(stages, items, students)

    out_equip = os.path.join(OUT_DIR, "equip_stages_cn.json")
    out_equip_pretty = os.path.join(OUT_DIR, "equip_stages_cn.pretty.json")
    out_stone = os.path.join(OUT_DIR, "secretstone_stages_cn.json")
    out_stone_pretty = os.path.join(OUT_DIR, "secretstone_stages_cn.pretty.json")

    with open(out_equip, "w", encoding="utf-8") as f:
        json.dump(equip_data, f, ensure_ascii=False, separators=(",", ":"))
    with open(out_equip_pretty, "w", encoding="utf-8") as f:
        json.dump(equip_data, f, ensure_ascii=False, indent=2)
    with open(out_stone, "w", encoding="utf-8") as f:
        json.dump(stone_data, f, ensure_ascii=False, separators=(",", ":"))
    with open(out_stone_pretty, "w", encoding="utf-8") as f:
        json.dump(stone_data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {out_equip}")
    print(f"Wrote {out_equip_pretty}")
    print(f"Wrote {out_stone}")
    print(f"Wrote {out_stone_pretty}")

    print("\n======== 装备表校验 ========")
    for line in validate_equip(equip_data):
        print(line)

    print("\n======== 14-1 详情 ========")
    s141 = next(s for s in equip_data["stages"] if s["id"] == "14-1")
    print("summary_cn:", s141["summary_cn"])
    print("random_pools:")
    print(json.dumps(s141["random_pools"], ensure_ascii=False, indent=2))
    print("fixed_drops:")
    print(json.dumps(s141["fixed_drops"], ensure_ascii=False, indent=2))
    print("expected_by_equip:", json.dumps(s141["expected_by_equip"], ensure_ascii=False))

    print("\n======== 前 20 个普通 apply_token ========")
    normals = [s for s in equip_data["stages"] if s["difficulty_code"] == 0][:20]
    tokens = [s["apply_token"] for s in normals]
    print("".join(tokens))
    print(tokens)

    print("\n======== 神名文字校验 ========")
    print(f"stones={len(stone_data['stones'])} stages_with_drops={len(stone_data['stages'])}")
    print(f"stats={stone_data['stats']}")
    # sample h1-1
    sh = next((s for s in stone_data["stages"] if s["id"] == "h1-1"), None)
    if sh:
        print("h1-1:", json.dumps(sh, ensure_ascii=False, indent=2)[:800])
    matched = sum(1 for s in stone_data["stones"] if s.get("student_id"))
    print(f"student matched: {matched}/{len(stone_data['stones'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
