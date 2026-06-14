from __future__ import annotations

from contextlib import suppress
from typing import Any


class ScrcpyProxySession:
    """Owns callback setup and cleanup for one proxied scrcpy websocket."""

    def __init__(self, client: Any, stream: Any, *, encrypt_adb_to_ws: bool) -> None:
        """Create a proxy session.

        Args:
            client: Initialized-compatible `ScrcpyClient` instance.
            stream: Secret stream with `encrypt` and `decrypt` methods.
            encrypt_adb_to_ws: Whether bytes from ADB should be encrypted before websocket send.
        """
        self.client = client
        self.stream = stream
        self.encrypt_adb_to_ws = encrypt_adb_to_ws

    async def run(self, websocket) -> None:
        """Attach stream callbacks, initialize the client if needed, and proxy bytes.

        Args:
            websocket: Accepted FastAPI/Starlette websocket.
        """
        self.client.set_proxy_callbacks(
            ws_to_adb=lambda data: self.stream.decrypt(data),
            adb_to_ws=lambda data: self.stream.encrypt(data) if self.encrypt_adb_to_ws else data,
        )
        if not self.client.alive:
            await self.client.init()
        await self.client.proxy_websocket(websocket)

    async def close(self) -> None:
        """Clear callbacks and stop the scrcpy client if the proxy is still alive."""
        self.client.set_proxy_callbacks(None, None)
        if self.client.alive:
            with suppress(Exception):
                await self.client.stop()
