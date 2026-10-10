from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any

from service.transport import ChannelClosed, ChannelEndpoint
from service.types import ProviderRequest


class ProviderChannelHandler:
    def __init__(self, service_context: Any) -> None:
        self.context = service_context

    async def handle(self, endpoint: ChannelEndpoint) -> None:
        send_lock = asyncio.Lock()
        log_queue = await self.context.log_manager.subscribe()
        status_queue = await self.context.runtime.subscribe_status()
        tasks = []
        try:
            history = self.context.log_manager.get_history()
            scopes = self.context.log_manager.get_scopes()
            await endpoint.send_json({"type": "logs_full", "scopes": scopes, "entries": history})
            await endpoint.send_json({"type": "status", "status": self.context.runtime.current_status()})
            if self.context.runtime.is_all_data_initialized:
                await endpoint.send_json({"type": "status", "status": {"is_all_data_initialized": True}})
            tasks.extend(
                [
                    asyncio.create_task(self._send_queue(endpoint, log_queue, "log", send_lock)),
                    asyncio.create_task(self._send_queue(endpoint, status_queue, "status", send_lock)),
                ]
            )
            while True:
                message = await endpoint.recv_json()
                req_type = message.get("type")
                if req_type == "static_request":
                    ProviderRequest(**message)
                    snapshot = await self.context.config_manager.get_static_snapshot()
                    response = {
                        "type": "static_snapshot",
                        "timestamp": snapshot.timestamp,
                        "data": snapshot.data,
                    }
                elif req_type == "status_request":
                    response = {"type": "status", "status": self.context.runtime.current_status()}
                else:
                    raise ValueError(f"Unsupported provider message: {req_type}")
                async with send_lock:
                    await endpoint.send_json(response)
        finally:
            for task in tasks:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            self.context.log_manager.unsubscribe(log_queue)
            self.context.runtime.unsubscribe_status(status_queue)

    @staticmethod
    async def _send_queue(
        endpoint: ChannelEndpoint,
        queue: asyncio.Queue,
        envelope_type: str,
        send_lock: asyncio.Lock,
    ) -> None:
        try:
            while True:
                payload = await queue.get()
                key = "status" if envelope_type == "status" else "entry"
                async with send_lock:
                    await endpoint.send_json({"type": envelope_type, key: payload})
        except (asyncio.CancelledError, ChannelClosed):
            return
