"""Business and manifest contracts for portable bundled compute examples."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from types import ModuleType
from pathlib import Path

import pytest

from service.plugins.schema import validate_manifest, validate_value, with_defaults

ROOT = Path(__file__).resolve().parents[2]
BUNDLED = ROOT / "service/plugins/bundled"


def load_plugin(plugin_id, *, external=False):
    directory = (ROOT / "examples/plugins" if external else BUNDLED) / plugin_id
    manifest = json.loads((directory / "plugin.json").read_text(encoding="utf-8"))
    source = directory / "main.py"
    module = ModuleType(plugin_id.replace(".", "_"))
    module.__file__ = str(source)
    exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), module.__dict__)
    return manifest, module.run


def call(plugin_id, inputs=None, settings=None, *, external=False):
    manifest, run = load_plugin(plugin_id, external=external)
    action = manifest["actions"][0]
    settings = with_defaults(manifest["settings_schema"], settings or {})
    inputs = with_defaults(action["input_schema"], inputs or {})
    validate_value(manifest["settings_schema"], settings)
    validate_value(action["input_schema"], inputs)
    context = {"api_version": 1, "plugin_id": plugin_id, "config_id": "test-profile", "settings": settings}
    result = run(context, inputs)
    validate_value(action["output_schema"], result)
    json.dumps(result, allow_nan=False)
    return result


@pytest.mark.parametrize("plugin_id,external", [
    ("baas.ap-budget", False), ("baas.resource-budget", False), ("example.notes", True),
])
def test_manifest_is_portable_bilingual_and_has_a_valid_example(plugin_id, external):
    manifest, _ = load_plugin(plugin_id, external=external)
    validate_manifest(manifest)
    assert set(manifest["name"]) >= {"en", "zh"}
    assert set(manifest["description"]) >= {"en", "zh"}
    assert manifest["permissions"] == ["compute"]
    call(plugin_id, external=external)


def test_ap_budget_accounts_for_prior_purchases_and_future_windows():
    result = call("baas.ap-budget", {
        "current_ap": 120, "stored_ap": 200, "target_ap": 1000,
        "hours_remaining": 24, "purchase_days": 2, "purchases_today": 1,
    })
    assert result["natural_recovery_ap"] == 240
    assert result["available_before_purchases"] == 560
    assert result["required_purchases"] == result["planned_purchases"] == 4
    assert result["purchase_capacity"] == 5
    assert result["projected_ap"] == 1040
    assert result["remaining_shortfall"] == 0 and result["status"] == "planned"
    assert [row["purchases"] for row in result["days"]] == [2, 2]


def test_ap_recovery_rounds_down_and_never_exceeds_purchase_capacity():
    result = call("baas.ap-budget", {
        "current_ap": 0, "hours_remaining": 0.29, "purchase_days": 2,
        "purchases_today": 20, "target_ap": 1000,
    }, {"daily_purchase_limit": 1})
    assert result["natural_recovery_ap"] == 2
    assert result["planned_purchases"] == 1
    assert result["remaining_shortfall"] == 878 and result["status"] == "shortfall"
    assert [row["purchases"] for row in result["days"]] == [0, 1]


def test_ap_free_income_can_cover_target_without_purchases():
    result = call("baas.ap-budget", {"target_ap": 100, "hours_remaining": 0})
    assert result["status"] == "covered" and result["planned_purchases"] == 0


def test_ap_zero_purchase_limit_is_a_valid_budget():
    result = call("baas.ap-budget", {"hours_remaining": 0, "purchase_days": 31},
                  {"daily_purchase_limit": 0})
    assert result["purchase_capacity"] == result["planned_purchases"] == 0
    assert result["remaining_shortfall"] == 880


def test_resource_budget_default_plan_reaches_target_and_respects_limits():
    result = call("baas.resource-budget")
    assert result["required_runs"] == result["planned_runs"] == 19
    assert result["required_ap"] == result["planned_ap"] == 380
    assert result["projected_tokens"] == 1010 and result["surplus_tokens"] == 10
    assert result["remaining_shortfall"] == 0 and result["status"] == "planned"
    assert [row["runs"] for row in result["days"]] == [7, 6, 6]


def test_resource_budget_reports_shortfall_with_bonus_and_total_ap_limit():
    result = call("baas.resource-budget", {
        "current_tokens": 200, "target_tokens": 1000, "days_remaining": 3,
        "free_tokens_daily": 50, "available_ap": 200, "daily_ap_budget": 80,
    }, {"bonus_percent": 50})
    assert result["tokens_per_run_after_bonus"] == 60
    assert result["required_runs"] == 11 and result["required_ap"] == 220
    assert result["planned_runs"] == 10 and result["planned_ap"] == 200
    assert result["projected_tokens"] == 950 and result["remaining_shortfall"] == 50
    assert result["status"] == "shortfall"


def test_resource_budget_does_not_turn_unusable_daily_ap_into_extra_runs():
    result = call("baas.resource-budget", {
        "current_tokens": 0, "free_tokens_daily": 0, "available_ap": 1000,
        "daily_ap_budget": 19, "days_remaining": 3,
    })
    assert result["planned_runs"] == result["planned_ap"] == 0
    assert result["remaining_shortfall"] == 1000


def test_resource_bonus_rounds_down_per_run_and_free_income_can_cover_target():
    result = call("baas.resource-budget", {"target_tokens": 200},
                  {"tokens_per_run": 3, "bonus_percent": 12.5})
    assert result["tokens_per_run_after_bonus"] == 3
    assert result["status"] == "covered" and result["planned_runs"] == 0


@pytest.mark.parametrize("total_ap,daily_ap,days", [(0, 0, 1), (399, 99, 7), (10000, 39, 90)])
def test_resource_schedule_conserves_budget_and_reported_income(total_ap, daily_ap, days):
    result = call("baas.resource-budget", {
        "target_tokens": 1000000, "current_tokens": 0, "free_tokens_daily": 1,
        "available_ap": total_ap, "daily_ap_budget": daily_ap, "days_remaining": days,
    })
    assert sum(row["runs"] for row in result["days"]) == result["planned_runs"]
    assert sum(row["ap"] for row in result["days"]) == result["planned_ap"] <= total_ap
    assert all(row["ap"] <= daily_ap for row in result["days"])
    assert sum(row["tokens"] for row in result["days"]) == result["projected_tokens"]
    assert result["remaining_shortfall"] + result["projected_tokens"] == 1000000


def test_template_settings_and_unicode_output_are_valid():
    result = call("example.notes", {"note": "Collect cafe AP"},
                  {"prefix": "Daily plan"}, external=True)
    assert result == {"text": "Daily plan\nCollect cafe AP", "characters": 26, "lines": 2}
    result = call("example.notes", {"note": "ﬃ" * 2000},
                  {"prefix": "ﬃ" * 80, "uppercase": True}, external=True)
    assert result["characters"] == 6241
    assert result["text"].startswith("FFI")


@pytest.mark.parametrize("plugin_id,setting", [
    ("baas.ap-budget", {"ap_per_purchase": 0}),
    ("baas.resource-budget", {"ap_per_run": 0}),
    ("baas.resource-budget", {"tokens_per_run": True}),
])
def test_direct_entrypoints_reject_invalid_divisor_settings(plugin_id, setting):
    _, run = load_plugin(plugin_id)
    with pytest.raises(ValueError):
        run({"settings": setting}, {})


@pytest.mark.parametrize("plugin_id,external", [
    ("baas.ap-budget", False), ("baas.resource-budget", False), ("example.notes", True),
])
def test_examples_run_in_the_actual_isolated_worker(plugin_id, external):
    manifest, _ = load_plugin(plugin_id, external=external)
    action = manifest["actions"][0]
    directory = (ROOT / "examples/plugins" if external else BUNDLED) / plugin_id
    request = {
        "entrypoint": action["entrypoint"],
        "context": {"api_version": 1, "plugin_id": plugin_id, "config_id": "test-profile",
                    "settings": with_defaults(manifest["settings_schema"], {})},
        "input": with_defaults(action["input_schema"], {}),
    }
    worker = ROOT / "service/plugins/worker.py"
    environment = {key: os.environ[key] for key in (
        "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL",
    ) if key in os.environ}
    process = subprocess.run(
        [sys.executable, "-I", "-B", str(worker), str(directory)],
        input=json.dumps(request, ensure_ascii=False).encode("utf-8"), capture_output=True, timeout=5,
        env=environment,
    )
    assert process.returncode == 0 and process.stderr == b""
    assert json.loads(process.stdout.decode("utf-8")) == {"ok": True, "result": call(plugin_id, external=external)}
