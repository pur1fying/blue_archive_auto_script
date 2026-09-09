from __future__ import annotations

from typing import Any, Protocol


class ChannelClosed(Exception):
    """Raised when a transport endpoint is no longer usable."""


class ChannelEndpoint(Protocol):
    async def recv_json(self) -> dict[str, Any]: ...

    async def recv_bytes(self) -> bytes: ...

    async def send_json(self, payload: dict[str, Any]) -> None: ...

    async def send_bytes(self, payload: bytes) -> None: ...

    def configure_binary_encryption(self, enabled: bool) -> None: ...

    async def close(self) -> None: ...
