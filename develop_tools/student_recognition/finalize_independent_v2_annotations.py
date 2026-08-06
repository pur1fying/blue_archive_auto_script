"""Materialize user-confirmed ground truth for independent_v2.

The model preannotation remains unchanged.  This tool applies only the explicit
manual corrections below and treats every unlisted prediction as confirmed by
the user's "all remaining entries are correct" statement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREANNOTATION_PATH = Path(__file__).with_name(
    "independent_test_preannotations_v2.json"
)
DEFAULT_OUTPUT = Path(__file__).with_name("independent_test_annotations_v2.json")

IDENTITY_CORRECTIONS = {
    ("MuMu-20260806-231258-968.png", "6:0"): "Sumire (Part-Timer)",
    ("MuMu-20260806-231304-820.png", "5:1"): "Kasumi",
    ("MuMu-20260806-231311-941.png", "3:1"): "Ui (Swimsuit)",
    ("MuMu-20260806-231317-557.png", "7:0"): "Ui (Swimsuit)",
}

GRAY_CORRECTIONS = {
    ("MuMu-20260806-231304-820.png", "6:0"),
    # The user confirmed that their original 7-3 entry was a position typo.
    ("MuMu-20260806-231311-941.png", "6:1"),
    ("MuMu-20260806-231317-557.png", "0:1"),
    ("MuMu-20260806-231317-557.png", "3:1"),
    ("MuMu-20260806-231317-557.png", "5:1"),
    ("MuMu-20260806-231322-679.png", "3:1"),
    ("MuMu-20260806-231322-679.png", "6:2"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_location(location: str) -> str:
    card, slot = (int(value) for value in location.split(":"))
    return f"{card + 1}-{slot + 1}"


def generate() -> dict:
    preannotation = json.loads(PREANNOTATION_PATH.read_text(encoding="utf-8"))
    if preannotation["status"] != "pending_user_review":
        raise ValueError("independent_v2 preannotation is not pending review")
    if preannotation["counts"]["avatars"] != 182:
        raise ValueError("independent_v2 preannotation count changed")

    known_locations = {
        (image["file"], row["location"])
        for image in preannotation["images"]
        for row in image["instances"]
    }
    requested_locations = set(IDENTITY_CORRECTIONS) | GRAY_CORRECTIONS
    if not requested_locations <= known_locations:
        raise ValueError(
            f"Manual correction locations are missing: "
            f"{sorted(requested_locations - known_locations)}"
        )
    if ("MuMu-20260806-231311-941.png", "6:2") in known_locations:
        raise ValueError("Unexpected 7-3 avatar exists in MuMu-20260806-231311-941.png")

    images = []
    for source_image in preannotation["images"]:
        filename = source_image["file"]
        instances = []
        for source_row in source_image["instances"]:
            key = (filename, source_row["location"])
            instances.append(
                {
                    "location": source_row["location"],
                    "bbox": source_row["bbox"],
                    "name": IDENTITY_CORRECTIONS.get(
                        key, source_row["predicted_name"]
                    ),
                    "eligible": (
                        False
                        if key in GRAY_CORRECTIONS
                        else source_row["predicted_eligible"]
                    ),
                    "card_state": source_row["card_state"],
                }
            )
        images.append(
            {
                "file": filename,
                "sha256": source_image["sha256"],
                "selected_card_indices": source_image["selected_card_indices"],
                "card_bboxes": source_image["card_bboxes"],
                "instances": instances,
            }
        )

    return {
        "version": 1,
        "dataset_id": "lesson_independent_v2",
        "status": "sealed_posttraining_independent_test",
        "canonical_size": [1280, 720],
        "coordinate_format": "xyxy_exclusive",
        "indexing": {
            "card": "zero_based_row_major",
            "slot": "zero_based_left_to_right",
            "display": "one_based_card-avatar",
        },
        "annotation_sources": {
            "identity_and_eligibility": "user_manual_confirmation",
            "card_state": "user_confirmed_selected_card_map",
            "card_and_avatar_boxes": "unchanged_production_locator_preannotation",
            "unlisted_entries": "user_confirmed_all_remaining_entries_correct",
        },
        "source_preannotation": {
            "file": PREANNOTATION_PATH.name,
            "sha256": sha256(PREANNOTATION_PATH),
            "status": preannotation["status"],
        },
        "manual_corrections": {
            "identity": [
                {
                    "file": filename,
                    "location": location,
                    "display_location": display_location(location),
                    "name": name,
                }
                for (filename, location), name in IDENTITY_CORRECTIONS.items()
            ],
            "eligibility_to_gray": [
                {
                    "file": filename,
                    "location": location,
                    "display_location": display_location(location),
                }
                for filename, location in sorted(GRAY_CORRECTIONS)
            ],
            "confirmed_position_correction": {
                "file": "MuMu-20260806-231311-941.png",
                "submitted_display_location": "7-3",
                "confirmed_display_location": "7-2",
                "name": "Sena (Casual)",
            },
        },
        "data_policy": {
            "included_in_training": False,
            "included_in_gallery": False,
            "used_for_model_or_threshold_selection": False,
            "formal_metrics_allowed": True,
        },
        "images": images,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(generate(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != text:
            raise RuntimeError("independent_v2 ground truth is stale")
        print("Validated independent_v2 ground truth")
        return 0
    args.output.write_text(text, encoding="utf-8")
    print(f"Generated {args.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
