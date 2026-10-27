"""Estimate an AP budget without reading profiles or controlling a device.

The caller supplies the number of purchase windows. Natural recovery assumes
continuous recovery without a cap; expiry, actual game inventory and reset time
are deliberately outside this small mathematical model.
"""
from decimal import Decimal, ROUND_FLOOR
import math


def _integer(values, key, default, minimum, maximum):
    value = values.get(key, default)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{key} must be an integer between {minimum} and {maximum}.")
    return value


def _number(values, key, default, minimum, maximum):
    value = values.get(key, default)
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{key} must be a finite number between {minimum} and {maximum}.")
    return Decimal(str(value))


def run(context, inputs):
    settings = context.get("settings", {})
    rate = _number(settings, "recovery_per_hour", 10, 0, 60)
    purchase_ap = _integer(settings, "ap_per_purchase", 120, 1, 999)
    daily_limit = _integer(settings, "daily_purchase_limit", 3, 0, 20)
    current = _integer(inputs, "current_ap", 120, 0, 10000000)
    stored = _integer(inputs, "stored_ap", 0, 0, 10000000)
    target = _integer(inputs, "target_ap", 1000, 0, 10000000)
    hours = _number(inputs, "hours_remaining", 24, 0, 744)
    windows = _integer(inputs, "purchase_days", 1, 1, 31)
    used_today = _integer(inputs, "purchases_today", 0, 0, 20)

    recovered = int((rate * hours).to_integral_value(rounding=ROUND_FLOOR))
    base = current + stored + recovered
    deficit = max(0, target - base)
    needed = (deficit + purchase_ap - 1) // purchase_ap
    first_capacity = max(0, daily_limit - used_today)
    capacity = first_capacity + (windows - 1) * daily_limit
    planned = min(needed, capacity)
    remaining = planned
    days = []
    for day in range(1, windows + 1):
        limit = first_capacity if day == 1 else daily_limit
        count = min(remaining, limit)
        days.append({"day": day, "purchases": count, "ap": count * purchase_ap})
        remaining -= count
    projected = base + planned * purchase_ap
    return {
        "status": "covered" if deficit == 0 else "planned" if projected >= target else "shortfall",
        "natural_recovery_ap": recovered,
        "available_before_purchases": base,
        "required_purchases": needed,
        "planned_purchases": planned,
        "purchase_capacity": capacity,
        "projected_ap": projected,
        "remaining_shortfall": max(0, target - projected),
        "days": days,
    }
