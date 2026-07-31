"""Recover the deduplicated lesson portrait seed set from all Git history."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(__file__).with_name("data") / "historical_portraits"
HISTORICAL_ROOTS = tuple(
    f"src/images/{server}/lesson_affection"
    for server in (
        "CN",
        "JP",
        "Global_en-us",
        "Global_zh-tw",
        "Global_ko-kr",
    )
)
LABEL_ALIASES = {"Ar1s-maid": "Aris (Maid)"}
RAW_CHANGE = re.compile(
    r"^:[0-7]{6} [0-7]{6} ([0-9a-f]{40}) ([0-9a-f]{40}) [A-Z][0-9]*\t(.+)$"
)


@dataclass(frozen=True)
class HistoricalPortrait:
    label: str
    git_blob: str
    server: str
    source_path: str


def scan_historical_portraits(root: Path = ROOT) -> list[HistoricalPortrait]:
    """Return every distinct labelled portrait reachable from Git history.

    ``--no-renames`` makes both sides of a rename appear as ordinary delete/add
    records. Reading both the old and new blob of every change also recovers
    overwritten portrait versions, including the second Toki (Bunny) image.
    """
    output = subprocess.check_output(
        [
            "git",
            "log",
            "--all",
            "--raw",
            "--no-abbrev",
            "--no-renames",
            "--format=commit:%H",
            "--",
            *HISTORICAL_ROOTS,
        ],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
    )
    found: dict[tuple[str, str], HistoricalPortrait] = {}
    for line in output.splitlines():
        match = RAW_CHANGE.match(line)
        if match is None:
            continue
        old_blob, new_blob, source_path = match.groups()
        normalized_path = source_path.replace("\\", "/")
        if not normalized_path.lower().endswith(".png"):
            continue
        parts = normalized_path.split("/")
        if len(parts) < 5 or parts[-2] != "lesson_affection":
            continue
        server = parts[-3]
        raw_label = os.path.splitext(parts[-1])[0]
        label = LABEL_ALIASES.get(raw_label, raw_label)
        for blob in (old_blob, new_blob):
            if set(blob) == {"0"}:
                continue
            key = (label, blob)
            found.setdefault(
                key,
                HistoricalPortrait(label, blob, server, normalized_path),
            )
    return sorted(found.values(), key=lambda item: (item.label.casefold(), item.git_blob))


def read_git_blob(blob_hash: str, root: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", blob_hash], cwd=root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for portrait in scan_historical_portraits():
        raw = read_git_blob(portrait.git_blob)
        filename = f"{portrait.git_blob[:12]}.png"
        (args.output / filename).write_bytes(raw)
        manifest.append(
            {
                "label": portrait.label,
                "server": portrait.server,
                "source_path": portrait.source_path,
                "git_blob": portrait.git_blob,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "file": filename,
            }
        )
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(manifest)} distinct historical portraits to {args.output}")


if __name__ == "__main__":
    main()
