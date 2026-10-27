from __future__ import annotations

import asyncio
import secrets
from types import SimpleNamespace

from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient
import pytest

from service.api import commands, http, security, ws_trigger
from service.auth import ServiceAuthManager
from service.channels.trigger import TriggerChannelHandler
from service.plugins import PluginManager
from service.transport import ChannelClosed
from service.types import CommandMessage


@pytest.mark.parametrize("command", ["get_plugin_catalog", "set_plugin_enabled", "install_plugin", "run_plugin_action", "get_plugin_settings", "uninstall_plugin"])
def test_unauthenticated_sockets_cannot_reach_plugin_host(tmp_path, monkeypatch, command):
    auth = ServiceAuthManager(tmp_path)
    auth.initialize_password(secrets.token_urlsafe(24))
    manager = PluginManager(tmp_path, SimpleNamespace(), bundled_root=tmp_path / "bundled")
    context = SimpleNamespace(auth_manager=auth, runtime=SimpleNamespace(plugins=manager, current_status=lambda: {}))
    for module in (commands, http, security, ws_trigger):
        monkeypatch.setattr(module, "context", context)
    app = FastAPI()
    app.include_router(ws_trigger.router)
    app.include_router(http.router)
    with TestClient(app) as client:
        for path in ("/plugins", "/install_plugin", "/run_plugin_action"):
            assert client.post(path, json={"command": command}).status_code == 404
        health = client.get("/health").json()
        assert health["plugins_api_version"] == 1
        assert "plugins" not in health
        with client.websocket_connect("/ws/trigger") as socket:
            socket.send_json({"type": "command", "command": command, "timestamp": 1, "payload": {}})
            with pytest.raises(WebSocketDisconnect) as exc:
                socket.receive_json()
            assert exc.value.code == 4401
    assert not (tmp_path / "plugins").exists()


def test_authenticated_trigger_reads_install_binary_without_desynchronizing_next_command(monkeypatch):
    calls = []

    class Endpoint:
        def __init__(self):
            self.incoming = [
                {"type": "command", "command": "install_plugin", "timestamp": 1, "payload": {"binary": True}},
                {"type": "command", "command": "get_plugin_catalog", "timestamp": 2},
            ]
            self.sent = []

        async def recv_json(self):
            if not self.incoming:
                raise ChannelClosed()
            return self.incoming.pop(0)

        async def recv_bytes(self):
            return b"archive"

        async def send_json(self, value):
            self.sent.append(value)

    async def execute(cmd, binary_payload=None):
        calls.append((cmd.command, binary_payload))
        return {"status": "ok", "data": {}}

    from service.channels import trigger
    monkeypatch.setattr(trigger, "execute_command", execute)
    endpoint = Endpoint()
    with pytest.raises(ChannelClosed):
        asyncio.run(TriggerChannelHandler(SimpleNamespace()).handle(endpoint))
    assert calls == [("install_plugin", b"archive"), ("get_plugin_catalog", None)]
    assert [r["timestamp"] for r in endpoint.sent] == [1, 2]


def test_plugin_command_errors_are_stable_and_do_not_leak_private_paths(tmp_path, monkeypatch):
    manager = PluginManager(tmp_path, SimpleNamespace(), bundled_root=tmp_path / "bundled")
    monkeypatch.setattr(commands, "context", SimpleNamespace(runtime=SimpleNamespace(plugins=manager)))
    command = CommandMessage(type="command", command="get_plugin_settings", config_id="../../secret", timestamp=1, payload={"plugin_id": "example.none"})
    result = asyncio.run(commands.execute_command(command))
    assert result["status"] == "error" and result["code"] == "PLUGIN_NOT_FOUND"
    assert str(tmp_path) not in str(result) and "../../" not in str(result)
