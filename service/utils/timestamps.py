from __future__ import annotations

import time
from pathlib import Path


def unix_timestamp_ms() -> float:
    return time.time() * 1000


def file_mtime_ms(path: Path) -> float:
    return path.stat().st_mtime * 1000
