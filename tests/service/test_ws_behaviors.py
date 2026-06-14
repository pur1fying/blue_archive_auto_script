from __future__ import annotations

import asyncio
from types import SimpleNamespace

from service.api import ws_provider, ws_remote, ws_sync


class _Stream:
    def encrypt(self, payload: bytes) -> bytes:
        return payload

    def decrypt(self, payload: bytes) -> bytes:
        return payload


class _WebSocket:
    def __init__(self) -> None:
        self.sent = []

    async def send_bytes(self, payload: bytes):
        self.sent.append(payload)


def test_sync_sender_preserves_push_envelope():
    async def scenario():
        queue = asyncio.Queue()
        websocket = _WebSocket()
        await queue.put({"type": "patch"})
        task = asyncio.create_task(ws_sync.sync_sender(websocket, _Stream(), queue))
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return websocket.sent

    assert asyncio.run(scenario()) == [b'{"type":"patch","direction":"push"}']


def test_provider_sender_wraps_status_payload():
    async def scenario():
        queue = asyncio.Queue()
        websocket = _WebSocket()
        await queue.put({"running": False})
        task = asyncio.create_task(ws_provider.provider_sender(websocket, _Stream(), queue, "status"))
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return websocket.sent

    assert asyncio.run(scenario()) == [b'{"type":"status","status":{"running":false}}']


def test_remote_proxy_initializes_and_cleans_client(monkeypatch):
    class FakeClient:
        def __init__(self) -> None:
            self.alive = False
            self.callbacks = None
            self.initialized = False
            self.proxied = False
            self.stopped = False

        def set_proxy_callbacks(self, ws_to_adb=None, adb_to_ws=None):
            self.callbacks = (ws_to_adb, adb_to_ws)

        async def init(self):
            self.initialized = True
            self.alive = True

        async def proxy_websocket(self, websocket):
            self.proxied = True

        async def stop(self):
            self.stopped = True
            self.alive = False

    client = FakeClient()

    async def fake_resume(websocket, *, channel):
        return SimpleNamespace(), _Stream()

    async def fake_recv(websocket, stream):
        return {"config_id": "default_config", "decrypt": True}

    async def fake_require_remote(config_id):
        assert config_id == "default_config"
        return client

    monkeypatch.setattr(ws_remote, "perform_business_resume", fake_resume)
    monkeypatch.setattr(ws_remote, "recv_stream_json", fake_recv)
    monkeypatch.setattr(ws_remote, "context", SimpleNamespace(runtime=SimpleNamespace(require_remote_=fake_require_remote)))

    asyncio.run(ws_remote.websocket_remote(SimpleNamespace()))

    assert client.initialized is True
    assert client.proxied is True
    assert client.callbacks == (None, None)
    assert client.stopped is True
