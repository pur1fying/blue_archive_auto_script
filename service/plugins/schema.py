"""Small, deliberately closed JSON Schema dialect for portable forms and APIs."""
from __future__ import annotations

import copy
import json
import math
import re
from typing import Any

from .errors import PluginError, require

API_VERSION = 1
CAPABILITIES = ["compute", "device.tasks", "home.cards", "settings.schema.v1", "install", "uninstall", "host.automation.v1"]
PERMISSIONS = {"compute", "device.tasks"}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
ENTRY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$")
DEVICE_TASKS = frozenset({
    "group", "momo_talk", "common_shop", "cafe_reward", "no1_cafe_invite", "no2_cafe_invite",
    "lesson", "rewarded_task", "arena", "create", "explore_normal_task", "explore_hard_task",
    "mail", "main_story", "group_story", "mini_story", "scrimmage", "collect_reward",
    "normal_task", "hard_task", "clear_special_task_power", "de_clothes",
    "tactical_challenge_shop", "collect_daily_power", "total_assault", "restart",
    "refresh_uiautomator2", "activity_sweep", "explore_activity_story",
    "explore_activity_challenge", "explore_activity_mission", "dailyGameActivity", "friend",
    "joint_firing_drill", "pass", "collect_daily_free_power",
})
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def finite(value: Any) -> bool:
    try:
        return type(value) in {int, float} and math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def identifier(value: Any) -> str:
    require(isinstance(value, str) and len(value) <= 64 and ID_RE.fullmatch(value) is not None
            and value.split(".")[0] not in WINDOWS_RESERVED,
            "INVALID_ID", "Identifiers must use lowercase letters, numbers and separated dots, underscores or hyphens.")
    return value


def json_size(value: Any, maximum: int = 65536) -> bytes:
    def check_numbers(item, depth=0):
        require(depth <= 32, "INVALID_JSON", "JSON nesting exceeds the limit.")
        if type(item) in {int, float}:
            require(finite(item), "INVALID_JSON", "A finite JSON number is required.")
        elif isinstance(item, dict):
            for child in item.values():
                check_numbers(child, depth + 1)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check_numbers(child, depth + 1)
    check_numbers(value)
    try:
        content = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        raise PluginError("INVALID_JSON", "A finite JSON value is required.") from None
    require(len(content) <= maximum, "PAYLOAD_TOO_LARGE", "Plugin data exceeds its size limit.")
    return content


def localized(value: Any) -> bool:
    if isinstance(value, str):
        return 0 < len(value) <= 2000
    return (isinstance(value, dict) and 0 < len(value) <= 16
            and all(isinstance(k, str) and 0 < len(k) <= 32 and isinstance(v, str)
                    and 0 < len(v) <= 2000 for k, v in value.items()))


_COMMON = {"type", "title", "description", "default", "enum"}
_KEYS = {
    "object": _COMMON | {"properties", "required", "additionalProperties"},
    "array": _COMMON | {"items", "minItems", "maxItems"},
    "string": _COMMON | {"minLength", "maxLength", "format"},
    "integer": _COMMON | {"minimum", "maximum"},
    "number": _COMMON | {"minimum", "maximum"},
    "boolean": _COMMON,
    "null": _COMMON,
}


