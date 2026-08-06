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
LABEL_CORRECTIONS_BY_BLOB = {
    # These four Git blobs were stored under stale lesson template filenames.
    # Their identities were confirmed manually by the user.
    "ac63cee6faa2cbb496b5bc6e798544646e2e6dfc": "Noa (Pajamas)",
    "9cfd12b434c50c19d05a804f2983a2e274a0a306": "Saki",
    "d4f34f0e611285e0236fd3034f99e33c2193edc2": "Saki (Swimsuit)",
    "4074255cf5ec772f6b14203789fb892e673dd538": "Toki",
}
INVALID_FILENAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RAW_CHANGE = re.compile(
    r"^:[0-7]{6} [0-7]{6} ([0-9a-f]{40}) ([0-9a-f]{40}) [A-Z][0-9]*\t(.+)$"
)


@dataclass(frozen=True)
class HistoricalPortrait:
    label: str
    source_label: str
    git_blob: str
    server: str
    source_path: str


def _safe_filename_component(value: str) -> str:
    component = INVALID_FILENAME_CHARACTERS.sub("_", value).rstrip(" .")
    if not component:
        raise ValueError(f"Empty filename component after sanitizing {value!r}")
    return component


def historical_portrait_filename(portrait: HistoricalPortrait) -> str:
    return (
        f"{_safe_filename_component(portrait.label)}__history__"
        f"{_safe_filename_component(portrait.server)}__"
        f"{portrait.git_blob[:8]}.png"
    )


def scan_historical_portraits(root: Path = ROOT) -> list[HistoricalPortrait]:
    """Return every distinct labelled portrait reachable from Git history.

    ``--no-renames`` makes both sides of a rename appear as ordinary delete/add
    records. Reading both the old and new blob of every change also recovers
    overwritten portrait versions. Explicit blob-level corrections handle four
    stale filenames whose pixels belong to a different student/form.
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
            corrected_label = LABEL_CORRECTIONS_BY_BLOB.get(blob, label)
            key = (corrected_label, blob)
            found.setdefault(
                key,
                HistoricalPortrait(
                    corrected_label,
                    label,
                    blob,
                    server,
                    normalized_path,
                ),
            )
    return sorted(found.values(), key=lambda item: (item.label.casefold(), item.git_blob))


def read_git_blob(blob_hash: str, root: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", blob_hash], cwd=root)


def check(output: Path = DEFAULT_OUTPUT) -> list[dict]:
    """Verify that the committed export uses the deterministic audit names."""
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_portraits = {
        portrait.git_blob: portrait for portrait in scan_historical_portraits()
    }
    if len(manifest) != len(expected_portraits):
        raise ValueError(
            f"Manifest contains {len(manifest)} portraits; "
            f"Git history contains {len(expected_portraits)}"
        )
    seen_files: set[str] = set()
    for row in manifest:
        portrait = expected_portraits.get(row["git_blob"])
        if portrait is None:
            raise ValueError(f"Unknown Git blob in manifest: {row['git_blob']}")
        expected_filename = historical_portrait_filename(portrait)
        if row["file"] != expected_filename:
            raise ValueError(
                f"Non-auditable historical portrait filename: {row['file']} "
                f"(expected {expected_filename})"
            )
        if row["file"] in seen_files:
            raise ValueError(f"Duplicate manifest file: {row['file']}")
        seen_files.add(row["file"])
        path = output / row["file"]
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError(f"Portrait checksum mismatch: {row['file']}")
        if payload != read_git_blob(row["git_blob"]):
            raise ValueError(f"Portrait no longer matches Git blob: {row['file']}")
    disk_files = {path.name for path in output.glob("*.png")}
    if disk_files != seen_files:
        missing = sorted(seen_files - disk_files)
        extra = sorted(disk_files - seen_files)
        raise ValueError(f"Historical portrait file mismatch: missing={missing}, extra={extra}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the committed manifest and files without exporting.",
    )
    args = parser.parse_args()
    if args.check:
        manifest = check(args.output)
        print(f"Validated {len(manifest)} historical portraits in {args.output}")
        return
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for portrait in scan_historical_portraits():
        raw = read_git_blob(portrait.git_blob)
        filename = historical_portrait_filename(portrait)
        (args.output / filename).write_bytes(raw)
        row = {
                "label": portrait.label,
                "server": portrait.server,
                "source_path": portrait.source_path,
                "git_blob": portrait.git_blob,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "file": filename,
            }
        if portrait.source_label != portrait.label:
            row["source_label"] = portrait.source_label
            row["label_correction"] = "stale_filename_user_confirmed"
        manifest.append(row)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(manifest)} distinct historical portraits to {args.output}")


if __name__ == "__main__":
    main()
