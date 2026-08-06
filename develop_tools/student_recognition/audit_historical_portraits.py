"""Create a deterministic duplicate/near-duplicate audit for historical portraits."""

from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from develop_tools.student_recognition.training_data import HISTORICAL_MANIFEST


DEFAULT_OUTPUT = HISTORICAL_MANIFEST.with_name("similarity_audit.json")
PHASH_DISTANCE_THRESHOLD = 6


def _decoded_sha256(image: np.ndarray) -> str:
    payload = str(image.shape).encode("ascii") + image.tobytes()
    return hashlib.sha256(payload).hexdigest()


def _phash_bits(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    coefficients = cv2.dct(resized)[:8, :8].reshape(-1)[1:]
    return coefficients > np.median(coefficients)


def build_audit(manifest_path: Path = HISTORICAL_MANIFEST) -> dict:
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    directory = manifest_path.parent
    items = []
    for row in rows:
        image = cv2.imread(str(directory / row["file"]), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Cannot decode historical portrait: {row['file']}")
        items.append((row, _decoded_sha256(image), _phash_bits(image)))

    exact_groups = collections.defaultdict(list)
    for row, digest, _ in items:
        exact_groups[digest].append(row["file"])
    exact_duplicates = [
        {"decoded_sha256": digest, "files": sorted(files)}
        for digest, files in sorted(exact_groups.items())
        if len(files) > 1
    ]

    near_same_identity = []
    near_cross_identity = []
    for first, second in itertools.combinations(items, 2):
        distance = int(np.count_nonzero(first[2] != second[2]))
        if distance > PHASH_DISTANCE_THRESHOLD:
            continue
        pair = {
            "distance": distance,
            "first_label": first[0]["label"],
            "first_file": first[0]["file"],
            "second_label": second[0]["label"],
            "second_file": second[0]["file"],
        }
        destination = (
            near_same_identity
            if first[0]["label"] == second[0]["label"]
            else near_cross_identity
        )
        destination.append(pair)

    sort_key = lambda row: (
        row["distance"],
        row["first_label"].casefold(),
        row["first_file"],
        row["second_file"],
    )
    near_same_identity.sort(key=sort_key)
    near_cross_identity.sort(key=sort_key)
    return {
        "version": 1,
        "classification": "audit_only_no_training_filter",
        "method": {
            "decoded_exact_hash": "sha256(shape + decoded_bgr_bytes)",
            "perceptual_hash": "32x32 grayscale DCT, top-left 8x8, DC excluded, median bits",
            "maximum_hamming_distance": PHASH_DISTANCE_THRESHOLD,
        },
        "portrait_count": len(rows),
        "identity_count": len({row["label"] for row in rows}),
        "exact_duplicate_groups": exact_duplicates,
        "exact_redundant_file_count": sum(
            len(group["files"]) - 1 for group in exact_duplicates
        ),
        "near_same_identity_pairs": near_same_identity,
        "near_cross_identity_pairs": near_cross_identity,
        "training_policy": "retain_all_identity_balanced",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=HISTORICAL_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    actual = build_audit(args.manifest)
    if args.check:
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        if committed != actual:
            raise ValueError(f"Historical similarity audit is stale: {args.output}")
        print(f"Validated historical similarity audit: {args.output}")
        return 0
    args.output.write_text(
        json.dumps(actual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote historical similarity audit: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
