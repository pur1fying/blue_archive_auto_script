"""Materialize the deduplicated lesson portrait seed set from Git history."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    ("CN", "870ddc335^"),
    ("JP", "d36428149^"),
    ("Global_en-us", "683039fce^"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    seen = set()
    for server, revision in SOURCES:
        root = f"src/images/{server}/lesson_affection"
        output = subprocess.check_output(
            ["git", "ls-tree", "-r", revision, "--", root],
            cwd=ROOT,
        )
        for line in output.splitlines():
            metadata, path = line.split(b"\t", 1)
            blob_hash = metadata.split()[2].decode()
            if blob_hash in seen:
                continue
            seen.add(blob_hash)
            source_path = path.decode()
            name = os.path.splitext(os.path.basename(source_path))[0]
            raw = subprocess.check_output(
                ["git", "cat-file", "blob", blob_hash],
                cwd=ROOT,
            )
            filename = f"{blob_hash[:12]}.png"
            (args.output / filename).write_bytes(raw)
            manifest.append(
                {
                    "label": name,
                    "server": server,
                    "revision": revision,
                    "source_path": source_path,
                    "git_blob": blob_hash,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "file": filename,
                }
            )
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(manifest)} unique historical portraits to {args.output}")


if __name__ == "__main__":
    main()