def validate_schema(schema: Any, depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [256]
    budget[0] -= 1
    require(depth <= 8 and budget[0] >= 0, "INVALID_SCHEMA", "Schema nesting or field count exceeds the limit.")
    require(isinstance(schema, dict) and schema.get("type") in _KEYS,
            "INVALID_SCHEMA", "Each schema must declare a supported type.")
    kind = schema["type"]
    if "format" in schema:
        require(kind == "string" and schema["format"] == "date-time",
                "INVALID_SCHEMA", "Only string date-time input hints are supported.")
    require(set(schema) <= _KEYS[kind], "INVALID_SCHEMA", "Unsupported schema keyword.")
    for field in ("title", "description"):
        if field in schema:
            require(localized(schema[field]), "INVALID_SCHEMA", "Schema labels must be localized text.")
    if "enum" in schema:
        require(isinstance(schema["enum"], list) and 1 <= len(schema["enum"]) <= 64,
                "INVALID_SCHEMA", "Schema enum must contain between 1 and 64 choices.")
    if kind == "object":
        props = schema.get("properties", {})
        require(isinstance(props, dict) and len(props) <= 64
                and all(isinstance(k, str) and 0 < len(k) <= 64 and k not in {"__proto__", "prototype", "constructor"} for k in props),
                "INVALID_SCHEMA", "Invalid object properties.")
        require(schema.get("additionalProperties", False) is False,
                "INVALID_SCHEMA", "Open object schemas are not supported.")
        required = schema.get("required", [])
        require(isinstance(required, list) and all(isinstance(k, str) and k in props for k in required)
                and len(required) == len(set(required)), "INVALID_SCHEMA", "Invalid required properties.")
        for child in props.values():
            validate_schema(child, depth + 1, budget)
    elif kind == "array":
        validate_schema(schema.get("items"), depth + 1, budget)
    for low, high, default_max in (("minItems", "maxItems", 256), ("minLength", "maxLength", 16384)):
        if low in _KEYS[kind]:
            lo, hi = schema.get(low, 0), schema.get(high, default_max)
            require(type(lo) is int and type(hi) is int and 0 <= lo <= hi <= default_max,
                    "INVALID_SCHEMA", "Invalid schema size bounds.")
    if kind in {"number", "integer"}:
        for key in ("minimum", "maximum"):
            if key in schema:
                value = schema[key]
                require(finite(value), "INVALID_SCHEMA", "Invalid numeric bound.")
        require(schema.get("minimum", -math.inf) <= schema.get("maximum", math.inf),
                "INVALID_SCHEMA", "Reversed numeric bounds.")
    if "default" in schema:
        validate_value(schema, schema["default"])
    if "enum" in schema:
        for choice in schema["enum"]:
            validate_value({k: v for k, v in schema.items() if k not in {"default", "enum"}}, choice)


def validate_value(schema: dict, value: Any, depth: int = 0) -> Any:
    require(depth <= 9, "INVALID_SETTINGS", "JSON nesting exceeds the limit.")
    kind = schema["type"]
    valid = {
        "object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "boolean": type(value) is bool,
        "integer": type(value) is int, "number": type(value) in {int, float}, "null": value is None,
    }[kind]
    require(valid, "INVALID_SETTINGS", "A value does not match its declared schema type.")
    if "enum" in schema:
        require(any(type(choice) is type(value) and choice == value for choice in schema["enum"]),
                "INVALID_SETTINGS", "A value is outside the allowed choices.")
    if kind == "object":
        props = schema.get("properties", {})
        require(set(value) <= set(props) and set(schema.get("required", [])) <= set(value),
                "INVALID_SETTINGS", "An object contains unknown fields or misses required fields.")
        for key, child in value.items():
            validate_value(props[key], child, depth + 1)
    elif kind == "array":
        require(schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 256),
                "INVALID_SETTINGS", "An array exceeds its bounds.")
        for child in value:
            validate_value(schema["items"], child, depth + 1)
    elif kind == "string":
        require(schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 16384),
                "INVALID_SETTINGS", "A string exceeds its bounds.")
    elif kind in {"number", "integer"}:
        require(finite(value) and schema.get("minimum", -math.inf) <= value <= schema.get("maximum", math.inf),
                "INVALID_SETTINGS", "A number exceeds its bounds.")
    return value


def with_defaults(schema: dict, value: Any = None) -> Any:
    if value is None:
        value = copy.deepcopy(schema.get("default", {} if schema["type"] == "object" else None))
    if schema["type"] == "object" and isinstance(value, dict):
        value = copy.deepcopy(value)
        for key, child in schema.get("properties", {}).items():
            if key not in value and "default" in child:
                value[key] = copy.deepcopy(child["default"])
            elif key in value:
                value[key] = with_defaults(child, value[key])
    return value


