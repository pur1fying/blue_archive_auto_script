from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import requests

from core.Baas_thread import Baas_thread
from core.config.default_config import DEFAULT_CONFIG
from core.config.generated_user_config import Config
from core.pushkit import push


@pytest.mark.parametrize(
    "chat_id",
    [
        "123456789",
        "-1001234567890",
        "9007199254740993",
        "-9007199254740993",
        "@baas_test_channel",
        "",
    ],
)
def test_runtime_preserves_telegram_identifiers_through_notification_json(monkeypatch, chat_id):
    """Exercise the task config conversion and actual requests JSON serialization, offline."""
    values = json.loads(DEFAULT_CONFIG)
    values.update(
        push_after_completion=True,
        push_json="",
        push_serverchan="",
        push_feishu="",
        push_wecom="",
        push_telegram_bot_token="123456:offline-test-token",
        push_telegram_chat_id=chat_id,
        push_telegram_proxy="",
        push_telegram_api="",
        purchase_arena_ticket_times="3",
        screenshot_interval="0.25",
        rewarded_task_times="-1",
    )
    source = Config(**values)
    errors, infos, sent = [], [], []
    thread = Baas_thread.__new__(Baas_thread)
    thread.config_set = SimpleNamespace(config=source)
    thread.update_create_priority = lambda: None
    thread.logger = SimpleNamespace(error=errors.append, info=infos.append)

    def capture_send(_session, request, **_kwargs):
        sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"ok": true}'
        response.headers["Content-Type"] = "application/json"
        return response

    # Intercept before requests can open a socket; no Telegram request is sent.
    monkeypatch.setattr(requests.sessions.Session, "send", capture_send)

    assert thread.init_config() is True
    assert thread.config is not source
    assert type(thread.config.push_telegram_chat_id) is str
    assert thread.config.push_telegram_chat_id == chat_id
    assert source.push_telegram_chat_id == chat_id
    # Existing task settings continue to receive their original number conversion.
    assert type(thread.config.purchase_arena_ticket_times) is int
    assert thread.config.purchase_arena_ticket_times == 3
    assert type(thread.config.screenshot_interval) is float
    assert thread.config.screenshot_interval == 0.25
    assert thread.config.rewarded_task_times == -1

    push(thread.logger, thread.config)

    if chat_id:
        assert len(sent) == 1
        assert sent[0].method == "POST"
        payload = json.loads(sent[0].body)
        assert type(payload["chat_id"]) is str
        assert payload["chat_id"] == chat_id
        assert payload["text"] == "Baas Completed\nall activities finished"
        assert infos == ["[ Telegram ] push success"]
    else:
        assert sent == []
        assert infos == []
    assert errors == []
    assert "offline-test-token" not in " ".join(infos + errors)
