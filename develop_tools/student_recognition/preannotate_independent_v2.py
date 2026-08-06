"""Generate review-only predictions for the sealed independent_v2 screenshots.

This tool never writes ground truth, accuracy metrics, models, galleries or
training inputs.  Selected cards remain useful identity fixtures, but their
status is passed as ``selected`` so they cannot be chosen by click simulation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.service import StudentRecognitionService


FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson_independent_v2"
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
DEFAULT_JSON = Path(__file__).with_name("independent_test_preannotations_v2.json")
DEFAULT_MARKDOWN = Path(__file__).with_name("independent_test_preannotations_v2.md")
MODEL_FILES = (
    "lesson_locator.onnx",
    "lesson_locator.json",
    "student_encoder.onnx",
    "student_encoder.json",
    "gallery.npz",
)

# Card indices are zero based here and one based in the review document.
SCREENSHOTS = (
    ("MuMu-20260806-231258-968.png", 7, 17, {6}),
    ("MuMu-20260806-231304-820.png", 7, 15, {5}),
    ("MuMu-20260806-231311-941.png", 8, 18, {3}),
    ("MuMu-20260806-231317-557.png", 8, 16, {7}),
    ("MuMu-20260806-231322-679.png", 8, 17, {0}),
    ("MuMu-20260806-231327-489.png", 8, 17, set()),
    ("MuMu-20260806-231332-087.png", 8, 17, {4}),
    ("MuMu-20260806-231336-603.png", 8, 17, set()),
    ("MuMu-20260806-231341-107.png", 8, 16, set()),
    ("MuMu-20260806-231345-085.png", 8, 16, set()),
    ("MuMu-20260806-231349-471.png", 8, 16, {4}),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bbox_values(box) -> list[int]:
    return [box.x1, box.y1, box.x2, box.y2]


def model_hashes() -> dict[str, dict]:
    return {
        name: {
            "bytes": (MODEL_DIR / name).stat().st_size,
            "sha256": sha256(MODEL_DIR / name),
        }
        for name in MODEL_FILES
    }


def generate() -> dict:
    before = model_hashes()
    catalog_rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    service = StudentRecognitionService(catalog_rows, MODEL_DIR)
    if not service.identity_available or not service.lesson_locator.model_available:
        raise RuntimeError("Production student-recognition models are unavailable")

    expected_names = {row[0] for row in SCREENSHOTS}
    actual_names = {path.name for path in FIXTURE_DIR.glob("*.png")}
    if actual_names != expected_names:
        raise ValueError(
            "independent_v2 fixture files differ: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )

    images = []
    for filename, expected_cards, expected_avatars, selected_cards in SCREENSHOTS:
        path = FIXTURE_DIR / filename
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None or image.shape[:2] != (720, 1280):
            raise ValueError(f"Invalid 1280x720 screenshot: {path}")
        cards = service.recognize_lesson(image, "CN")
        avatar_count = sum(len(card.avatars) for card in cards)
        if len(cards) != expected_cards or avatar_count != expected_avatars:
            raise ValueError(
                f"Unexpected detection count for {filename}: "
                f"{len(cards)}/{avatar_count} != {expected_cards}/{expected_avatars}"
            )
        located_indices = {card.index for card in cards}
        if not selected_cards <= located_indices:
            raise ValueError(f"Selected card was not located in {filename}")

        statuses = ["unavailable"] * 9
        for card in cards:
            statuses[card.index] = (
                "selected" if card.index in selected_cards else "available"
            )
            card.available = statuses[card.index] == "available"

        instances = []
        for card in cards:
            card_state = statuses[card.index]
            for slot, avatar in enumerate(card.avatars):
                prediction = avatar.prediction
                if prediction is None or prediction.name is None:
                    raise ValueError(
                        f"Missing identity prediction: {filename}/{card.index}:{slot}"
                    )
                selected = service.select_priority_card(
                    cards,
                    statuses,
                    [prediction.name],
                )
                selected_index = selected.index if selected is not None else None
                instances.append(
                    {
                        "location": f"{card.index}:{slot}",
                        "display_location": f"{card.index + 1}-{slot + 1}",
                        "card_index": card.index,
                        "slot": slot,
                        "bbox": bbox_values(avatar.bbox),
                        "predicted_name": prediction.name,
                        "predicted_student_id": prediction.student_id,
                        "score": float(prediction.score),
                        "margin": float(prediction.margin),
                        "prediction_valid": bool(prediction.accepted),
                        "predicted_eligible": bool(avatar.eligible),
                        "card_state": card_state,
                        "simulated_selected_card_index": selected_index,
                        "simulated_selected_display_card": (
                            selected_index + 1 if selected_index is not None else None
                        ),
                        "simulated_source_card_clicked": selected_index == card.index,
                        "review_status": "pending_user_review",
                    }
                )

        images.append(
            {
                "file": filename,
                "sha256": sha256(path),
                "width": image.shape[1],
                "height": image.shape[0],
                "locator_backend": service.lesson_locator.last_backend,
                "selected_card_indices": sorted(selected_cards),
                "selected_display_cards": [index + 1 for index in sorted(selected_cards)],
                "card_bboxes": [
                    {
                        "card_index": card.index,
                        "display_card": card.index + 1,
                        "bbox": bbox_values(card.bbox),
                        "click_point": list(card.click_point),
                        "card_state": statuses[card.index],
                    }
                    for card in cards
                ],
                "instances": instances,
            }
        )

    after = model_hashes()
    if before != after:
        raise RuntimeError("Production model hashes changed during preannotation")

    all_instances = [row for image in images for row in image["instances"]]
    selected_instances = [
        row for row in all_instances if row["card_state"] == "selected"
    ]
    available_instances = [
        row for row in all_instances if row["card_state"] == "available"
    ]
    selected_source_clicks = [
        row
        for row in selected_instances
        if row["simulated_source_card_clicked"]
    ]
    if selected_source_clicks:
        raise RuntimeError("Selected card was clickable during simulation")

    return {
        "version": 1,
        "dataset_id": "lesson_independent_v2",
        "status": "pending_user_review",
        "classification": "model_preannotation_not_ground_truth_or_accuracy",
        "canonical_size": [1280, 720],
        "coordinate_format": "xyxy_exclusive",
        "indexing": {
            "card": "zero_based_row_major",
            "slot": "zero_based_left_to_right",
            "display": "one_based_card-avatar",
        },
        "data_policy": {
            "included_in_training": False,
            "included_in_gallery": False,
            "used_for_model_or_threshold_selection": False,
            "formal_metrics_allowed_before_user_review": False,
            "selected_cards_identity_test": True,
            "selected_cards_available_click_test": False,
            "selected_cards_must_not_click": True,
        },
        "counts": {
            "images": len(images),
            "nonempty_cards": sum(len(image["card_bboxes"]) for image in images),
            "avatars": len(all_instances),
            "selected_cards": sum(
                len(image["selected_card_indices"]) for image in images
            ),
            "selected_state_avatars": len(selected_instances),
            "available_state_cards": sum(
                card["card_state"] == "available"
                for image in images
                for card in image["card_bboxes"]
            ),
            "available_state_avatars": len(available_instances),
            "predicted_pink_available": sum(
                row["predicted_eligible"] for row in available_instances
            ),
            "predicted_gray_available": sum(
                not row["predicted_eligible"] for row in available_instances
            ),
            "predicted_pink_selected": sum(
                row["predicted_eligible"] for row in selected_instances
            ),
            "predicted_gray_selected": sum(
                not row["predicted_eligible"] for row in selected_instances
            ),
        },
        "environment": {
            "opencv_version": cv2.__version__,
            "server_argument": "CN",
            "identity_click_policy": "valid_global_top1",
        },
        "production_model_hashes_before": before,
        "production_model_hashes_after": after,
        "images": images,
    }


def render_markdown(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# independent_v2 模型预标注审核表",
        "",
        "> 状态：`pending_user_review`。以下姓名、粉灰和已选择状态均为预标注，",
        "> 不是人工真值，也没有据此计算准确率。",
        "",
        "## 完整性",
        "",
        f"- 11张截图，{counts['nonempty_cards']}个非空卡片，{counts['avatars']}个头像。",
        f"- 7个已选择卡片、{counts['selected_state_avatars']}个已选择状态头像。",
        f"- {counts['available_state_cards']}个普通卡片、{counts['available_state_avatars']}个普通状态头像。",
        "- `[低分差]`表示Top-1/Top-2分差低于0.10，请优先审核。",
        "",
        "## 优先审核",
        "",
    ]
    priority_rows = sorted(
        (
            (image["file"], row)
            for image in report["images"]
            for row in image["instances"]
            if row["card_state"] == "selected" or row["margin"] < 0.10
        ),
        key=lambda item: (item[1]["margin"], item[0], item[1]["location"]),
    )
    for filename, row in priority_rows:
        flags = []
        if not row["predicted_eligible"]:
            flags.append("灰框")
        if row["card_state"] == "selected":
            flags.append("已选择")
        if row["margin"] < 0.10:
            flags.append("低分差")
        suffix = " " + " ".join(f"[{flag}]" for flag in flags) if flags else ""
        lines.append(
            f"- `{filename}` {row['display_location']} = "
            f"`{row['predicted_name']}`{suffix} "
            f"(score={row['score']:.3f}, margin={row['margin']:.3f})"
        )

    for image in report["images"]:
        lines.extend(["", f"## {image['file']}", ""])
        selected = image["selected_display_cards"]
        lines.append(
            "已选择卡片：" + (", ".join(str(value) for value in selected) if selected else "无")
        )
        lines.append("")
        for row in image["instances"]:
            flags = []
            if not row["predicted_eligible"]:
                flags.append("灰框")
            if row["card_state"] == "selected":
                flags.append("已选择")
            if row["margin"] < 0.10:
                flags.append("低分差")
            suffix = " " + " ".join(f"[{flag}]" for flag in flags) if flags else ""
            lines.append(
                f"- {row['display_location']} = `{row['predicted_name']}`{suffix} "
                f"(score={row['score']:.3f}, margin={row['margin']:.3f})"
            )

    lines.extend(
        [
            "",
            "## 回复格式",
            "",
            "只需列出错误项，并在最后写明“其余均正确”。例如：",
            "",
            "```text",
            "MuMu-20260806-231258-968.png",
            "1-1 = Correct Name [灰框]",
            "7-2 = Correct Name [已选择]",
            "其余均正确",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = generate()
    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    markdown_text = render_markdown(report)
    if args.check:
        if not args.json_output.exists() or args.json_output.read_text(encoding="utf-8") != json_text:
            raise RuntimeError("independent_v2 JSON preannotation is stale")
        if not args.markdown_output.exists() or args.markdown_output.read_text(encoding="utf-8") != markdown_text:
            raise RuntimeError("independent_v2 Markdown preannotation is stale")
        print("Validated independent_v2 preannotations")
        return 0
    args.json_output.write_text(json_text, encoding="utf-8")
    args.markdown_output.write_text(markdown_text, encoding="utf-8")
    print(
        "Generated independent_v2 preannotations: "
        f"{report['counts']['images']} images, "
        f"{report['counts']['nonempty_cards']} cards, "
        f"{report['counts']['avatars']} avatars"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