def validate_manifest(data: Any) -> dict:
    require(isinstance(data, dict), "INVALID_MANIFEST", "Plugin manifest must be an object.")
    allowed = {"schema_version", "api_version", "id", "version", "name", "description", "author",
               "permissions", "settings_schema", "actions", "contributions"}
    require(set(data) <= allowed, "INVALID_MANIFEST", "Unknown manifest fields.")
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "INCOMPATIBLE_SCHEMA", "Unsupported plugin manifest version.")
    require(type(data.get("api_version")) is int and data["api_version"] == API_VERSION,
            "INCOMPATIBLE_API", "Unsupported plugin API version.")
    identifier(data.get("id"))
    require(isinstance(data.get("version"), str) and re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", data["version"]) is not None,
            "INVALID_MANIFEST", "Plugin version must be a semantic version.")
    require(localized(data.get("name")) and localized(data.get("description")), "INVALID_MANIFEST", "Plugin name and description are required.")
    if "author" in data:
        require(isinstance(data["author"], str) and len(data["author"]) <= 256, "INVALID_MANIFEST", "Invalid author.")
    perms = data.get("permissions")
    require(isinstance(perms, list) and all(isinstance(p, str) and p in PERMISSIONS for p in perms)
            and len(perms) == len(set(perms)), "UNSUPPORTED_PERMISSION", "Unsupported or duplicated plugin permission.")
    validate_schema(data.get("settings_schema"))
    require(data["settings_schema"]["type"] == "object", "INVALID_SCHEMA", "Settings must use an object schema.")
    actions = data.get("actions")
    require(isinstance(actions, list) and len(actions) <= 64, "INVALID_MANIFEST", "Plugin actions must be a bounded array.")
    action_ids = set()
    for action in actions:
        require(isinstance(action, dict) and set(action) <= {"id", "name", "description", "execution", "input_schema", "output_schema", "entrypoint", "task_name", "timeout_seconds"},
                "INVALID_MANIFEST", "Invalid action declaration.")
        action_id = identifier(action.get("id"))
        require(action_id not in action_ids, "DUPLICATE_ACTION", "Duplicate plugin action.")
        action_ids.add(action_id)
        require(localized(action.get("name")) and ("description" not in action or localized(action["description"])), "INVALID_MANIFEST", "Invalid action label.")
        validate_schema(action.get("input_schema"))
        require(action["input_schema"]["type"] == "object", "INVALID_SCHEMA", "Action input must be an object schema.")
        if "output_schema" in action:
            validate_schema(action["output_schema"])
        execution = action.get("execution")
        require(execution in {"compute", "device_task", "host_automation"}, "UNSUPPORTED_CAPABILITY", "Unsupported action execution mode.")
        permission = "compute" if execution == "compute" else "device.tasks"
        require(permission in perms, "MISSING_PERMISSION", "An action lacks its required permission.")
        if execution == "compute":
            require(isinstance(action.get("entrypoint"), str) and ENTRY_RE.fullmatch(action["entrypoint"]) is not None
                    and "task_name" not in action, "INVALID_ENTRYPOINT", "Invalid compute entrypoint.")
        elif execution == "host_automation":
            from .automation import HOST_ACTIONS
            require(action_id in HOST_ACTIONS.get(data["id"], ()) and "entrypoint" not in action and "task_name" not in action,
                    "UNSUPPORTED_AUTOMATION", "Host automation is reserved for declared bundled tools.")
        else:
            require(action.get("task_name") in DEVICE_TASKS and "entrypoint" not in action,
                    "UNSUPPORTED_TASK", "Device actions must reference a supported host task.")
        timeout = action.get("timeout_seconds", 30 if execution == "compute" else 1800)
        require(finite(timeout) and 0.1 <= timeout <= (120 if execution == "compute" else 604800 if execution == "host_automation" else 3600),
                "INVALID_MANIFEST", "Invalid action timeout.")
    contributions = data.get("contributions", {})
    require(isinstance(contributions, dict) and set(contributions) <= {"home"}, "UNSUPPORTED_CAPABILITY", "Unsupported plugin contribution.")
    cards = contributions.get("home", [])
    require(isinstance(cards, list) and len(cards) <= 8, "INVALID_MANIFEST", "Invalid home contributions.")
    card_ids = set()
    for card in cards:
        require(isinstance(card, dict) and set(card) <= {"id", "title", "description", "action_id"}, "INVALID_MANIFEST", "Invalid home card.")
        card_id = identifier(card.get("id"))
        require(card_id not in card_ids and localized(card.get("title"))
                and ("description" not in card or localized(card["description"]))
                and card.get("action_id") in action_ids, "INVALID_MANIFEST", "Home cards must reference declared actions.")
        card_ids.add(card_id)
    json_size(data, 262144)
    json_size(with_defaults(data["settings_schema"], {}))
    for action in actions:
        json_size(with_defaults(action["input_schema"], {}))
    return copy.deepcopy(data)
