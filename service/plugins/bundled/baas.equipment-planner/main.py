"""Portable equipment/Eleph farming tools migrated from upstream PR #583.

The bundled CN Schale snapshot is intentionally explicit; it is not a live JP
or Global drop table. Expected drops are estimates, never guaranteed outcomes.
The two weighted greedy strategies follow the reference calculator; they do
not claim a globally optimal integer/linear-programming solution.
"""
import json
import math
from pathlib import Path
import re

SLOTS = ("necklace", "watch", "charm", "hairpin", "badge", "bag", "shoes", "gloves", "hat")
RANKS = ("S1", "S2", "S3", "S4", "S5", "Z2", "Z3", "Z4")
RANK_COSTS = (30, 80, 100, 120, 120, 180, 200)


def _table():
    return json.loads(Path(__file__).with_name("stages-cn.json").read_text(encoding="utf-8"))


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Integer is outside the supported range.")
    return value


def _multiplier(inputs):
    value = inputs.get("drop_multiplier", 1)
    if type(value) not in (int, float) or not math.isfinite(value) or not 1 <= value <= 3:
        raise ValueError("Drop multiplier must be between one and three.")
    return float(value)


def _round(value):
    return round(value, 6)


def _sweeps(rows, hard):
    return ",".join(f"{row['stage_id'].lstrip('h')}-{row['runs']}" for row in rows
                    if row["stage_id"].startswith("h") == hard)


def _yield_rows(totals, equipment):
    return [{"equipment_id": key, "slot": equipment[key]["slot"], "tier": equipment[key]["tier"],
             "kind": equipment[key]["kind"], "expected": _round(value)}
            for key, value in sorted(totals.items()) if value > 0]


def catalog(context, inputs):
    table = _table()
    students = sorted({row["student"] for row in table["eleph"]})
    return {"region": "CN", "source": table["source"], "source_commit": table["source_commit"],
            "max_area": max(int(s["id"].lstrip("h").split("-")[0]) for s in table["stages"]),
            "max_tier": max(row["tier"] for row in table["equipment"]), "students": students}


def plan(context, inputs):
    table, mult = _table(), _multiplier(inputs)
    equipment = {row["id"]: row for row in table["equipment"]}
    max_tier = max(row["tier"] for row in table["equipment"])
    remaining, initial, seen = {}, {}, set()
    for row in inputs.get("needs", []):
        slot = row["slot"]
        if slot not in SLOTS:
            raise ValueError("Unknown equipment slot.")
        tier = _integer(row["tier"], 1, max_tier)
        quantity = _integer(row["quantity"], 0, 1000000)
        owned = _integer(row.get("owned", 0), 0, 1000000)
        key = (slot, tier)
        if key in seen:
            raise ValueError("Each slot/tier must appear only once.")
        seen.add(key)
        if quantity > owned:
            remaining[key] = initial[key] = quantity - owned
    if not inputs.get("include_normal", True) and not inputs.get("include_hard", False):
        raise ValueError("At least one difficulty must be enabled.")
    strategy = inputs.get("strategy", "high_random")
    if strategy not in {"high_random", "low_fixed"}:
        raise ValueError("Unknown farming strategy.")
    max_area = _integer(inputs.get("max_area", 30), 1, 30)
    max_stages = _integer(inputs.get("max_stages", 10), 1, 30)
    hard_limit = _integer(inputs.get("hard_runs_per_stage", 3), 1, 6)
    normal_limit = _integer(inputs.get("normal_runs_limit", 9999), 1, 9999)
    candidates = []
    for stage in table["stages"]:
        hard = stage["id"].startswith("h")
        if int(stage["id"].lstrip("h").split("-")[0]) > max_area:
            continue
        if (hard and not inputs.get("include_hard", False)) or (not hard and not inputs.get("include_normal", True)):
            continue
        expected, fixed = {}, {}
        for key, amount in stage["expected"].items():
            meta = equipment[key]
            if meta["tier"]:
                need_key = (meta["slot"], meta["tier"])
                expected[need_key] = expected.get(need_key, 0) + amount * mult
        for key, amount in stage["fixed"].items():
            meta = equipment[key]
            if meta["tier"]:
                need_key = (meta["slot"], meta["tier"])
                fixed[need_key] = fixed.get(need_key, 0) + amount * mult
        candidates.append((stage, expected, fixed))
    rows, totals, normal_used = [], {}, 0
    while remaining and len(rows) < max_stages:
        best = None
        for stage, expected, fixed in candidates:
            hard = stage["id"].startswith("h")
            capacity = hard_limit if hard else normal_limit - normal_used
            if capacity <= 0:
                continue
            useful = 0
            for (slot, tier), gap in remaining.items():
                amount = expected.get((slot, tier), 0)
                if strategy == "low_fixed":
                    guaranteed = fixed.get((slot, tier), 0)
                    amount = guaranteed + max(0, amount - guaranteed) * 0.25
                weight = 1 + (max(0, tier - 1) * 0.55 if strategy == "high_random" else max(0, 10 - tier) * 0.12)
                order = 1 + max(0, 12 - SLOTS.index(slot)) * 0.04
                useful += min(gap, amount) * weight * (1 + min(gap, 30) / 15) * order
            score = useful / stage["ap"]
            if score > 0 and (best is None or score > best[0]):
                best = (score, stage, expected, capacity)
        if best is None:
            break
        _, stage, expected, capacity = best
        runs = min(capacity, max(math.ceil(gap / expected[key] - 1e-10)
                                 for key, gap in remaining.items() if expected.get(key, 0) > 0))
        hard = stage["id"].startswith("h")
        if not hard:
            normal_used += runs
        rows.append({"stage_id": stage["id"], "runs": runs, "ap": stage["ap"] * runs})
        for key, value in stage["expected"].items():
            totals[key] = totals.get(key, 0) + value * mult * runs
        remaining = {key: max(0, gap - expected.get(key, 0) * runs) for key, gap in remaining.items()
                     if gap - expected.get(key, 0) * runs > 1e-8}
        candidates = [row for row in candidates if row[0]["id"] != stage["id"]]
    return {"region": "CN", "status": "covered" if not initial else "planned" if not remaining else "partial",
            "strategy": strategy, "total_ap": sum(row["ap"] for row in rows), "plan": rows,
            "normal_sweep": _sweeps(rows, False), "hard_sweep": _sweeps(rows, True),
            "remaining": [{"slot": slot, "tier": tier, "quantity": _round(gap)} for (slot, tier), gap in sorted(remaining.items())],
            "yields": _yield_rows(totals, equipment)}


