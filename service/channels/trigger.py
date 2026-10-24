from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from service.api.commands import execute_command
from service.transport import ChannelEndpoint
from service.types import CommandMessage


class TriggerChannelHandler:
    def __init__(self, service_context: Any) -> None:
        self.context = service_context

    async def handle(self, endpoint: ChannelEndpoint) -> None:
        send_lock = asyncio.Lock()
        while True:
            command = CommandMessage(**(await endpoint.recv_json()))
            binary = None
            if command.command == "import_config" and command.payload.get("binary") is True:
                binary = await endpoint.recv_bytes()
            await self._dispatch(endpoint, send_lock, command, binary)

    async def _dispatch(
        self,
        endpoint: ChannelEndpoint,
        send_lock: asyncio.Lock,
        command: CommandMessage,
        binary: Optional[bytes],
    ) -> None:
        if command.command in ("test_all_sha_stream", "update_to_latest_stream"):
            try:
                iterator = (
                    self.context.runtime.test_all_sha_stream(
                        command.payload.get("channel"), command.payload.get("timeout")
                    )
                    if command.command == "test_all_sha_stream"
                    else self.context.runtime.update_to_latest_stream()
                )
                async for result in iterator:
                    await self._send_response(
                        endpoint, send_lock, command, {"status": "ok", "data": result}
                    )
                response: Dict[str, Any] = {"status": "ok", "data": {"done": True}}
            except Exception as exc:  # noqa: BLE001 - returned to the client
                response = {"status": "error", "error": str(exc), "data": {"done": True}}
            await self._send_response(endpoint, send_lock, command, response)
            return

        try:
            response = await execute_command(command, binary_payload=binary)
        except Exception as exc:  # noqa: BLE001 - returned to the client
            response = {"status": "error", "error": str(exc)}
        await self._send_response(endpoint, send_lock, command, response)

    @staticmethod
    async def _send_response(
        endpoint: ChannelEndpoint,
        send_lock: asyncio.Lock,
        command: CommandMessage,
        response: Dict[str, Any],
    ) -> None:
        binary = response.pop("_binary", None)
        if binary is not None:
            response.setdefault("data", {})["binary"] = {"size": len(binary)}
        async with send_lock:
            await endpoint.send_json(
                {
                    "type": "command_response",
                    "command": command.command,
                    **response,
                    "timestamp": command.timestamp,
                }
            )
            if binary is not None:
                await endpoint.send_bytes(binary)
