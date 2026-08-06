"""Evaluate the composed YOLOX + MobileNetV3 global Top-1 candidate.

The sealed ``lesson_independent_v1`` fixtures are evaluation-only. This module
imports the generic evaluator but never imports a training entry point.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.service import StudentRecognitionService
from develop_tools.student_recognition.evaluate_independent_test import (
    ANNOTATION_PATH as INDEPENDENT_ANNOTATION_PATH,
    FIXTURE_DIR as INDEPENDENT_FIXTURE_DIR,
    benchmark_candidate,
    evaluate as evaluate_independent,
    read_image,
)


TRAINING_FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
TRAINING_ANNOTATION_PATH = Path(__file__).with_name("lesson_locator_annotations.json")
DEFAULT_MODEL_DIR = Path(__file__).with_name("experiments") / "yolox_mobilenetv3_top1"
DEFAULT_JSON = Path(__file__).with_name("combined_top1_report.json")
DEFAULT_MARKDOWN = Path(__file__).with_name("combined_top1_report.md")
MODEL_FILES = (
    "lesson_locator.onnx",
    "lesson_locator.json",
    "student_encoder.onnx",
    "student_encoder.json",
    "gallery.npz",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_training_replay(model_dir: Path) -> dict:
    annotation = json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))
    catalog_rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    service = StudentRecognitionService(catalog_rows, model_dir)
    rows = []
    detected_cards = 0
    detected_avatars = 0
    for image_name, expected in annotation["images"].items():
        cards = service.recognize_lesson(
            read_image(TRAINING_FIXTURE_DIR / image_name),
            "CN",
        )
        detected_cards += len(cards)
        actual = {
            f"{card.index}:{slot}": (card, avatar)
            for card in cards
            for slot, avatar in enumerate(card.avatars)
        }
        detected_avatars += len(actual)
        eligibility = {
            f"{card}:{slot}": bool(eligible)
            for card, slot, eligible in expected["avatars"]
        }
        for location, expected_name in expected["identity_labels"].items():
            card_index, slot = (int(part) for part in location.split(":"))
            pair = actual.get(location)
            card, avatar = pair if pair is not None else (None, None)
            prediction = avatar.prediction if avatar is not None else None
            selected = service.select_priority_card(
                cards,
                ["available"] * 9,
                [expected_name],
            )
            selected_card = selected.index if selected is not None else None
            expected_eligible = eligibility[location]
            rows.append(
                {
                    "image": image_name,
                    "location": location,
                    "display_location": f"{card_index + 1}-{slot + 1}",
                    "card_index": card_index,
                    "slot": slot,
                    "expected_name": expected_name,
                    "top1_name": prediction.name if prediction is not None else None,
                    "score": float(prediction.score) if prediction is not None else 0.0,
                    "margin": float(prediction.margin) if prediction is not None else 0.0,
                    "top1_valid": bool(prediction and prediction.accepted),
                    "expected_eligible": expected_eligible,
                    "predicted_eligible": (
                        bool(avatar.eligible) if avatar is not None else None
                    ),
                    "identity_correct": bool(
                        prediction is not None and prediction.name == expected_name
                    ),
                    "eligibility_correct": bool(
                        avatar is not None and avatar.eligible == expected_eligible
                    ),
                    "selected_card": selected_card,
                    "click_passed": (
                        selected_card == card_index
                        if expected_eligible
                        else selected_card is None
                    ),
                    "support_status": (
                        prediction.support_status
                        if prediction is not None
                        else "no_prediction"
                    ),
                }
            )

    pink_rows = [row for row in rows if row["expected_eligible"]]
    gray_rows = [row for row in rows if not row["expected_eligible"]]
    click_passed_students = sorted(
        {row["expected_name"] for row in pink_rows if row["click_passed"]}
    )
    gray_only_students = sorted(
        {row["expected_name"] for row in gray_rows}
        - {row["expected_name"] for row in pink_rows}
    )
    return {
        "metrics": {
            "image_count": len(annotation["images"]),
            "expected_card_count": sum(
                len(image["card_indices"])
                for image in annotation["images"].values()
            ),
            "detected_card_count": detected_cards,
            "avatar_count": len(rows),
            "detected_avatar_count": detected_avatars,
            "identity_correct": sum(row["identity_correct"] for row in rows),
            "eligibility_correct": sum(row["eligibility_correct"] for row in rows),
            "pink_count": len(pink_rows),
            "pink_click_passed": sum(row["click_passed"] for row in pink_rows),
            "gray_count": len(gray_rows),
            "gray_blocked": sum(row["click_passed"] for row in gray_rows),
            "click_passed_student_count": len(click_passed_students),
            "gray_only_student_count": len(gray_only_students),
        },
        "instances": rows,
        "identity_failures": [row for row in rows if not row["identity_correct"]],
        "eligibility_failures": [
            row for row in rows if not row["eligibility_correct"]
        ],
        "pink_click_failures": [
            row for row in pink_rows if not row["click_passed"]
        ],
        "gray_wrong_clicks": [
            row for row in gray_rows if not row["click_passed"]
        ],
        "click_passed_students": click_passed_students,
        "gray_only_students": gray_only_students,
    }


def classify_catalog(independent: dict, training: dict, model_dir: Path) -> dict:
    catalog_rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    all_names = sorted(row["Global_name"] for row in catalog_rows)
    independent_by_name: dict[str, list[dict]] = {}
    for row in independent["instances"]:
        independent_by_name.setdefault(row["expected_name"], []).append(row)
    training_by_name: dict[str, list[dict]] = {}
    for row in training["instances"]:
        training_by_name.setdefault(row["expected_name"], []).append(row)

    metadata = json.loads((model_dir / "student_encoder.json").read_text(encoding="utf-8"))
    support_by_name = {
        detail["name"]: detail
        for detail in metadata.get("student_support", {}).values()
    }
    students = []
    categories = {"correct": [], "error": [], "uncertain": []}
    for name in all_names:
        independent_rows = independent_by_name.get(name, [])
        training_rows = training_by_name.get(name, [])
        independent_errors = [
            row
            for row in independent_rows
            if (
                not row["identity_correct"]
                or not row["eligibility_correct"]
                or (
                    row["expected_eligible"]
                    and not row["expected_target_click_passed"]
                )
                or row["potential_wrong_target_click"]
            )
        ]
        independent_pink_passes = [
            row
            for row in independent_rows
            if row["expected_eligible"] and row["expected_target_click_passed"]
        ]
        if independent_errors:
            category = "error"
            reason = "known_failure_on_frozen_comparison"
        elif independent_pink_passes:
            category = "correct"
            reason = "independent_pink_click_passed"
        else:
            category = "uncertain"
            reason = (
                "independent_gray_only"
                if independent_rows
                else "no_independent_pink_fixture"
            )
        categories[category].append(name)
        support = support_by_name.get(name, {})
        students.append(
            {
                "name": name,
                "category": category,
                "reason": reason,
                "support_status": support.get("status", "no_prototype"),
                "prototype_sources": support.get("prototype_sources", []),
                "training_instances": len(training_rows),
                "training_pink_click_passes": sum(
                    row["expected_eligible"] and row["click_passed"]
                    for row in training_rows
                ),
                "independent_instances": len(independent_rows),
                "independent_pink_click_passes": len(independent_pink_passes),
                "independent_failures": [
                    {
                        "image": row["image"],
                        "location": row["display_location"],
                        "expected": row["expected_name"],
                        "top1": row["top1_name"],
                        "identity_correct": row["identity_correct"],
                        "eligibility_correct": row["eligibility_correct"],
                        "click_passed": row["expected_target_click_passed"],
                    }
                    for row in independent_errors
                ],
            }
        )

    training_names = set(training_by_name)
    independent_names = set(independent_by_name)
    newly_target_covered = sorted(independent_names - training_names)
    independent_gray_only = sorted(
        name
        for name, rows in independent_by_name.items()
        if rows and not any(row["expected_eligible"] for row in rows)
    )
    return {
        "definitions": {
            "correct": "At least one frozen-comparison pink click passed and no known comparison error.",
            "error": "At least one frozen-comparison identity, eligibility, click, or wrong-target risk is known.",
            "uncertain": "No frozen-comparison pink click evidence; this never blocks runtime Top-1 selection.",
        },
        "counts": {name: len(values) for name, values in categories.items()},
        "correct": categories["correct"],
        "error": categories["error"],
        "uncertain": categories["uncertain"],
        "students": students,
        "if_independent_v1_were_added_to_training": {
            "classification": "counterfactual_expectation_not_measured",
            "high_probability_error_improvements": categories["error"],
            "new_target_domain_coverage": newly_target_covered,
            "gray_only_still_without_pink_click_evidence": independent_gray_only,
            "note": (
                "Training replay would likely improve represented failures, but no student "
                "moves to independently confirmed correct without a new independent_v2 fixture."
            ),
        },
    }


def architecture_report(model_dir: Path) -> dict:
    catalog_size = len(json.loads(STATIC_DEFAULT_CONFIG)["student_names"])
    metadata = json.loads((model_dir / "student_encoder.json").read_text(encoding="utf-8"))
    gallery_size = int(metadata["gallery_identity_count"])
    return {
        "catalog_identity_count": catalog_size,
        "gallery_identity_count": gallery_size,
        "pipeline": [
            "YOLOX-Nano card/pink-avatar/gray-avatar detection",
            "custom avatar-to-card association and dynamic click point",
            "torchvision MobileNetV3-Small 128-D L2 embedding",
            f"custom {gallery_size}-identity prototype gallery and global cosine Top-1",
            "custom pink/card-available priority selection",
        ],
        "github_components": [
            {
                "name": "YOLOX-Nano",
                "repository": "https://github.com/Megvii-BaseDetection/YOLOX",
                "commit": "6ddff4824372906469a7fae2dc3206c7aa4bbaee",
                "license": "Apache-2.0",
                "runtime": "exported ONNX via OpenCV; repository not vendored",
            },
            {
                "name": "torchvision MobileNetV3-Small ImageNet1K V1",
                "repository": "https://github.com/pytorch/vision",
                "package_version": "0.20.1+cu124",
                "license": "BSD-3-Clause",
                "runtime": "exported ONNX via OpenCV; PyTorch is development-only",
            },
        ],
        "custom_components": [
            "lesson annotations, COCO export, identity-balanced sampling and augmentation",
            "128-D projection head with classification plus supervised contrastive loss",
            "multi-source prototype gallery and global cosine ranking",
            "OpenCV YOLOX decoding, class-agnostic avatar NMS and card association",
            "single-screenshot lesson caching, priority selection, dynamic click and fallback",
        ],
    }


def markdown_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "（无）"


def render_markdown(report: dict) -> str:
    independent = report["independent_v1"]
    training = report["training_replay"]
    capability = report["catalog_capability"]
    catalog_count = report["architecture"]["catalog_identity_count"]
    gallery_count = report["architecture"]["gallery_identity_count"]
    no_prototype_count = sum(
        row["support_status"] == "no_prototype"
        for row in capability["students"]
    )
    lines = [
        "# YOLOX + MobileNetV3 Top-1 组合验收报告",
        "",
        "## 结论",
        "",
        f"- 训练回放：{training['metrics']['identity_correct']}/81 身份，"
        f"{training['metrics']['pink_click_passed']}/71 粉框点击，"
        f"{training['metrics']['gray_blocked']}/10 灰框阻止。",
        f"- independent_v1：{independent['metrics']['identity_correct']}/83 身份，"
        f"{independent['metrics']['eligibility_correct']}/83 粉灰，"
        f"{independent['metrics']['eligible_click_passed']}/70 粉框点击。",
        f"- {catalog_count}人证据分类：correct {capability['counts']['correct']}，"
        f"error {capability['counts']['error']}，uncertain {capability['counts']['uncertain']}。",
        f"- 当前生产图库仍为{gallery_count}人；新增{no_prototype_count}名在重新训练前为"
        "`no_prototype`并回退普通日程。身份分数和分差仍只用于诊断。",
        "",
        "## 模块架构与来源",
        "",
        "| 环节 | 来源 |",
        "|---|---|",
        "| 日程定位 | 官方 YOLOX-Nano；项目自定义三类数据、OpenCV解码、NMS和卡片归属 |",
        "| 学生编码 | 官方 torchvision MobileNetV3-Small/ImageNet权重；项目自定义128维投影头和训练损失 |",
        f"| 身份判断 | 项目自定义{gallery_count}人原型图库与全局余弦Top-1；配置名册{catalog_count}人 |",
        "| 点击业务 | 项目自定义粉框、卡片可用、优先级、动态点击和回退逻辑 |",
        "",
        "## independent_v1 身份错误",
        "",
        "| 图片 | 位置 | 正确身份 | Top-1 | 分数 | 分差 |",
        "|---|---:|---|---|---:|---:|",
    ]
    for row in independent["identity_failures"]:
        lines.append(
            f"| {row['image']} | {row['display_location']} | {row['expected_name']} | "
            f"{row['top1_name']} | {row['score']:.3f} | {row['margin']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## independent_v1 粉灰与点击错误",
            "",
            "| 图片 | 位置 | 身份 | 真实粉灰 | 预测粉灰 | 目标点击卡片 |",
            "|---|---:|---|---|---|---:|",
        ]
    )
    issue_rows = {
        (row["image"], row["location"]): row
        for row in independent["eligibility_failures"]
        + independent["eligible_click_failures"]
        + independent["gray_target_clicks"]
    }
    for row in issue_rows.values():
        lines.append(
            f"| {row['image']} | {row['display_location']} | {row['expected_name']} | "
            f"{'粉' if row['expected_eligible'] else '灰'} | "
            f"{'粉' if row['predicted_eligible'] else '灰'} | "
            f"{row['expected_target_selected_card']} |"
        )
    lines.extend(
        [
            "",
            f"## {catalog_count}人点击证据分类",
            "",
            "这些状态只描述测试证据，不会阻止运行时对任何学生进行Top-1选择。",
            "",
            f"### Correct（{capability['counts']['correct']}）",
            "",
            markdown_list(capability["correct"]),
            "",
            f"### Error（{capability['counts']['error']}）",
            "",
            markdown_list(capability["error"]),
            "",
            f"### Uncertain（{capability['counts']['uncertain']}）",
            "",
            markdown_list(capability["uncertain"]),
            "",
            "## 训练集覆盖",
            "",
            f"训练图粉框点击学生（{len(training['click_passed_students'])}）：",
            "",
            markdown_list(training["click_passed_students"]),
            "",
            f"训练图仅灰框学生（{len(training['gray_only_students'])}）：",
            "",
            markdown_list(training["gray_only_students"]),
            "",
            "训练回放不是独立验证；即使训练图71/71点击成功，没有独立粉框样本的学生仍归为uncertain。",
            "",
            "## 如果未来把 independent_v1 加入训练",
            "",
            "高概率改善的当前错误学生：",
            "",
            markdown_list(
                capability["if_independent_v1_were_added_to_training"][
                    "high_probability_error_improvements"
                ]
            ),
            "",
            "新增真实日程域覆盖：",
            "",
            markdown_list(
                capability["if_independent_v1_were_added_to_training"][
                    "new_target_domain_coverage"
                ]
            ),
            "",
            "这些是预期而非实测；加入训练后必须使用新的independent_v2才能确认。",
            "",
        ]
    )
    return "\n".join(lines)


def build_report(model_dir: Path, benchmark_runs: int) -> dict:
    model_dir = model_dir.resolve()
    independent = evaluate_independent(
        model_dir=model_dir,
        enforce_expected_baseline=False,
        candidate_name="yolox-mobilenetv3-valid-top1",
    )
    independent["performance"] = benchmark_candidate(model_dir, benchmark_runs)
    metrics = independent["metrics"]
    promotion_checks = {
        "cards_40": metrics["detected_card_count"] == 40,
        "avatars_83": metrics["detected_avatar_count"] == 83,
        "identity_at_least_75": metrics["identity_correct"] >= 75,
        "eligibility_at_least_82": metrics["eligibility_correct"] >= 82,
        "pink_clicks_at_least_65": metrics["eligible_click_passed"] >= 65,
        "p95_under_500_ms": independent["performance"]["p95_under_500_ms"],
        "models_under_25_mb": independent["performance"]["models_under_25_mb"],
    }
    independent["promotion"] = {
        "passed": all(promotion_checks.values()),
        "checks": promotion_checks,
    }
    training = evaluate_training_replay(model_dir)
    training_checks = {
        "cards_39": training["metrics"]["detected_card_count"] == 39,
        "avatars_81": training["metrics"]["detected_avatar_count"] == 81,
        "identity_81": training["metrics"]["identity_correct"] == 81,
        "pink_clicks_71": training["metrics"]["pink_click_passed"] == 71,
        "gray_blocked_10": training["metrics"]["gray_blocked"] == 10,
    }
    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "classification": "combined_candidate_frozen_comparison",
        "completed": all(promotion_checks.values()) and all(training_checks.values()),
        "training_action": {
            "performed": False,
            "reason": "Existing sequential ONNX components met the predeclared integration targets.",
        },
        "identity_click_policy": "valid_global_top1",
        "data_isolation": {
            "independent_v1_in_training": False,
            "independent_annotation_sha256": sha256(INDEPENDENT_ANNOTATION_PATH),
            "training_annotation_sha256": sha256(TRAINING_ANNOTATION_PATH),
            "training_fixture_names": sorted(
                json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))["images"]
            ),
            "independent_fixture_names": sorted(
                image["file"]
                for image in json.loads(
                    INDEPENDENT_ANNOTATION_PATH.read_text(encoding="utf-8")
                )["images"]
            ),
            "note": "The frozen set has informed architecture comparison, but not weights, prototypes, or training.",
        },
        "architecture": architecture_report(model_dir),
        "artifacts": {
            name: {
                "bytes": (model_dir / name).stat().st_size,
                "sha256": sha256(model_dir / name),
            }
            for name in MODEL_FILES
        },
        "training_replay_checks": training_checks,
        "training_replay": training,
        "independent_v1": independent,
    }
    report["catalog_capability"] = classify_catalog(independent, training, model_dir)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--benchmark-runs", type=int, default=30)
    args = parser.parse_args()
    report = build_report(args.model_dir, args.benchmark_runs)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "completed": report["completed"],
                "training": report["training_replay"]["metrics"],
                "independent": report["independent_v1"]["metrics"],
                "catalog_counts": report["catalog_capability"]["counts"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
