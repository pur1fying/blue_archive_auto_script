from __future__ import annotations

import asyncio

from service.remote import ScrcpyProxySession


class _Stream:
    def encrypt(self, payload: bytes) -> bytes:
        return b"enc:" + payload

    def decrypt(self, payload: bytes) -> bytes:
        return payload.removeprefix(b"enc:")


class _Client:
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


def test_scrcpy_proxy_session_lifecycle():
    async def scenario():
        client = _Client()
        proxy = ScrcpyProxySession(client, _Stream(), encrypt_adb_to_ws=True)
        await proxy.run(object())
        encrypted = client.callbacks[1](b"frame")
        decrypted = client.callbacks[0](b"enc:touch")
        await proxy.close()
        return client, encrypted, decrypted

    client, encrypted, decrypted = asyncio.run(scenario())

    assert client.initialized is True
    assert client.proxied is True
    assert client.stopped is True
    assert client.callbacks == (None, None)
    assert encrypted == b"enc:frame"
    assert decrypted == b"touch"
