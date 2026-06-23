from __future__ import annotations

from typing import Any, Dict

from service.types import CommandMessage

from .state import context


def _require_config_id(cmd: CommandMessage) -> str:
    if not cmd.config_id:
        raise ValueError(f"config_id is required for command '{cmd.command}'")
    return cmd.config_id


async def execute_command(cmd: CommandMessage, binary_payload: bytes | None = None) -> Dict[str, Any]:
    if cmd.command == "start_scheduler":
        if not cmd.config_id:
            raise ValueError("config_id is required for start_scheduler")
        result = await context.runtime.start_scheduler(
            cmd.config_id,
            set_log=context.ensure_runtime_logger_attached,
        )
        return {"status": "ok", "data": result}

    if cmd.command == "stop_scheduler":
        if not cmd.config_id:
            raise ValueError("config_id is required for stop_scheduler")
        result = await context.runtime.stop_scheduler(cmd.config_id)
        return {"status": "ok", "data": result}

    if cmd.command == "solve":
        if not cmd.config_id:
            raise ValueError("config_id is required for solve")
        task = cmd.payload.get("task")
        if not task:
            raise ValueError("task is required for solve command")
        result = await context.runtime.solve_task(
            cmd.config_id,
            task,
            set_log=context.ensure_runtime_logger_attached,
        )
        return {"status": "ok", "data": result}

    if cmd.command.startswith("start_"):
        config_id = _require_config_id(cmd)
        result = await context.runtime.solve_task(
            config_id=config_id,
            task_name=cmd.command,
            set_log=context.ensure_runtime_logger_attached,
        )
        return {"status": "ok", "data": result}

    if cmd.command.startswith("add_config"):
        name = cmd.payload.get("name")
        server = cmd.payload.get("server")
        if not server or not name:
            raise ValueError("server and name are required for add_config")
        result = await context.runtime.add_config(name, server)
        await context.config_manager.scan_once()
        return {"status": "ok", "data": result}

    if cmd.command.startswith("remove_config"):
        config_id = cmd.payload.get("id")
        if not config_id:
            raise ValueError("id is required for remove_config")
        result = await context.runtime.remove_config(config_id)
        await context.config_manager.scan_once()
        return {"status": "ok", "data": result}

    if cmd.command == "copy_config":
        config_id = cmd.payload.get("id")
        if not config_id:
            raise ValueError("id is required for copy_config")
        result = await context.runtime.copy_config(config_id)
        await context.config_manager.scan_once()
        return {"status": "ok", "data": result}

    if cmd.command == "export_config":
        config_id = cmd.payload.get("id")
        if not config_id:
            raise ValueError("id is required for export_config")
        result = await context.runtime.export_config(config_id)
        content = result.pop("content")
        return {"status": "ok", "data": result, "_binary": content}

    if cmd.command == "import_config":
        if binary_payload is None:
            raise ValueError("binary archive payload is required for import_config")
        result = await context.runtime.import_config(binary_payload)
        await context.config_manager.scan_once()
        return {"status": "ok", "data": result}

    if cmd.command == "detect_adb":
        result = await context.runtime.detect_adb()
        return {"status": "ok", "data": {"addresses": result}}

    if cmd.command == "valid_cdk":
        result = await context.runtime.valid_cdk(cmd.payload["cdk"], cmd.payload.get("channel"))
        return {"status": "ok", "data": result}

    if cmd.command == "test_all_sha":
        result = await context.runtime.test_all_sha(
            cmd.payload.get("channel"),
            cmd.payload.get("timeout"),
        )
        return {"status": "ok", "data": result}

    if cmd.command == "check_for_update":
        if "channel" in cmd.payload:
            await context.runtime.update_setup_toml({"channel": cmd.payload["channel"]})
        result = await context.runtime.check_for_update()
        return {"status": "ok", "data": result}

    if cmd.command == "update_setup_toml":
        result = await context.runtime.update_setup_toml(cmd.payload)
        return {"status": "ok", "data": result}

    if cmd.command == "update_to_latest":
        result = await context.runtime.update_to_latest()
        return {"status": "ok", "data": result}

    if cmd.command == "stop_all_tasks":
        result = await context.runtime.stop_all_tasks()
        return {"status": "ok", "data": result}

    if cmd.command == "control_device":
        config_id = _require_config_id(cmd)
        operation = cmd.payload.get("operation")
        if not operation:
            raise ValueError(f"operation is required for command '{cmd.command}'")
        result = await context.runtime.control_device_(config_id, operation)
        return {"status": "ok", "data": result}

    if cmd.command == "status":
        return {"status": "ok", "data": context.runtime.current_status()}

    raise ValueError(f"Unsupported command '{cmd.command}'")
