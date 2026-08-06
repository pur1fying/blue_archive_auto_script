"""Evaluate the sealed lesson-independent-v1 screenshots without training.

This entry point only reads the committed fixtures, manual ground truth and
current production OpenCV models. It never imports or invokes the training
pipeline and never writes under ``src/models``.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.service import StudentRecognitionService


FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson_independent_v1"
TRAINING_FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
ANNOTATION_PATH = Path(__file__).with_name("independent_test_annotations_v1.json")
TRAINING_ANNOTATION_PATH = Path(__file__).with_name("lesson_locator_annotations.json")
TRAINING_SCRIPT_PATH = Path(__file__).with_name("train_student_models.py")
LEGACY_REPORT_PATH = Path(__file__).with_name("validation_report.json")
DEFAULT_REPORT_PATH = Path(__file__).with_name("independent_test_report_v1.json")
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"

MODEL_FILES = (
    "lesson_locator.onnx",
    "student_encoder.onnx",
    "gallery.npz",
    "lesson_locator.json",
    "student_encoder.json",
)
PROTECTED_PATHS = tuple(MODEL_DIR / name for name in MODEL_FILES) + (
    TRAINING_ANNOTATION_PATH,
    TRAINING_SCRIPT_PATH,
    LEGACY_REPORT_PATH,
)
EXPECTED_BASELINE = {
    "image_count": 5,
    "card_count": 40,
    "avatar_count": 83,
    "eligible_count": 70,
    "plain_count": 13,
    "identity_correct": 66,
    "eligible_identity_correct": 57,
    "plain_identity_correct": 9,
    "eligibility_correct": 81,
    "eligible_false_positive": 2,
    "eligible_false_negative": 0,
    "eligible_click_passed": 57,
    "gray_target_blocked": 12,
    "gray_target_clicked": 1,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hashes(paths) -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in paths
    }


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def bbox_list(box) -> Optional[list[int]]:
    if box is None:
        return None
    return [int(box.x1), int(box.y1), int(box.x2), int(box.y2)]


def percentage(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate(
    model_dir: Path = MODEL_DIR,
    enforce_expected_baseline: bool = True,
    candidate_name: str = "current_production",
) -> dict:
    model_dir = Path(model_dir).resolve()
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    student_rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    service = StudentRecognitionService(student_rows, model_dir)
    if not service.identity_available or not service.lesson_locator.model_available:
        raise RuntimeError(f"Student-recognition models are unavailable: {model_dir}")

    candidate_model_paths = tuple(model_dir / name for name in MODEL_FILES)
    missing_model_files = [path.name for path in candidate_model_paths if not path.exists()]
    if missing_model_files:
        raise FileNotFoundError(
            f"Incomplete candidate model directory {model_dir}: {missing_model_files}"
        )

    protected_before = hashes(PROTECTED_PATHS)
    candidate_before = {
        path.name: sha256(path)
        for path in candidate_model_paths
    }
    training_annotation = json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))
    training_images = sorted(training_annotation["images"])
    fixture_files = sorted(path.name for path in FIXTURE_DIR.glob("*.png"))
    annotated_files = sorted(image["file"] for image in annotation["images"])
    if fixture_files != annotated_files:
        raise ValueError("Independent fixture files and annotation image names differ")
    for image_annotation in annotation["images"]:
        image_path = FIXTURE_DIR / image_annotation["file"]
        if sha256(image_path) != image_annotation["sha256"]:
            raise ValueError(f"Independent fixture checksum mismatch: {image_path.name}")
        for instance in image_annotation["instances"]:
            if service.catalog.resolve(instance["name"]) is None:
                raise ValueError(f"Unknown catalog name: {instance['name']}")

    rows = []
    image_results = []
    detected_cards = 0
    detected_avatars = 0
    locator_backends = set()
    for image_annotation in annotation["images"]:
        image_name = image_annotation["file"]
        cards = service.recognize_lesson(read_image(FIXTURE_DIR / image_name), "CN")
        locator_backends.add(service.lesson_locator.last_backend)
        detected_cards += len(cards)
        actual = {
            f"{card.index}:{slot}": (card, avatar)
            for card in cards
            for slot, avatar in enumerate(card.avatars)
        }
        detected_avatars += len(actual)
        expected_locations = {item["location"] for item in image_annotation["instances"]}
        actual_locations = set(actual)
        image_rows = []
        for expected in image_annotation["instances"]:
            location = expected["location"]
            card_index, slot = (int(part) for part in location.split(":"))
            pair = actual.get(location)
            card, avatar = pair if pair is not None else (None, None)
            prediction = avatar.prediction if avatar is not None else None
            top1_name = prediction.name if prediction is not None else None
            identity_correct = top1_name == expected["name"]
            predicted_eligible = bool(avatar.eligible) if avatar is not None else None
            eligibility_correct = predicted_eligible == expected["eligible"]
            selected = service.select_priority_card(
                cards,
                ["available"] * 9,
                [expected["name"]],
            )
            selected_card = selected.index if selected is not None else None
            expected_click = bool(expected["eligible"])
            click_passed = (
                selected_card == card_index
                if expected_click
                else selected_card is None
            )
            potential_top1_click = bool(
                prediction is not None
                and prediction.accepted
                and avatar is not None
                and avatar.eligible
            )
            row = {
                "image": image_name,
                "location": location,
                "display_location": f"{card_index + 1}-{slot + 1}",
                "card_index": card_index,
                "slot": slot,
                "expected_bbox": expected["bbox"],
                "detected_bbox": bbox_list(avatar.bbox) if avatar is not None else None,
                "expected_name": expected["name"],
                "top1_name": top1_name,
                "score": float(prediction.score) if prediction is not None else 0.0,
                "margin": float(prediction.margin) if prediction is not None else 0.0,
                "accepted_at_0_60": bool(prediction.accepted) if prediction is not None else False,
                "expected_eligible": bool(expected["eligible"]),
                "predicted_eligible": predicted_eligible,
                "identity_correct": identity_correct,
                "eligibility_correct": eligibility_correct,
                "expected_target_selected_card": selected_card,
                "expected_target_click_passed": click_passed,
                "potential_top1_click": potential_top1_click,
                "support_status": prediction.support_status if prediction is not None else "no_prediction",
            }
            rows.append(row)
            image_rows.append(row)
        image_results.append(
            {
                "image": image_name,
                "sha256": image_annotation["sha256"],
                "expected_cards": len(image_annotation["card_bboxes"]),
                "detected_cards": len(cards),
                "expected_avatars": len(image_annotation["instances"]),
                "detected_avatars": len(actual),
                "missing_locations": sorted(expected_locations - actual_locations),
                "unexpected_locations": sorted(actual_locations - expected_locations),
                "identity_correct": sum(row["identity_correct"] for row in image_rows),
                "eligibility_correct": sum(row["eligibility_correct"] for row in image_rows),
                "locator_backend": service.lesson_locator.last_backend,
            }
        )

    identity_correct = sum(row["identity_correct"] for row in rows)
    eligible_rows = [row for row in rows if row["expected_eligible"]]
    plain_rows = [row for row in rows if not row["expected_eligible"]]
    eligibility_correct = sum(row["eligibility_correct"] for row in rows)
    eligible_false_positive = sum(
        row["predicted_eligible"] is True for row in plain_rows
    )
    eligible_false_negative = sum(
        row["predicted_eligible"] is False for row in eligible_rows
    )
    eligible_click_passed = sum(
        row["expected_target_click_passed"] for row in eligible_rows
    )
    gray_target_blocked = sum(
        row["expected_target_click_passed"] for row in plain_rows
    )
    metrics = {
        "image_count": len(annotation["images"]),
        "card_count": sum(len(image["card_bboxes"]) for image in annotation["images"]),
        "detected_card_count": detected_cards,
        "avatar_count": len(rows),
        "detected_avatar_count": detected_avatars,
        "eligible_count": len(eligible_rows),
        "plain_count": len(plain_rows),
        "predicted_eligible_count": sum(row["predicted_eligible"] is True for row in rows),
        "predicted_plain_count": sum(row["predicted_eligible"] is False for row in rows),
        "identity_correct": identity_correct,
        "identity_top1_accuracy": percentage(identity_correct, len(rows)),
        "eligible_identity_correct": sum(row["identity_correct"] for row in eligible_rows),
        "eligible_identity_accuracy": percentage(
            sum(row["identity_correct"] for row in eligible_rows), len(eligible_rows)
        ),
        "plain_identity_correct": sum(row["identity_correct"] for row in plain_rows),
        "plain_identity_accuracy": percentage(
            sum(row["identity_correct"] for row in plain_rows), len(plain_rows)
        ),
        "eligibility_correct": eligibility_correct,
        "eligibility_accuracy": percentage(eligibility_correct, len(rows)),
        "eligible_false_positive": eligible_false_positive,
        "eligible_false_negative": eligible_false_negative,
        "eligible_click_passed": eligible_click_passed,
        "eligible_click_failed": len(eligible_rows) - eligible_click_passed,
        "gray_target_blocked": gray_target_blocked,
        "gray_target_clicked": len(plain_rows) - gray_target_blocked,
    }
    baseline_checks = {}
    if enforce_expected_baseline:
        baseline_checks.update(
            {
                key: metrics[key] == expected
                for key, expected in EXPECTED_BASELINE.items()
            }
        )
    baseline_checks.update(
        {
            "detected_card_count": metrics["detected_card_count"] == EXPECTED_BASELINE["card_count"],
            "detected_avatar_count": metrics["detected_avatar_count"] == EXPECTED_BASELINE["avatar_count"],
            "all_locations_match": all(
                not item["missing_locations"] and not item["unexpected_locations"]
                for item in image_results
            ),
            "all_locator_backends_onnx": locator_backends == {"onnx"},
            "all_scores_accepted_at_0_60": all(row["accepted_at_0_60"] for row in rows),
        }
    )
    protected_after = hashes(PROTECTED_PATHS)
    candidate_after = {
        path.name: sha256(path)
        for path in candidate_model_paths
    }
    baseline_checks["protected_files_unchanged"] = protected_before == protected_after
    baseline_checks["candidate_files_unchanged_during_evaluation"] = (
        candidate_before == candidate_after
    )
    report = {
        "version": 1,
        "dataset_id": annotation["dataset_id"],
        "classification": (
            "one_time_independent_pretraining_baseline"
            if enforce_expected_baseline
            else "frozen_comparison_candidate"
        ),
        "candidate_name": candidate_name,
        "completed": all(baseline_checks.values()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "opencv_version": cv2.__version__,
            "similarity_threshold": float(service.recognizer.metadata["similarity_threshold"]),
            "server_argument": "CN",
            "candidate_ranking": "global_265",
        },
        "data_policy": {
            "included_in_training": False,
            "used_for_threshold_or_model_selection": False,
            "merged_into_training_validation_report": False,
            "identity_and_eligibility_ground_truth": "user_manual_confirmation",
            "box_source": "unchanged_production_locator_preannotation",
            "future_policy": "Retain this report as the pre-training baseline if these fixtures later enter training.",
        },
        "training_isolation": {
            "training_fixture_directory": TRAINING_FIXTURE_DIR.relative_to(ROOT).as_posix(),
            "independent_fixture_directory": FIXTURE_DIR.relative_to(ROOT).as_posix(),
            "training_annotation": TRAINING_ANNOTATION_PATH.relative_to(ROOT).as_posix(),
            "independent_annotation": ANNOTATION_PATH.relative_to(ROOT).as_posix(),
            "training_images": training_images,
            "independent_images": annotated_files,
            "directories_are_distinct": TRAINING_FIXTURE_DIR != FIXTURE_DIR,
            "image_names_are_disjoint": set(training_images).isdisjoint(annotated_files),
        },
        "artifact_hashes": {
            "fixtures": {
                image["file"]: image["sha256"] for image in annotation["images"]
            },
            "protected_files_before": protected_before,
            "protected_files_after": protected_after,
            "candidate_model_files_before": candidate_before,
            "candidate_model_files_after": candidate_after,
        },
        "expected_baseline": EXPECTED_BASELINE if enforce_expected_baseline else None,
        "production_baseline_reference": EXPECTED_BASELINE,
        "checks": baseline_checks,
        "metrics": metrics,
        "per_image": image_results,
        "instances": rows,
        "identity_failures": [row for row in rows if not row["identity_correct"]],
        "eligibility_failures": [row for row in rows if not row["eligibility_correct"]],
        "eligible_click_failures": [
            row for row in eligible_rows if not row["expected_target_click_passed"]
        ],
        "gray_target_clicks": [
            row for row in plain_rows if not row["expected_target_click_passed"]
        ],
        "gray_target_blocked_instances": [
            row for row in plain_rows if row["expected_target_click_passed"]
        ],
        "potential_wrong_target_clicks": [
            row
            for row in rows
            if not row["identity_correct"] and row["potential_top1_click"]
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--candidate-name", default="current_production")
    args = parser.parse_args()
    if args.candidate and args.output is None:
        parser.error("--candidate requires an explicit --output path")
    output = args.output or DEFAULT_REPORT_PATH
    report = evaluate(
        model_dir=args.model_dir,
        enforce_expected_baseline=not args.candidate,
        candidate_name=args.candidate_name,
    )
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report["completed"]:
        failed = [name for name, passed in report["checks"].items() if not passed]
        print(f"Independent baseline failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    metrics = report["metrics"]
    print(
        "Independent baseline recorded: "
        f"{metrics['identity_correct']}/{metrics['avatar_count']} identity, "
        f"{metrics['eligibility_correct']}/{metrics['avatar_count']} eligibility, "
        f"{metrics['eligible_click_passed']}/{metrics['eligible_count']} pink clicks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
