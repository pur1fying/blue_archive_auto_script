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
import sys
import types

MAX_RESULT = 65536


def main() -> None:
    output = sys.stdout
    response = {"ok": False, "code": "ACTION_FAILED", "message": "Plugin action failed."}
    try:
        request = json.loads(sys.stdin.buffer.read(131073))
        root = Path(sys.argv[1]).resolve()
        module_name, function_name = request["entrypoint"].split(":")
        candidate = root.joinpath(*module_name.split("."))
        source = candidate.with_suffix(".py")
        package_source = candidate / "__init__.py"
        if not source.is_file() and not package_source.is_file():
            raise ValueError("missing entrypoint")
        sys.path.insert(0, str(root))
        package = types.ModuleType("_baas_plugin")
        package.__path__ = [str(root)]
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
    encoded = json.dumps(response, ensure_ascii=False, allow_nan=False).encode("utf-8")
    output.buffer.write(encoded)
    output.buffer.flush()


if __name__ == "__main__":
    main()
