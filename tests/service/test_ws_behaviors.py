from __future__ import annotations

import asyncio
from service.api import ws_provider, ws_sync
from service.channels import RemoteChannelHandler
from service.transport import InMemoryChannelEndpoint
from service.transport.websocket_endpoint import WebSocketChannelEndpoint


class _Stream:
    def encrypt(self, payload: bytes) -> bytes:
        return b"encrypted:" + payload

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

    assert asyncio.run(scenario()) == [b'encrypted:{"type":"patch","direction":"push"}']


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

    assert asyncio.run(scenario()) == [b'encrypted:{"type":"status","status":{"running":false}}']


def test_websocket_endpoint_can_disable_binary_encryption_without_affecting_json():
    async def scenario():
        websocket = _WebSocket()
        endpoint = WebSocketChannelEndpoint(websocket, _Stream())
        endpoint.configure_binary_encryption(False)
        await endpoint.send_bytes(b"video")
        await endpoint.send_json({"type": "control"})
        return websocket.sent

    assert asyncio.run(scenario()) == [b"video", b'encrypted:{"type":"control"}']


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

    async def fake_require_remote(config_id):
        assert config_id == "default_config"
        return client

    async def scenario():
        endpoint = InMemoryChannelEndpoint()
        await endpoint.incoming.put({"config_id": "default_config", "decrypt": True})
        context = type("Context", (), {"runtime": type("Runtime", (), {"require_remote_": staticmethod(fake_require_remote)})()})()
        await RemoteChannelHandler(context).handle(endpoint)

    asyncio.run(scenario())

    assert client.initialized is True
    assert client.proxied is True
    assert client.callbacks == (None, None)
    assert client.stopped is True
