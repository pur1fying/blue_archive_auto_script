import re
from dataclasses import dataclass
from typing import Iterable, Optional


def _student_id(name: str) -> str:
    normalized = name.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _alias_key(name: str) -> str:
    return name.strip().casefold()


@dataclass(frozen=True)
class StudentRecord:
    student_id: str
    canonical_name: str
    aliases: tuple[str, ...]


class StudentCatalog:
    """Canonical student identifiers and multilingual aliases."""

    def __init__(self, student_rows: Iterable[dict]):
        records: dict[str, StudentRecord] = {}
        for row in student_rows:
            canonical_name = str(row.get("Global_name", "")).strip()
            if not canonical_name:
                continue
            sid = _student_id(canonical_name)
            aliases = tuple(
                dict.fromkeys(
                    str(row.get(key, "")).strip()
                    for key in ("Global_name", "CN_name", "JP_name")
                    if str(row.get(key, "")).strip()
                )
            )
            if sid in records:
                previous = records[sid]
                records[sid] = StudentRecord(
                    student_id=sid,
                    canonical_name=previous.canonical_name,
                    aliases=tuple(dict.fromkeys(previous.aliases + aliases)),
                )
            else:
                records[sid] = StudentRecord(sid, canonical_name, aliases)

        self.records = records
        self._aliases: dict[str, str] = {}
        for sid, record in records.items():
            self._aliases[_alias_key(record.canonical_name)] = sid
            for alias in record.aliases:
                self._aliases[_alias_key(alias)] = sid

    def resolve(self, name: str) -> Optional[StudentRecord]:
        sid = self._aliases.get(_alias_key(name))
        return self.records.get(sid) if sid else None

    def record(self, student_id: str) -> Optional[StudentRecord]:
        return self.records.get(student_id)

    def validate_names(self, names: Iterable[str]) -> tuple[list[str], list[str]]:
        valid: list[str] = []
        unknown: list[str] = []
        for raw_name in names:
            name = raw_name.strip()
            if not name:
                continue
            record = self.resolve(name)
            if record is None:
                unknown.append(name)
            else:
                valid.append(record.canonical_name)
        return valid, unknown
