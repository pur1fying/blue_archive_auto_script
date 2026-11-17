import json
import math
from dataclasses import dataclass
from pathlib import Path

SERVER_LABELS = {
    "官服": "CN Official", "B服": "CN Bilibili", "国际服": "Global",
    "国际服青少年": "Global Teen", "韩国ONE": "Global ONE Store", "日服": "JP",
    "日服PC端": "JP PC", "Steam国际服": "Global Steam", "auto": "Auto",
}


def server_label(value):
    return SERVER_LABELS.get(value, value)


@dataclass(frozen=True)
class Job:
    config_id: str
    tasks: tuple
    timeout_seconds: float = 1800


def safe_id(value):
    if (not isinstance(value, str) or not value or value in {".", ".."}
            or any(c in value for c in '/\\:\x00') or value != value.strip()):
        raise ValueError("Config ID must name a single directory under config")
    return value


def load_plan(data, root, tasks):
    if not isinstance(data, dict) or type(data.get("version")) is not int or data.get("version") != 1:
        raise ValueError("Test plan must specify version: 1")
    if set(data) - {"version", "jobs", "task_timeout_seconds"}:
        raise ValueError("Test plan contains unknown fields")
    entries = data.get("jobs")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Select at least one config")
    seen, jobs = set(), []
    config_root = (root / "config").resolve()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - {"config_id", "tasks", "timeout_seconds"}:
            raise ValueError("Invalid job fields")
        config_id = safe_id(entry.get("config_id"))
        config_path = (config_root / config_id / "config.json").resolve()
        if config_root not in config_path.parents or not config_path.is_file():
            raise ValueError(f"Config is missing or outside the config directory: {config_id}")
        if config_id in seen:
            raise ValueError(f"Duplicate config: {config_id}; combine its tasks in one ordered list")
        seen.add(config_id)
        selected = entry.get("tasks")
        if not isinstance(selected, list) or not selected or any(not isinstance(t, str) or t not in tasks for t in selected):
            raise ValueError(f"{config_id}: Task list is empty or contains an unknown task")
        timeout = entry.get("timeout_seconds", data.get("task_timeout_seconds", 1800))
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Task timeout must be a positive finite number of seconds")
        jobs.append(Job(config_id, tuple(selected), float(timeout)))
    return jobs


def plan_data(jobs):
    return {"version": 1, "jobs": [{"config_id": j.config_id, "tasks": list(j.tasks),
                                    "timeout_seconds": j.timeout_seconds} for j in jobs]}


def read_config(root, config_id):
    return json.loads((root / "config" / safe_id(config_id) / "config.json").read_text(encoding="utf-8-sig"))
