from __future__ import annotations

import asyncio
import json
import logging
import logging.handlers
import os
import sys
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SYSTEM_LOG_DIR = Path("config") / "logs"
SYSTEM_LOG_FILE = "baas-service.jsonl"
SYSTEM_LOG_MAX_BYTES = 10 * 1024 * 1024
SYSTEM_LOG_BACKUP_COUNT = 5
SYSTEM_LOG_HANDLER_MARKER = "_baas_system_log_handler"
NOISY_DEPENDENCY_LOG_LEVELS = {
    "PIL": logging.WARNING,
    "urllib3": logging.WARNING,
}
_exception_hooks_installed = False


class JsonLineFormatter(logging.Formatter):
    """Formats one complete, machine-readable log record per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "source": "python",
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def system_log_path(project_root: Path) -> Path:
    return project_root / SYSTEM_LOG_DIR / SYSTEM_LOG_FILE


def configure_dependency_log_levels() -> None:
    """Keep high-frequency dependency diagnostics out of the system log."""
    for logger_name, level in NOISY_DEPENDENCY_LOG_LEVELS.items():
        logging.getLogger(logger_name).setLevel(level)


def configure_system_logging(project_root: Path) -> Path:
    """Attach the persistent DEBUG handler and global exception hooks."""
    path = system_log_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    configure_dependency_log_levels()
    for handler in root.handlers:
        if getattr(handler, SYSTEM_LOG_HANDLER_MARKER, False):
            return path

    file_handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=SYSTEM_LOG_MAX_BYTES,
        backupCount=SYSTEM_LOG_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    setattr(file_handler, SYSTEM_LOG_HANDLER_MARKER, True)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonLineFormatter())
    root.addHandler(file_handler)

    logging.captureWarnings(True)
    _install_exception_hooks()
    logging.getLogger(__name__).info(
        "Python system logging initialized path=%s pid=%s cwd=%s",
        path,
        os.getpid(),
        Path.cwd(),
    )
    return path


def install_asyncio_exception_handler(loop: asyncio.AbstractEventLoop) -> None:
    previous = loop.get_exception_handler()

    def handle_exception(event_loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
        exception = context.get("exception")
        message = str(context.get("message") or "Unhandled asyncio exception")
        logging.getLogger("baas.asyncio").error(
            "%s context=%s",
            message,
            {key: repr(value) for key, value in context.items() if key != "exception"},
            exc_info=(type(exception), exception, exception.__traceback__) if exception else None,
        )
        if previous is not None:
            previous(event_loop, context)

    loop.set_exception_handler(handle_exception)


def read_system_logs(
    project_root: Path,
    limit: int = 2000,
    level: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 10000))
    selected_level = level.strip().upper() if level else ""
    selected_query = query.strip().lower() if query else ""
    records: deque[Dict[str, Any]] = deque(maxlen=limit)

    path = system_log_path(project_root)
    paths = [Path(f"{path}.{index}") for index in range(SYSTEM_LOG_BACKUP_COUNT, 0, -1)]
    paths.append(path)
    for candidate in paths:
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8", errors="replace") as stream:
                for raw_line in stream:
                    entry = _parse_log_line(raw_line)
                    if selected_level and entry.get("level", "").upper() != selected_level:
                        continue
                    if selected_query and selected_query not in json.dumps(entry, ensure_ascii=False).lower():
                        continue
                    records.append(entry)
        except OSError as exc:
            logging.getLogger(__name__).warning("Failed to read system log %s: %s", candidate, exc)
    return list(records)


def clear_system_logs(project_root: Path) -> None:
    path = system_log_path(project_root)
    root = logging.getLogger()
    truncated = False
    for handler in root.handlers:
        if not getattr(handler, SYSTEM_LOG_HANDLER_MARKER, False):
            continue
        handler.acquire()
        try:
            if handler.stream is not None:
                handler.stream.seek(0)
                handler.stream.truncate(0)
                handler.flush()
                truncated = True
        finally:
            handler.release()

    if not truncated:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    for index in range(1, SYSTEM_LOG_BACKUP_COUNT + 1):
        rotated = Path(f"{path}.{index}")
        try:
            rotated.unlink(missing_ok=True)
        except OSError:
            logging.getLogger(__name__).exception("Failed to remove rotated system log %s", rotated)


def system_log_files(project_root: Path) -> List[Dict[str, Any]]:
    path = system_log_path(project_root)
    files = [path] + [Path(f"{path}.{index}") for index in range(1, SYSTEM_LOG_BACKUP_COUNT + 1)]
    result: List[Dict[str, Any]] = []
    for candidate in files:
        if not candidate.exists():
            continue
        try:
            stat = candidate.stat()
        except OSError:
            continue
        result.append(
            {
                "path": str(candidate),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )
    return result


def _parse_log_line(raw_line: str) -> Dict[str, Any]:
    line = raw_line.rstrip("\r\n")
    try:
        value = json.loads(line)
        if isinstance(value, dict):
            value.setdefault("source", "python")
            return value
    except json.JSONDecodeError:
        pass
    return {
        "source": "python",
        "timestamp": "",
        "level": "INFO",
        "logger": "legacy",
        "message": line,
    }


def _install_exception_hooks() -> None:
    global _exception_hooks_installed
    if _exception_hooks_installed:
        return
    _exception_hooks_installed = True
    previous_sys_hook = sys.excepthook

    def sys_hook(exc_type, exc_value, traceback) -> None:
        logging.getLogger("baas.unhandled").critical(
            "Unhandled process exception",
            exc_info=(exc_type, exc_value, traceback),
        )
        previous_sys_hook(exc_type, exc_value, traceback)

    sys.excepthook = sys_hook

    if hasattr(threading, "excepthook"):
        previous_thread_hook = threading.excepthook

        def thread_hook(args) -> None:
            logging.getLogger("baas.unhandled.thread").critical(
                "Unhandled thread exception thread=%s",
                getattr(args.thread, "name", "unknown"),
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
            previous_thread_hook(args)

        threading.excepthook = thread_hook
