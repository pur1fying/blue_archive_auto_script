from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from service.transport import ChannelClosed, ChannelEndpoint
from service.types import SyncPatchMessage, SyncPullMessage
from service.utils.diff import PatchConflictError

_logger = logging.getLogger(__name__)


class SyncChannelHandler:
    def __init__(self, service_context: Any) -> None:
        self.context = service_context

    async def handle(self, endpoint: ChannelEndpoint) -> None:
        queue = await self.context.config_manager.subscribe_updates()
        send_lock = asyncio.Lock()
        sender = asyncio.create_task(self._send_updates(endpoint, queue, send_lock))
        try:
            while True:
                message = await endpoint.recv_json()
                response = await self._handle_message(message)
                async with send_lock:
                    await endpoint.send_json(response)
        finally:
            sender.cancel()
            with suppress(asyncio.CancelledError):
                await sender
            self.context.config_manager.unsubscribe_updates(queue)

    async def _send_updates(
        self, endpoint: ChannelEndpoint, queue: asyncio.Queue, send_lock: asyncio.Lock
    ) -> None:
        try:
            while True:
                payload = dict(await queue.get())
                payload.setdefault("direction", "push")
                async with send_lock:
                    await endpoint.send_json(payload)
        except (asyncio.CancelledError, ChannelClosed):
            return

    async def _handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        msg_type = message.get("type")
        if msg_type == "pull":
            data = SyncPullMessage(**message)
            snapshot = await self.context.config_manager.get_snapshot(data.resource, data.resource_id)
            return {
                "type": "snapshot",
                "resource": data.resource,
                "resource_id": data.resource_id,
                "timestamp": snapshot.timestamp,
                "data": snapshot.data,
            }
        if msg_type == "patch":
            data = SyncPatchMessage(**message)
            try:
                await self.context.config_manager.apply_patch(
                    data.resource, data.resource_id, data.ops, data.timestamp, origin="frontend"
                )
            except PatchConflictError as exc:
                snapshot = await self.context.config_manager.get_snapshot(data.resource, data.resource_id)
                _logger.info(
                    "Sync patch conflict resource=%s resource_id=%s request_timestamp=%s snapshot_timestamp=%s",
                    data.resource,
                    data.resource_id,
                    data.timestamp,
                    snapshot.timestamp,
                )
                return {
                    "type": "patch_conflict",
                    "resource": data.resource,
                    "resource_id": data.resource_id,
                    "request_timestamp": data.timestamp,
                    "timestamp": snapshot.timestamp,
                    "data": snapshot.data,
                    "error": str(exc),
                }
            return {
                "type": "patch_ack",
                "resource": data.resource,
                "resource_id": data.resource_id,
                "timestamp": data.timestamp,
            }
        if msg_type == "list":
            snapshot = await self.context.config_manager.get_config_list()
            return {"type": "config_list", "timestamp": snapshot.timestamp, "data": snapshot.data}
        raise ValueError(f"Unsupported sync message: {msg_type}")