def estimate(context, inputs):
    table, mult = _table(), _multiplier(inputs)
    stages = {row["id"]: row for row in table["stages"]}
    equipment = {row["id"]: row for row in table["equipment"]}
    text = inputs.get("sweeps", "").replace("，", ",")
    merged = {}
    for part in text.split(","):
        match = re.fullmatch(r"\s*([hH]?)([1-9][0-9]*)-([1-9][0-9]*)-([1-9][0-9]*)\s*", part)
        if not match:
            raise ValueError("Use stage-runs syntax, for example 14-1-15,h14-1-3.")
        prefix, area, number, runs = match.groups()
        stage = ("h" if prefix else "") + f"{int(area)}-{int(number)}"
        if stage not in stages:
            raise ValueError("Stage is not present in the bundled CN snapshot.")
        merged[stage] = _integer(merged.get(stage, 0) + int(runs), 1, 9999)
    if len(merged) > 64:
        raise ValueError("Too many sweep stages.")
    rows, totals = [], {}
    for stage_id, runs in merged.items():
        stage = stages[stage_id]
        rows.append({"stage_id": stage_id, "runs": runs, "ap": stage["ap"] * runs})
        for key, amount in stage["expected"].items():
            totals[key] = totals.get(key, 0) + amount * mult * runs
    return {"region": "CN", "total_ap": sum(row["ap"] for row in rows), "plan": rows,
            "normal_sweep": _sweeps(rows, False), "hard_sweep": _sweeps(rows, True),
            "yields": _yield_rows(totals, equipment)}


def eleph(context, inputs):
    table, mult = _table(), _multiplier(inputs)
    limit = _integer(inputs.get("max_area", 30), 1, 30)
    per_day = _integer(inputs.get("runs_per_stage_daily", 3), 1, 6)
    plans, sweeps, seen = [], {}, set()
    for student in inputs.get("students", []):
        name = student["name"].strip()
        current, target = student["current_rank"], student["target_rank"]
        if current not in RANKS or target not in RANKS or RANKS.index(target) < RANKS.index(current):
            raise ValueError("Target rank must be at least the current rank.")
        if name in seen or not any(row["student"] == name for row in table["eleph"]):
            raise ValueError("Student must be unique and have a known CN hard-stage drop.")
        seen.add(name)
        owned = _integer(student.get("owned", 0), 0, 1000000)
        need = max(0, sum(RANK_COSTS[RANKS.index(current):RANKS.index(target)]) - owned)
        stages = [row for row in table["eleph"] if row["student"] == name
                  and int(row["stage"].lstrip("h").split("-")[0]) <= limit]
        daily = sum(row["expected"] for row in stages) * mult * per_day
        days = math.ceil(need / daily - 1e-10) if need and daily else 0
        rows = [{"stage_id": row["stage"], "runs": per_day, "ap": row["ap"] * per_day} for row in stages] if need else []
        for row in rows:
            sweeps[row["stage_id"]] = row
        plans.append({"name": name, "fragments_needed": need, "expected_daily": _round(daily if need else 0),
                      "estimated_days": days, "status": "covered" if not need else "planned" if daily else "unavailable",
                      "stages": rows})
    rows = list(sweeps.values())
    return {"region": "CN", "students": plans, "hard_sweep": _sweeps(rows, True),
            "daily_ap": sum(row["ap"] for row in rows)}
