import json
import os
import stat
import time
from pathlib import Path
from tempfile import NamedTemporaryFile


def write_json_atomic(path, data, *, indent):
    """Publish a complete UTF-8 document in one rename."""
    path = Path(path).resolve()
    # The watchfiles default filter ignores backup names ending in '~'.
    stream = NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                prefix=f".{path.name}.", suffix="~", delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            json.dump(data, stream, ensure_ascii=False, indent=indent)
        try:
            temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        except FileNotFoundError:
            pass  # First save.
        for attempt in range(4):
            try:
                os.replace(temporary, path)
                break
            except PermissionError as exc:
                # Windows readers can briefly hold the destination without delete sharing.
                if getattr(exc, "winerror", None) not in (5, 32) or attempt == 3:
                    raise
                time.sleep(0.01 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)
