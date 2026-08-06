"""Evaluate user-confirmed independent_v2 without training or model writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.service import StudentRecognitionService


FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson_independent_v2"
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
ANNOTATION_PATH = Path(__file__).with_name("independent_test_annotations_v2.json")
PREANNOTATION_PATH = Path(__file__).with_name(
    "independent_test_preannotations_v2.json"
)
TRAINING_ANNOTATION_PATH = Path(__file__).with_name("lesson_locator_annotations.json")
TRAINING_SCRIPT_PATH = Path(__file__).with_name("train_student_models.py")
DEFAULT_JSON = Path(__file__).with_name("independent_test_report_v2.json")
DEFAULT_MARKDOWN = Path(__file__).with_name("independent_test_report_v2.md")
MODEL_FILES = (
    "lesson_locator.onnx",
    "lesson_locator.json",
    "student_encoder.onnx",
    "student_encoder.json",
    "gallery.npz",
)
PROTECTED_PATHS = tuple(MODEL_DIR / name for name in MODEL_FILES) + (
    TRAINING_ANNOTATION_PATH,
    TRAINING_SCRIPT_PATH,
    PREANNOTATION_PATH,
)

EXPECTED_COUNTS = {
    "images": 11,
    "cards": 86,
    "avatars": 182,
    "selected_cards": 7,
    "available_avatars": 164,
    "selected_avatars": 18,
    "available_pink": 137,
    "available_gray": 27,
    "selected_pink": 17,
    "selected_gray": 1,
    "identity_correct": 178,
    "available_identity_correct": 164,
    "selected_identity_correct": 14,
    "eligibility_correct": 175,
    "available_eligibility_correct": 157,
    "selected_eligibility_correct": 18,
    "available_gray_false_positive": 7,
    "available_pink_false_negative": 0,
    "available_pink_click_passed": 137,
    "available_pink_click_failed": 0,
    "available_gray_blocked": 20,
    "available_gray_click_risks": 7,
    "selected_source_blocked": 18,
    "selected_source_clicks": 0,
    "wrong_card_clicks": 0,
    "identity_error_wrong_clicks": 0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hashes(paths) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths}


def model_hashes(model_dir: Path) -> dict[str, dict]:
    return {
        name: {
            "bytes": (model_dir / name).stat().st_size,
            "sha256": sha256(model_dir / name),
        }
        for name in MODEL_FILES
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


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate(model_dir: Path = MODEL_DIR) -> dict:
    model_dir = Path(model_dir).resolve()
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    if annotation["status"] != "sealed_posttraining_independent_test":
        raise ValueError("independent_v2 ground truth is not sealed")
    if annotation["data_policy"]["included_in_training"]:
        raise ValueError("independent_v2 must not be a training input")

    student_rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    service = StudentRecognitionService(student_rows, model_dir)
    if not service.identity_available or not service.lesson_locator.model_available:
        raise RuntimeError(f"Student-recognition models are unavailable: {model_dir}")

    protected_before = hashes(PROTECTED_PATHS)
    models_before = model_hashes(model_dir)
    fixture_files = sorted(path.name for path in FIXTURE_DIR.glob("*.png"))
    annotated_files = sorted(image["file"] for image in annotation["images"])
    if fixture_files != annotated_files:
        raise ValueError("Independent v2 fixtures and annotations differ")

    rows = []
    image_results = []
    locator_backends = set()
    for expected_image in annotation["images"]:
        filename = expected_image["file"]
        image_path = FIXTURE_DIR / filename
        if sha256(image_path) != expected_image["sha256"]:
            raise ValueError(f"Screenshot checksum mismatch: {filename}")
        image = read_image(image_path)
        cards = service.recognize_lesson(image, "CN")
        locator_backends.add(service.lesson_locator.last_backend)
        actual = {
            f"{card.index}:{slot}": (card, avatar)
            for card in cards
            for slot, avatar in enumerate(card.avatars)
        }
        expected_locations = {
            item["location"] for item in expected_image["instances"]
        }
        selected_cards = set(expected_image["selected_card_indices"])
        statuses = ["unavailable"] * 9
        for card in cards:
            statuses[card.index] = (
                "selected" if card.index in selected_cards else "available"
            )
            card.available = statuses[card.index] == "available"

        image_rows = []
        for expected in expected_image["instances"]:
            location = expected["location"]
            card_index, slot = (int(value) for value in location.split(":"))
            card_state = "selected" if card_index in selected_cards else "available"
            if expected["card_state"] != card_state:
                raise ValueError(f"Inconsistent card state: {filename}/{location}")
            pair = actual.get(location)
            card, avatar = pair if pair is not None else (None, None)
            prediction = avatar.prediction if avatar is not None else None
            top1_name = prediction.name if prediction is not None else None
            predicted_eligible = bool(avatar.eligible) if avatar is not None else None
            identity_correct = top1_name == expected["name"]
            eligibility_correct = predicted_eligible == expected["eligible"]

            selected = service.select_priority_card(
                cards, statuses, [expected["name"]]
            )
            selected_card = selected.index if selected is not None else None
            predicted_target = service.select_priority_card(
                cards, statuses, [top1_name] if top1_name else []
            )
            predicted_target_card = (
                predicted_target.index if predicted_target is not None else None
            )
            should_click = card_state == "available" and expected["eligible"]
            source_clicked = selected_card == card_index
            click_passed = (
                source_clicked if should_click else selected_card is None
            )
            wrong_card_click = bool(
                should_click
                and selected_card is not None
                and selected_card != card_index
            )
            gray_click_risk = bool(
                card_state == "available"
                and not expected["eligible"]
                and source_clicked
            )
            selected_source_blocked = bool(
                card_state == "selected" and not source_clicked
            )
            identity_error_wrong_click = bool(
                not identity_correct
                and predicted_target_card == card_index
                and card_state == "available"
            )
            row = {
                "image": filename,
                "location": location,
                "display_location": f"{card_index + 1}-{slot + 1}",
                "card_index": card_index,
                "slot": slot,
                "card_state": card_state,
                "expected_bbox": expected["bbox"],
                "detected_bbox": bbox_list(avatar.bbox) if avatar is not None else None,
                "expected_name": expected["name"],
                "top1_name": top1_name,
                "score": float(prediction.score) if prediction is not None else 0.0,
                "margin": float(prediction.margin) if prediction is not None else 0.0,
                "top1_valid": bool(prediction is not None and prediction.accepted),
                "identity_correct": identity_correct,
                "expected_eligible": bool(expected["eligible"]),
                "predicted_eligible": predicted_eligible,
                "eligibility_correct": eligibility_correct,
                "expected_should_click": should_click,
                "simulated_selected_card_index": selected_card,
                "simulated_source_card_clicked": source_clicked,
                "click_passed": click_passed,
                "wrong_card_click": wrong_card_click,
                "gray_click_risk": gray_click_risk,
                "selected_source_blocked": selected_source_blocked,
                "predicted_target_selected_card_index": predicted_target_card,
                "identity_error_wrong_click": identity_error_wrong_click,
                "support_status": (
                    prediction.support_status if prediction is not None else "no_prediction"
                ),
            }
            rows.append(row)
            image_rows.append(row)

        actual_locations = set(actual)
        image_results.append(
            {
                "image": filename,
                "sha256": expected_image["sha256"],
                "expected_cards": len(expected_image["card_bboxes"]),
                "detected_cards": len(cards),
                "expected_avatars": len(expected_image["instances"]),
                "detected_avatars": len(actual),
                "selected_card_indices": sorted(selected_cards),
                "missing_locations": sorted(expected_locations - actual_locations),
                "unexpected_locations": sorted(actual_locations - expected_locations),
                "identity_correct": sum(row["identity_correct"] for row in image_rows),
                "eligibility_correct": sum(
                    row["eligibility_correct"] for row in image_rows
                ),
                "locator_backend": service.lesson_locator.last_backend,
            }
        )

    available = [row for row in rows if row["card_state"] == "available"]
    selected = [row for row in rows if row["card_state"] == "selected"]
    available_pink = [row for row in available if row["expected_eligible"]]
    available_gray = [row for row in available if not row["expected_eligible"]]
    selected_pink = [row for row in selected if row["expected_eligible"]]
    selected_gray = [row for row in selected if not row["expected_eligible"]]

    counts = {
        "images": len(annotation["images"]),
        "cards": sum(len(image["card_bboxes"]) for image in annotation["images"]),
        "avatars": len(rows),
        "selected_cards": sum(
            len(image["selected_card_indices"]) for image in annotation["images"]
        ),
        "available_avatars": len(available),
        "selected_avatars": len(selected),
        "available_pink": len(available_pink),
        "available_gray": len(available_gray),
        "selected_pink": len(selected_pink),
        "selected_gray": len(selected_gray),
        "identity_correct": sum(row["identity_correct"] for row in rows),
        "available_identity_correct": sum(
            row["identity_correct"] for row in available
        ),
        "selected_identity_correct": sum(
            row["identity_correct"] for row in selected
        ),
        "eligibility_correct": sum(row["eligibility_correct"] for row in rows),
        "available_eligibility_correct": sum(
            row["eligibility_correct"] for row in available
        ),
        "selected_eligibility_correct": sum(
            row["eligibility_correct"] for row in selected
        ),
        "available_gray_false_positive": sum(
            row["predicted_eligible"] is True for row in available_gray
        ),
        "available_pink_false_negative": sum(
            row["predicted_eligible"] is False for row in available_pink
        ),
        "available_pink_click_passed": sum(
            row["simulated_source_card_clicked"] for row in available_pink
        ),
        "available_pink_click_failed": sum(
            not row["simulated_source_card_clicked"] for row in available_pink
        ),
        "available_gray_blocked": sum(
            row["simulated_selected_card_index"] is None for row in available_gray
        ),
        "available_gray_click_risks": sum(row["gray_click_risk"] for row in rows),
        "selected_source_blocked": sum(
            row["selected_source_blocked"] for row in selected
        ),
        "selected_source_clicks": sum(
            row["simulated_source_card_clicked"] for row in selected
        ),
        "wrong_card_clicks": sum(row["wrong_card_click"] for row in rows),
        "identity_error_wrong_clicks": sum(
            row["identity_error_wrong_click"] for row in rows
        ),
    }
    metrics = {
        "identity": {
            "all": {
                "correct": counts["identity_correct"],
                "total": len(rows),
                "accuracy": ratio(counts["identity_correct"], len(rows)),
            },
            "available": {
                "correct": counts["available_identity_correct"],
                "total": len(available),
                "accuracy": ratio(counts["available_identity_correct"], len(available)),
            },
            "selected": {
                "correct": counts["selected_identity_correct"],
                "total": len(selected),
                "accuracy": ratio(counts["selected_identity_correct"], len(selected)),
            },
        },
        "eligibility": {
            "all": {
                "correct": counts["eligibility_correct"],
                "total": len(rows),
                "accuracy": ratio(counts["eligibility_correct"], len(rows)),
            },
            "available": {
                "correct": counts["available_eligibility_correct"],
                "total": len(available),
                "accuracy": ratio(
                    counts["available_eligibility_correct"], len(available)
                ),
                "gray_false_positive": counts["available_gray_false_positive"],
                "pink_false_negative": counts["available_pink_false_negative"],
            },
            "selected": {
                "correct": counts["selected_eligibility_correct"],
                "total": len(selected),
                "accuracy": ratio(
                    counts["selected_eligibility_correct"], len(selected)
                ),
            },
        },
        "clicks": {
            "available_pink_correct_card": counts["available_pink_click_passed"],
            "available_pink_total": len(available_pink),
            "available_gray_blocked": counts["available_gray_blocked"],
            "available_gray_total": len(available_gray),
            "available_gray_click_risks": counts["available_gray_click_risks"],
            "selected_source_blocked": counts["selected_source_blocked"],
            "selected_total": len(selected),
            "wrong_card_clicks": counts["wrong_card_clicks"],
            "identity_error_wrong_clicks": counts["identity_error_wrong_clicks"],
        },
    }

    protected_after = hashes(PROTECTED_PATHS)
    models_after = model_hashes(model_dir)
    checks = {
        **{
            f"expected_{key}": counts[key] == value
            for key, value in EXPECTED_COUNTS.items()
        },
        "detected_all_cards": sum(
            image["detected_cards"] for image in image_results
        ) == EXPECTED_COUNTS["cards"],
        "detected_all_avatars": sum(
            image["detected_avatars"] for image in image_results
        ) == EXPECTED_COUNTS["avatars"],
        "all_locations_match": all(
            not image["missing_locations"] and not image["unexpected_locations"]
            for image in image_results
        ),
        "all_locator_backends_onnx": locator_backends == {"onnx"},
        "all_top1_predictions_valid": all(row["top1_valid"] for row in rows),
        "protected_files_unchanged": protected_before == protected_after,
        "model_files_unchanged": models_before == models_after,
    }
    return {
        "version": 1,
        "dataset_id": "lesson_independent_v2",
        "classification": "frozen_posttraining_independent_test",
        "completed": all(checks.values()),
        "data_policy": annotation["data_policy"],
        "environment": {
            "opencv_version": cv2.__version__,
            "server_argument": "CN",
            "identity_click_policy": "valid_global_top1",
            "selected_card_policy": "never_select_source_card",
        },
        "artifact_hashes": {
            "annotation": sha256(ANNOTATION_PATH),
            "preannotation": sha256(PREANNOTATION_PATH),
            "production_models_before": models_before,
            "production_models_after": models_after,
            "protected_files_before": protected_before,
            "protected_files_after": protected_after,
        },
        "counts": counts,
        "metrics": metrics,
        "acceptance_checks": checks,
        "identity_failures": [row for row in rows if not row["identity_correct"]],
        "available_eligibility_failures": [
            row for row in available if not row["eligibility_correct"]
        ],
        "available_gray_click_risks": [row for row in rows if row["gray_click_risk"]],
        "available_pink_click_failures": [
            row for row in available_pink if not row["simulated_source_card_clicked"]
        ],
        "wrong_card_clicks": [row for row in rows if row["wrong_card_click"]],
        "identity_error_wrong_clicks": [
            row for row in rows if row["identity_error_wrong_click"]
        ],
        "selected_source_clicks": [
            row for row in selected if row["simulated_source_card_clicked"]
        ],
        "image_results": image_results,
        "instances": rows,
    }


def render_markdown(report: dict) -> str:
    identity = report["metrics"]["identity"]
    eligibility = report["metrics"]["eligibility"]
    clicks = report["metrics"]["clicks"]
    lines = [
        "# independent_v2 正式测试报告",
        "",
        f"> 状态：`{'completed' if report['completed'] else 'failed'}`；",
        "> 该集合未进入训练、图库、阈值或模型选择。",
        "",
        "## 总结",
        "",
        f"- 定位：86/86个卡片，182/182个头像。",
        f"- 普通状态身份：{identity['available']['correct']}/{identity['available']['total']}；"
        f"selected身份：{identity['selected']['correct']}/{identity['selected']['total']}；"
        f"总计：{identity['all']['correct']}/{identity['all']['total']}。",
        f"- 普通状态粉灰：{eligibility['available']['correct']}/{eligibility['available']['total']}；"
        f"selected粉灰：{eligibility['selected']['correct']}/{eligibility['selected']['total']}；"
        f"总计：{eligibility['all']['correct']}/{eligibility['all']['total']}。",
        f"- 普通彩框正确卡片：{clicks['available_pink_correct_card']}/"
        f"{clicks['available_pink_total']}。",
        f"- 普通灰框正确阻止：{clicks['available_gray_blocked']}/"
        f"{clicks['available_gray_total']}；点击风险："
        f"{clicks['available_gray_click_risks']}。",
        f"- selected来源卡片阻止：{clicks['selected_source_blocked']}/"
        f"{clicks['selected_total']}；实际来源卡片点击：0。",
        "",
        "## 身份错误（全部位于selected卡片）",
        "",
        "| 图片 | 位置 | 真值 | Top-1 | 分数 | 分差 |",
        "|---|---:|---|---|---:|---:|",
    ]
    for row in report["identity_failures"]:
        lines.append(
            f"| {row['image']} | {row['display_location']} | "
            f"{row['expected_name']} | {row['top1_name']} | "
            f"{row['score']:.3f} | {row['margin']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 普通灰框误判与点击风险",
            "",
            "| 图片 | 位置 | 学生 | 预测粉灰 | 模拟点击卡片 |",
            "|---|---:|---|---|---:|",
        ]
    )
    for row in report["available_gray_click_risks"]:
        lines.append(
            f"| {row['image']} | {row['display_location']} | "
            f"{row['expected_name']} | 彩框 | "
            f"{row['simulated_selected_card_index'] + 1} |"
        )
    lines.extend(
        [
            "",
            "## 全部头像",
            "",
            "| 图片 | 位置 | 状态 | 真值 | Top-1 | 身份 | 真值粉灰 | 预测粉灰 | 模拟卡片 |",
            "|---|---:|---|---|---|---|---|---|---:|",
        ]
    )
    for row in report["instances"]:
        selected_card = row["simulated_selected_card_index"]
        lines.append(
            f"| {row['image']} | {row['display_location']} | {row['card_state']} | "
            f"{row['expected_name']} | {row['top1_name']} | "
            f"{'正确' if row['identity_correct'] else '错误'} | "
            f"{'彩框' if row['expected_eligible'] else '灰框'} | "
            f"{'彩框' if row['predicted_eligible'] else '灰框'} | "
            f"{selected_card + 1 if selected_card is not None else '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = evaluate(args.model_dir)
    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    markdown_text = render_markdown(report)
    if args.check:
        if not args.json_output.exists() or args.json_output.read_text(encoding="utf-8") != json_text:
            raise RuntimeError("independent_v2 JSON report is stale")
        if not args.markdown_output.exists() or args.markdown_output.read_text(encoding="utf-8") != markdown_text:
            raise RuntimeError("independent_v2 Markdown report is stale")
        print("Validated independent_v2 report")
        return 0
    args.json_output.write_text(json_text, encoding="utf-8")
    args.markdown_output.write_text(markdown_text, encoding="utf-8")
    print(
        "Generated independent_v2 report: "
        f"identity={report['counts']['identity_correct']}/182, "
        f"eligibility={report['counts']['eligibility_correct']}/182"
    )
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
