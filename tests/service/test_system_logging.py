from __future__ import annotations

import json
import logging
import logging.handlers
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from service.api import http
from service.system_logging import (
    JsonLineFormatter,
    clear_system_logs,
    read_system_logs,
    system_log_path,
)


def _write_entry(path: Path, **overrides) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "python",
        "timestamp": "2026-07-12T12:00:00+00:00",
        "level": "INFO",
        "logger": "test",
        "message": "service ready",
        **overrides,
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload) + "\n")


def test_json_formatter_keeps_diagnostic_context():
    formatter = JsonLineFormatter()
    record = logging.LogRecord(
        name="baas.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=42,
        msg="failure %s",
        args=("detail",),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["source"] == "python"
    assert payload["level"] == "ERROR"
    assert payload["logger"] == "baas.test"
    assert payload["message"] == "failure detail"
    assert payload["line"] == 42
    assert payload["process"] > 0


def test_read_system_logs_merges_rotations_and_filters(tmp_path):
    current = system_log_path(tmp_path)
    rotated = Path(f"{current}.1")
    _write_entry(rotated, level="DEBUG", message="old handshake")
    _write_entry(current, level="ERROR", message="backend failed")
    _write_entry(current, level="INFO", message="service ready")

    all_entries = read_system_logs(tmp_path, limit=10)
    error_entries = read_system_logs(tmp_path, limit=10, level="error")
    queried_entries = read_system_logs(tmp_path, limit=10, query="handshake")

    assert [entry["message"] for entry in all_entries] == [
        "old handshake",
        "backend failed",
        "service ready",
    ]
    assert [entry["message"] for entry in error_entries] == ["backend failed"]
    assert [entry["message"] for entry in queried_entries] == ["old handshake"]


def test_clear_system_logs_truncates_active_handler_and_backups(tmp_path):
    path = system_log_path(tmp_path)
    path.parent.mkdir(parents=True)
    handler = logging.handlers.RotatingFileHandler(path, encoding="utf-8")
    setattr(handler, "_baas_system_log_handler", True)
    handler.setFormatter(JsonLineFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        logging.getLogger("baas.test.clear").warning("before clear")
        handler.flush()
        _write_entry(Path(f"{path}.1"), message="rotated")

        clear_system_logs(tmp_path)

        assert path.read_text(encoding="utf-8") == ""
        assert not Path(f"{path}.1").exists()
    finally:
        root.removeHandler(handler)
        handler.close()


def test_system_log_http_contract(monkeypatch, tmp_path):
    _write_entry(system_log_path(tmp_path), level="WARNING", message="test warning")
    monkeypatch.setattr(http, "context", SimpleNamespace(project_root=tmp_path))
    monkeypatch.setattr(http, "_require_loopback", lambda request: None)
    app = FastAPI()
    app.include_router(http.router)
    client = TestClient(app)

    response = client.get("/system/logs?limit=50")

    assert response.status_code == 200
    assert response.json()["entries"][0]["message"] == "test warning"
    assert response.json()["files"][0]["path"].endswith("baas-service.jsonl")

    clear_response = client.post("/system/logs/clear")
    assert clear_response.status_code == 200
    assert clear_response.json() == {"ok": True}
