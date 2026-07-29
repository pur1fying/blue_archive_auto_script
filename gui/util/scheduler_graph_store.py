"""Persistence and validation for the scheduler dependency graph."""

from __future__ import annotations

import json
import math
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Mapping


class SchedulerGraphError(Exception):
    """Base error for scheduler graph persistence failures."""


class InvalidEventConfig(SchedulerGraphError):
    """Raised when event.json cannot supply valid scheduler records."""


class InvalidRelationship(SchedulerGraphError):
    """Raised when a dependency relationship is invalid."""


class InvalidTime(SchedulerGraphError):
    """Raised when a next-tick time is not in the table's accepted format."""


@dataclass(frozen=True)
class SchedulerEvent:
    func_name: str
    event_name: str
    enabled: bool
    next_tick: int
    pre_task: tuple[str, ...]
    post_task: tuple[str, ...]


@dataclass(frozen=True)
class SchedulerRelationship:
    kind: Literal["pre", "post"]
    owner_func: str
    related_func: str
    source_func: str
    target_func: str


class SchedulerGraphStore:
    """Read and narrowly update scheduler graph metadata on disk."""

    def __init__(self, config_dir: str | Path):
        self.config_dir = Path(config_dir)
        self.event_path = self.config_dir / "event.json"
        self.graph_path = self.config_dir / "scheduler_graph.json"

    def load_events(self) -> list[SchedulerEvent]:
        return self._events_from_records(self._read_event_records())

    def load_relationships(self) -> tuple[list[SchedulerRelationship], list[str]]:
        return self._relationships_from_events(self.load_events())

    @classmethod
    def _relationships_from_events(
        cls, events: list[SchedulerEvent]
    ) -> tuple[list[SchedulerRelationship], list[str]]:
        known_funcs = {event.func_name for event in events}
        relationships: list[SchedulerRelationship] = []
        warnings: list[str] = []

        for event in events:
            for related_func in event.pre_task:
                relationship = SchedulerRelationship(
                    kind="pre",
                    owner_func=event.func_name,
                    related_func=related_func,
                    source_func=related_func,
                    target_func=event.func_name,
                )
                cls._append_drawable_relationship(
                    relationship, known_funcs, relationships, warnings
                )
            for related_func in event.post_task:
                relationship = SchedulerRelationship(
                    kind="post",
                    owner_func=event.func_name,
                    related_func=related_func,
                    source_func=event.func_name,
                    target_func=related_func,
                )
                cls._append_drawable_relationship(
                    relationship, known_funcs, relationships, warnings
                )

        if cls._contains_cycle(
            [(item.source_func, item.target_func) for item in relationships]
        ):
            warnings.append("Scheduler dependency cycle detected in existing event data.")
        return relationships, warnings

    def add_relationship(self, kind: str, owner_func: str, related_func: str) -> None:
        records = self._read_event_records()
        events = self._events_from_records(records)
        self._validate_relationship_inputs(kind, owner_func, related_func, events)
        relation_key = self._relationship_key(kind)
        by_func = {event.func_name: event for event in events}
        owner = by_func[owner_func]

        if related_func in getattr(owner, relation_key):
            raise InvalidRelationship("The same dependency metadata already exists.")

        source_func, target_func = self._edge_for(kind, owner_func, related_func)
        existing, _warnings = self._relationships_from_events(events)
        edges = [(item.source_func, item.target_func) for item in existing]
        if self._path_exists(target_func, source_func, edges):
            raise InvalidRelationship("The dependency would close a scheduler cycle.")

        record = self._record_by_func(records, owner_func)
        record[relation_key].append(related_func)
        self._atomic_write_json(self.event_path, records)

    def remove_relationship(self, kind: str, owner_func: str, related_func: str) -> None:
        records = self._read_event_records()
        events = self._events_from_records(records)
        self._validate_relationship_inputs(kind, owner_func, related_func, events)
        relation_key = self._relationship_key(kind)
        record = self._record_by_func(records, owner_func)
        if related_func in record[relation_key]:
            record[relation_key].remove(related_func)
            self._atomic_write_json(self.event_path, records)

    def update_next_tick(self, func_name: str, time_text: str) -> None:
        if not isinstance(time_text, str):
            raise InvalidTime("Time must use YYYY-MM-DD HH:MM:SS local time.")
        try:
            parsed = datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise InvalidTime("Time must use YYYY-MM-DD HH:MM:SS local time.") from exc
        if parsed.strftime("%Y-%m-%d %H:%M:%S") != time_text:
            raise InvalidTime("Time must use YYYY-MM-DD HH:MM:SS local time.")

        records = self._read_event_records()
        self._events_from_records(records)
        record = self._record_by_func(records, func_name)
        record["next_tick"] = int(parsed.timestamp())
        self._atomic_write_json(self.event_path, records)

    def update_enabled(self, func_name: str, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise InvalidEventConfig("enabled must be a boolean.")
        records = self._read_event_records()
        self._events_from_records(records)
        record = self._record_by_func(records, func_name)
        record["enabled"] = enabled
        self._atomic_write_json(self.event_path, records)

    def load_positions(self) -> dict[str, tuple[float, float]]:
        try:
            with self.graph_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}

        if not isinstance(payload, dict) or payload.get("version") != 1:
            return {}
        positions = payload.get("positions")
        if not isinstance(positions, dict):
            return {}

        result: dict[str, tuple[float, float]] = {}
        for func_name, position in positions.items():
            if (
                not isinstance(func_name, str)
                or not isinstance(position, list)
                or len(position) != 2
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in position
                )
            ):
                return {}
            result[func_name] = (float(position[0]), float(position[1]))
        return result

    def save_positions(self, positions: Mapping[str, tuple[float, float]]) -> None:
        serialized: dict[str, list[float]] = {}
        for func_name, position in positions.items():
            if (
                not isinstance(func_name, str)
                or not isinstance(position, tuple)
                or len(position) != 2
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in position
                )
            ):
                raise InvalidEventConfig("Positions must map task names to numeric x/y tuples.")
            serialized[func_name] = [float(position[0]), float(position[1])]
        self._atomic_write_json(self.graph_path, {"version": 1, "positions": serialized})

    def _read_event_records(self) -> list[dict]:
        try:
            with self.event_path.open("r", encoding="utf-8") as file:
                records = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise InvalidEventConfig("Unable to read event.json.") from exc
        if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
            raise InvalidEventConfig("event.json must contain a list of event records.")
        return records

    @staticmethod
    def _events_from_records(records: list[dict]) -> list[SchedulerEvent]:
        events: list[SchedulerEvent] = []
        func_names: set[str] = set()
        required = ("func_name", "event_name", "enabled", "next_tick", "pre_task", "post_task")
        for record in records:
            if any(key not in record for key in required):
                raise InvalidEventConfig("Event record is missing scheduler fields.")
            if (
                not isinstance(record["func_name"], str)
                or not record["func_name"]
                or not isinstance(record["event_name"], str)
                or not isinstance(record["enabled"], bool)
                or isinstance(record["next_tick"], bool)
                or not isinstance(record["next_tick"], int)
                or not isinstance(record["pre_task"], list)
                or not isinstance(record["post_task"], list)
                or any(not isinstance(item, str) for item in record["pre_task"])
                or any(not isinstance(item, str) for item in record["post_task"])
            ):
                raise InvalidEventConfig("Event record has invalid scheduler field values.")
            if record["func_name"] in func_names:
                raise InvalidEventConfig("func_name values must be unique.")
            func_names.add(record["func_name"])
            events.append(
                SchedulerEvent(
                    func_name=record["func_name"],
                    event_name=record["event_name"],
                    enabled=record["enabled"],
                    next_tick=record["next_tick"],
                    pre_task=tuple(record["pre_task"]),
                    post_task=tuple(record["post_task"]),
                )
            )
        return events

    @staticmethod
    def _append_drawable_relationship(
        relationship: SchedulerRelationship,
        known_funcs: set[str],
        relationships: list[SchedulerRelationship],
        warnings: list[str],
    ) -> None:
        if relationship.related_func not in known_funcs:
            warnings.append(
                f"Unknown scheduler dependency '{relationship.related_func}' referenced by "
                f"'{relationship.owner_func}'."
            )
            return
        relationships.append(relationship)

    @staticmethod
    def _relationship_key(kind: str) -> str:
        if kind == "pre":
            return "pre_task"
        if kind == "post":
            return "post_task"
        raise InvalidRelationship("Relationship kind must be 'pre' or 'post'.")

    def _validate_relationship_inputs(
        self, kind: str, owner_func: str, related_func: str, events: list[SchedulerEvent]
    ) -> None:
        self._relationship_key(kind)
        known_funcs = {event.func_name for event in events}
        if owner_func not in known_funcs or related_func not in known_funcs:
            raise InvalidRelationship("Relationship tasks must exist in event.json.")
        if owner_func == related_func:
            raise InvalidRelationship("A scheduler task cannot depend on itself.")

    @staticmethod
    def _edge_for(kind: str, owner_func: str, related_func: str) -> tuple[str, str]:
        if kind == "pre":
            return related_func, owner_func
        return owner_func, related_func

    @staticmethod
    def _record_by_func(records: list[dict], func_name: str) -> dict:
        for record in records:
            if record["func_name"] == func_name:
                return record
        raise InvalidEventConfig(f"Unknown scheduler task '{func_name}'.")

    @classmethod
    def _contains_cycle(cls, edges: list[tuple[str, str]]) -> bool:
        adjacency: dict[str, list[str]] = {}
        for source, target in edges:
            adjacency.setdefault(source, []).append(target)
            adjacency.setdefault(target, [])
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(func_name: str) -> bool:
            if func_name in visiting:
                return True
            if func_name in visited:
                return False
            visiting.add(func_name)
            if any(visit(target) for target in adjacency[func_name]):
                return True
            visiting.remove(func_name)
            visited.add(func_name)
            return False

        return any(visit(func_name) for func_name in adjacency)

    @staticmethod
    def _path_exists(start: str, goal: str, edges: list[tuple[str, str]]) -> bool:
        adjacency: dict[str, list[str]] = {}
        for source, target in edges:
            adjacency.setdefault(source, []).append(target)
        pending = [start]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == goal:
                return True
            if current in visited:
                continue
            visited.add(current)
            pending.extend(adjacency.get(current, ()))
        return False

    @staticmethod
    def _atomic_write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.flush()
            os.replace(temp_path, path)
        except BaseException:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            raise
