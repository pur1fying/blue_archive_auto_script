from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional


def student_id(name: str) -> str:
    normalized = name.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


@dataclass(frozen=True)
class StudentRecord:
    student_id: str
    canonical_name: str
    aliases: tuple[str, ...]


class StudentCatalog:
    def __init__(self, rows: Iterable[dict]):
        self.records: dict[str, StudentRecord] = {}
        self._aliases: dict[str, str] = {}
        for row in rows:
            canonical = str(row.get("Global_name", "")).strip()
            if not canonical:
                continue
            sid = student_id(canonical)
            aliases = tuple(
                dict.fromkeys(
                    str(row.get(key, "")).strip()
                    for key in ("Global_name", "CN_name", "JP_name")
                    if str(row.get(key, "")).strip()
                )
            )
            if sid in self.records:
                raise ValueError("Duplicate student identity: " + canonical)
            record = StudentRecord(sid, canonical, aliases)
            self.records[sid] = record
            for alias in aliases:
                key = alias.casefold()
                if key in self._aliases and self._aliases[key] != sid:
                    raise ValueError("Duplicate student alias: " + alias)
                self._aliases[key] = sid

    def resolve(self, name: str) -> Optional[StudentRecord]:
        sid = self._aliases.get(name.strip().casefold())
        return self.records.get(sid) if sid else None

    def record(self, sid: str) -> Optional[StudentRecord]:
        return self.records.get(sid)

    def validate_names(self, names: Iterable[str]) -> tuple[list[str], list[str]]:
        valid: list[str] = []
        unknown: list[str] = []
        seen: set[str] = set()
        for raw_name in names:
            name = str(raw_name).strip()
            if not name:
                continue
            record = self.resolve(name)
            if record is None:
                unknown.append(name)
            elif record.student_id not in seen:
                valid.append(record.canonical_name)
                seen.add(record.student_id)
        return valid, unknown
