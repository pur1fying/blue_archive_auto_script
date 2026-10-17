from types import SimpleNamespace

import pytest
import requests

from core.ocr.baas_ocr_client import Client


@pytest.mark.parametrize("status", [200, 404])
def test_ready_root_returns_immediately(monkeypatch, status):
    calls = []
    response = SimpleNamespace(status_code=status, close=lambda: None)

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return response

    monkeypatch.setattr(Client.requests, "get", get)
    client = Client.BaasOcrClient.__new__(Client.BaasOcrClient)
    client.config = SimpleNamespace(base_url="http://127.0.0.1:1145")
    client.server_process = SimpleNamespace(poll=lambda: None)
    client._wait_for_server()
    assert calls == [(client.config.base_url, {"timeout": (0.02, 0.2)})]


def test_failed_process_does_not_report_ready(monkeypatch):
    client = Client.BaasOcrClient.__new__(Client.BaasOcrClient)
    client.server_process = SimpleNamespace(poll=lambda: 1)
    with pytest.raises(RuntimeError, match="exited"):
        client._wait_for_server()


def test_probe_retries_connection_failure_and_nonready_status(monkeypatch):
    ticks = iter([0, 0, 0.1, 0.2, 0.3])
    replies = iter([requests.ConnectionError("not listening"), 503, 404])
    closed = []
    monkeypatch.setattr(Client.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(Client.time, "sleep", lambda _: None)

    def get(*args, **kwargs):
        reply = next(replies)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(status_code=reply, close=lambda: closed.append(reply))

    monkeypatch.setattr(Client.requests, "get", get)
    client = Client.BaasOcrClient.__new__(Client.BaasOcrClient)
    client.config = SimpleNamespace(base_url="http://127.0.0.1:1145")
    client.server_process = SimpleNamespace(poll=lambda: None)
    client._wait_for_server()
    assert closed == [503, 404]


def test_probe_times_out_instead_of_silently_succeeding(monkeypatch):
    ticks = iter([0, 0, 31])
    monkeypatch.setattr(Client.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(Client.time, "sleep", lambda _: None)
    monkeypatch.setattr(Client.requests, "get", lambda *a, **k: SimpleNamespace(status_code=503, close=lambda: None))
    client = Client.BaasOcrClient.__new__(Client.BaasOcrClient)
    client.config = SimpleNamespace(base_url="http://127.0.0.1:1145")
    client.server_process = SimpleNamespace(poll=lambda: None)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        client._wait_for_server()
