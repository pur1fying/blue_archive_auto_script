from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from service.auth import AuthenticationError
from service.types import CommandMessage

from .commands import execute_command
from .security import perform_business_resume, recv_stream_bytes, recv_stream_json, send_stream_bytes, send_stream_json
from .state import context

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.websocket("/ws/trigger")
async def websocket_trigger(websocket: WebSocket) -> None:
    try:
        _logger.debug("Trigger websocket connection started")
        _, stream = await perform_business_resume(websocket, channel="trigger")
        _logger.debug("Trigger websocket secure session resumed")
        while True:
            message = await recv_stream_json(websocket, stream)
            cmd = CommandMessage(**message)
            _logger.debug("Trigger command received command=%s", cmd.command)
            binary_payload = None
            if cmd.command == "import_config" and cmd.payload.get("binary") is True:
                binary_payload = await recv_stream_bytes(websocket, stream)
            response_payload: Dict[str, Any]
            if cmd.command == "test_all_sha_stream":
                try:
                    async for result in context.runtime.test_all_sha_stream(
                        cmd.payload.get("channel"),
                        cmd.payload.get("timeout"),
                    ):
                        await send_stream_json(
                            websocket,
                            stream,
                            {
                                "type": "command_response",
                                "command": cmd.command,
                                "status": "ok",
                                "data": result,
                                "timestamp": cmd.timestamp,
                            },
                        )
                    response_payload = {"status": "ok", "data": {"done": True}}
                except Exception as inner_exc:  # noqa: BLE001 - returned to frontend
                    _logger.exception("Streaming SHA test command failed: %s", inner_exc)
                    response_payload = {"status": "error", "error": str(inner_exc), "data": {"done": True}}
                await send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "command_response",
                        "command": cmd.command,
                        **response_payload,
                        "timestamp": cmd.timestamp,
                    },
                )
                continue
            if cmd.command == "update_to_latest_stream":
                try:
                    async for result in context.runtime.update_to_latest_stream():
                        await send_stream_json(
                            websocket,
                            stream,
                            {
                                "type": "command_response",
                                "command": cmd.command,
                                "status": "ok",
                                "data": result,
                                "timestamp": cmd.timestamp,
                            },
                        )
                    response_payload = {"status": "ok", "data": {"done": True}}
                except Exception as inner_exc:  # noqa: BLE001 - returned to frontend
                    _logger.exception("Streaming update command failed: %s", inner_exc)
                    response_payload = {"status": "error", "error": str(inner_exc), "data": {"done": True}}
                await send_stream_json(
                    websocket,
                    stream,
                    {
                        "type": "command_response",
                        "command": cmd.command,
                        **response_payload,
                        "timestamp": cmd.timestamp,
                    },
                )
                continue
            try:
                response_payload = await execute_command(cmd, binary_payload=binary_payload)
            except Exception as inner_exc:  # noqa: BLE001 - returned to frontend
                _logger.exception("Trigger command failed command=%s: %s", cmd.command, inner_exc)
                response_payload = {"status": "error", "error": str(inner_exc)}
            binary_response = response_payload.pop("_binary", None)
            if binary_response is not None:
                data = response_payload.setdefault("data", {})
                data["binary"] = {
                    "size": len(binary_response),
                }
            await send_stream_json(
                websocket,
                stream,
                {
                    "type": "command_response",
                    "command": cmd.command,
                    **response_payload,
                    "timestamp": cmd.timestamp,
                },
            )
            if binary_response is not None:
                await send_stream_bytes(websocket, stream, binary_response)
    except (AuthenticationError, HTTPException) as exc:
        _logger.warning("Trigger websocket authentication/protocol failure: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=4401, reason=str(exc))
    except WebSocketDisconnect:
        _logger.debug("Trigger websocket disconnected")
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        _logger.exception("Trigger websocket failed: %s", exc)
        with suppress(RuntimeError):
            await websocket.close(code=1011, reason=str(exc))
    finally:
        _logger.debug("Trigger websocket closed")
