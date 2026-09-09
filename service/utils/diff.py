from __future__ import annotations

import copy
from typing import Any, Iterable, List


class PatchConflictError(Exception):
    """Raised when an incoming patch cannot be applied cleanly."""


def _escape_segment(segment: str) -> str:
    return segment.replace("~", "~0").replace("/", "~1")


def _unescape_segment(segment: str) -> str:
    return segment.replace("~1", "/").replace("~0", "~")


def _split_path(path: str) -> List[str]:
    if path in ("", "/"):
        return []
    if not path.startswith("/"):
        raise PatchConflictError(f"Invalid json-pointer path: '{path}'")
    raw_segments = path.split("/")[1:]
    return [_unescape_segment(seg) for seg in raw_segments]


def _resolve_parent(document: Any, segments: Iterable[str]) -> tuple[Any, str]:
    segments = list(segments)
    if not segments:
        raise PatchConflictError("Cannot resolve empty path segments")
    target = document
    for seg in segments[:-1]:
        if isinstance(target, dict):
            if seg not in target:
                raise PatchConflictError(f"Missing key '{seg}' while resolving path")
            target = target[seg]
        elif isinstance(target, list):
            try:
                index = int(seg)
            except ValueError as exc:
                raise PatchConflictError(f"Invalid list index '{seg}'") from exc
            if index < 0 or index >= len(target):
                raise PatchConflictError(f"List index {index} out of range")
            target = target[index]
        else:
            raise PatchConflictError(f"Cannot traverse into non-container type at segment '{seg}'")
    return target, segments[-1]


def apply_patch(document: Any, operations: Iterable[dict[str, Any]]) -> Any:
    current = document
    for op in operations:
        operation = op.get("op")
        path = op.get("path", "")
        value = op.get("value")
        segments = _split_path(path)

        if not segments:
            if operation == "replace" or operation == "add":
                current = copy.deepcopy(value)
            elif operation == "remove":
                raise PatchConflictError("Cannot remove the document root")
            else:
                raise PatchConflictError(f"Unsupported operation '{operation}'")
            continue

        parent, last_seg = _resolve_parent(current, segments)

        if isinstance(parent, dict):
            if operation == "add" or operation == "replace":
                parent[last_seg] = copy.deepcopy(value)
            elif operation == "remove":
                if last_seg not in parent:
                    raise PatchConflictError(f"Key '{last_seg}' not found for removal")
                del parent[last_seg]
            else:
                raise PatchConflictError(f"Unsupported operation '{operation}'")
        elif isinstance(parent, list):
            if last_seg == "-":
                index = len(parent)
            else:
                try:
                    index = int(last_seg)
                except ValueError as exc:
                    raise PatchConflictError(f"Invalid list index '{last_seg}'") from exc
            if operation == "add":
                if index < 0 or index > len(parent):
                    raise PatchConflictError(f"List index {index} out of range for add")
                parent.insert(index, copy.deepcopy(value))
            elif operation == "replace":
                if index < 0 or index >= len(parent):
                    raise PatchConflictError(f"List index {index} out of range for replace")
                parent[index] = copy.deepcopy(value)
            elif operation == "remove":
                if index < 0 or index >= len(parent):
                    raise PatchConflictError(f"List index {index} out of range for remove")
                parent.pop(index)
            else:
                raise PatchConflictError(f"Unsupported operation '{operation}'")
        else:
            raise PatchConflictError("Target container must be dict or list")

    return current


def _diff_dict(old: dict[str, Any], new: dict[str, Any], base_path: str) -> List[dict[str, Any]]:
    ops: List[dict[str, Any]] = []
    old_keys = set(old.keys())
    new_keys = set(new.keys())

    for removed in old_keys - new_keys:
        path = f"{base_path}/{_escape_segment(removed)}" if base_path else f"/{_escape_segment(removed)}"
        ops.append({"op": "remove", "path": path})

    for added in new_keys - old_keys:
        path = f"{base_path}/{_escape_segment(added)}" if base_path else f"/{_escape_segment(added)}"
        ops.append({"op": "add", "path": path, "value": copy.deepcopy(new[added])})

    for common in old_keys & new_keys:
        path = f"{base_path}/{_escape_segment(common)}" if base_path else f"/{_escape_segment(common)}"
        ops.extend(diff_documents(old[common], new[common], path))

    return ops


def diff_documents(old: Any, new: Any, base_path: str = "") -> List[dict[str, Any]]:
    if isinstance(old, dict) and isinstance(new, dict):
        return _diff_dict(old, new, base_path)
    if isinstance(old, list) and isinstance(new, list):
        if old == new:
            return []
        return [{"op": "replace", "path": base_path or "", "value": copy.deepcopy(new)}]
    if old != new:
        return [{"op": "replace", "path": base_path or "", "value": copy.deepcopy(new)}]
    return []
