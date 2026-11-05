"""Disposable trusted-code worker. This process is NOT a security sandbox.

Python's isolated mode and a minimal environment prevent accidental dependence
on host state, not deliberate filesystem/network access by a trusted plugin.
"""
from __future__ import annotations

import asyncio
import contextlib
import importlib
import inspect
import json
import os
from pathlib import Path
import re
import sys
import types

MAX_RESULT = 65536
MAX_REQUEST = 131072
ENTRYPOINT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*$")


def execute_request(package_dir: str, request: dict) -> dict:
    """Execute once in a disposable process, including Android service workers.

    This function uses only the standard library so an embedded Python helper
    can load this file directly without importing the backend service package.
    """
    response = {"ok": False, "code": "ACTION_FAILED", "message": "Plugin action failed."}
    old_path = list(sys.path)
    try:
        if (not isinstance(request, dict) or not isinstance(request.get("entrypoint"), str)
                or not ENTRYPOINT.fullmatch(request["entrypoint"])
                or not isinstance(request.get("context"), dict) or not isinstance(request.get("input"), dict)
                or len(json.dumps(request, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_REQUEST):
            raise ValueError("invalid request")
        root = Path(package_dir).resolve()
        module_name, function_name = request["entrypoint"].split(":")
        candidate = root.joinpath(*module_name.split("."))
        source = candidate.with_suffix(".py")
        package_source = candidate / "__init__.py"
        if not source.is_file() and not package_source.is_file():
            raise ValueError("missing entrypoint")
        sys.path.insert(0, str(root))
        package = types.ModuleType("_baas_plugin")
        package.__path__ = [str(root)]
        for name in list(sys.modules):
            if name == "_baas_plugin" or name.startswith("_baas_plugin."):
                del sys.modules[name]
        sys.modules["_baas_plugin"] = package
        # Third-party stdout/stderr are not a result channel and may contain secrets.
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            module = importlib.import_module("_baas_plugin." + module_name)
            function = getattr(module, function_name)
            result = function(request["context"], request["input"])
            if inspect.isawaitable(result):
                result = asyncio.run(result)
        content = json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(content) > MAX_RESULT:
            response = {"ok": False, "code": "RESULT_TOO_LARGE", "message": "Plugin result exceeds 64 KiB."}
        else:
            response = {"ok": True, "result": result}
    except BaseException:
        pass  # Do not send Python traceback, paths, settings or exception text to clients.
    finally:
        sys.path[:] = old_path
    return response


def main() -> None:
    output = sys.stdout
    try:
        content = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if len(content) > MAX_REQUEST:
            raise ValueError("request too large")
        response = execute_request(sys.argv[1], json.loads(content))
    except BaseException:
        response = {"ok": False, "code": "ACTION_FAILED", "message": "Plugin action failed."}
    encoded = json.dumps(response, ensure_ascii=False, allow_nan=False).encode("utf-8")
    output.buffer.write(encoded)
    output.buffer.flush()


if __name__ == "__main__":
    main()
