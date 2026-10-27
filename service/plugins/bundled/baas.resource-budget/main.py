"""Plan deterministic event resource income from user-supplied yields.

No stage tables or drop probabilities are invented. Daily free income is assumed
to be collected on every supplied day; a run's bonus is rounded down separately.
"""
from decimal import Decimal, ROUND_FLOOR
import math


def _integer(values, key, default, minimum, maximum):
    value = values.get(key, default)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{key} must be an integer between {minimum} and {maximum}.")
    return value


def run(context, inputs):
    settings = context.get("settings", {})
    run_cost = _integer(settings, "ap_per_run", 20, 1, 100)
    base_yield = _integer(settings, "tokens_per_run", 40, 1, 100000)
    bonus = settings.get("bonus_percent", 0)
    if type(bonus) not in (int, float) or not math.isfinite(bonus) or not 0 <= bonus <= 1000:
        raise ValueError("bonus_percent must be a finite number between 0 and 1000.")
    run_yield = int((Decimal(base_yield) * (100 + Decimal(str(bonus))) / 100)
                    .to_integral_value(rounding=ROUND_FLOOR))
    current = _integer(inputs, "current_tokens", 100, 0, 10000000)
    target = _integer(inputs, "target_tokens", 1000, 0, 10000000)
    days = _integer(inputs, "days_remaining", 3, 1, 90)
    free_daily = _integer(inputs, "free_tokens_daily", 50, 0, 1000000)
    total_ap = _integer(inputs, "available_ap", 400, 0, 10000000)
    daily_ap = _integer(inputs, "daily_ap_budget", 160, 0, 10000)

    free_total = free_daily * days
    deficit = max(0, target - current - free_total)
    needed = (deficit + run_yield - 1) // run_yield
    per_day_limit = daily_ap // run_cost
    capacity = min(total_ap // run_cost, per_day_limit * days)
    planned = min(needed, capacity)
    each, extra = divmod(planned, days)
    schedule = []
    for day in range(1, days + 1):
        count = each + (1 if day <= extra else 0)
        schedule.append({"day": day, "runs": count, "ap": count * run_cost,
                         "tokens": count * run_yield + free_daily})
    projected = current + free_total + planned * run_yield
    return {
        "status": "covered" if deficit == 0 else "planned" if projected >= target else "shortfall",
        "tokens_per_run_after_bonus": run_yield,
        "free_tokens_total": free_total,
        "required_runs": needed,
        "required_ap": needed * run_cost,
        "affordable_runs": capacity,
        "planned_runs": planned,
        "planned_ap": planned * run_cost,
        "projected_tokens": projected,
        "remaining_shortfall": max(0, target - projected),
        "surplus_tokens": max(0, projected - target),
        "days": schedule,
    }
