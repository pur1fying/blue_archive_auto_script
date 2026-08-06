"""Train Alpha-aware, all-image-balanced MobileNetV3 candidates.

The frozen independent_v1 fixtures are evaluated exactly once, after the
training-domain winner has been selected.  Production remains on the sealed
pre-Wikiru rollback bundle unless every no-regression gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("TORCH_HOME", str(ROOT / ".training-runs" / "torch-cache"))

from develop_tools.student_recognition.train_pretrained_classifier import (
    _pretrained_trainer,
)


PRODUCTION = ROOT / "src" / "models" / "student_recognition"
RUN_ROOT = (
    ROOT
    / ".training-runs"
    / "student_recognition"
    / "wikiru270-alpha-balanced"
)
EXPERIMENT = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "experiments"
    / "yolox_mobilenetv3_wikiru270_alpha_balanced_top1"
)
SUMMARY_PATH = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "wikiru270_alpha_balanced_training_report.json"
)
ROLLBACK_REPORT = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "rollback_independent_report.json"
)
LOCATOR_DIAGNOSTIC = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "yolox_locator_grouped_diagnostic.json"
)
IDENTITY_FILES = ("student_encoder.onnx", "student_encoder.json", "gallery.npz")
LOCATOR_FILES = ("lesson_locator.onnx", "lesson_locator.json")
MODEL_FILES = LOCATOR_FILES + IDENTITY_FILES
ROLLBACK_HASHES = {
    "student_encoder.onnx": "a9358974bfae59bd9229c7811fc903d82c02644c995c17c9c5dd1df29f679a41",
    "gallery.npz": "1eda40daa3f264900f6d9252963e68f19448d9e5cf99440ef9721c722d31b2bd",
    "student_encoder.json": "37227741b47bb8a5b7324757a09f114aeb5fc1feac3d3d3ed5d070d448faccac",
}
DATA_ARTIFACTS = (
    ROOT / "develop_tools" / "student_recognition" / "data" / "historical_portraits" / "manifest.json",
    ROOT / "develop_tools" / "student_recognition" / "data" / "historical_portraits" / "similarity_audit.json",
    ROOT / "develop_tools" / "student_recognition" / "data" / "wikiru_portraits" / "manifest.json",
    ROOT / "develop_tools" / "student_recognition" / "data" / "roster_montages" / "roster_montage_annotations.json",
    ROOT / "develop_tools" / "student_recognition" / "lesson_locator_annotations.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_rows(directory: Path) -> dict:
    return {
        name: {"bytes": (directory / name).stat().st_size, "sha256": sha256(directory / name)}
        for name in MODEL_FILES
    }


def fresh_directory(root: Path, seed: int) -> Path:
    root = root.resolve()
    output = (root / f"seed-{seed}").resolve()
    if root not in output.parents:
        raise ValueError(f"Unsafe candidate directory: {output}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def atomic_copy(source: Path, destination: Path, filenames) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        temporary = destination / f"{name}.new"
        shutil.copy2(source / name, temporary)
        temporary.replace(destination / name)


def training_integrity(report: dict) -> tuple[bool, list[str]]:
    ignored_for_seed_selection = {"cpu_p95_under_500ms"}
    failures = [
        failure
        for failure in report["hard_failures"]
        if failure not in ignored_for_seed_selection
    ]
    metrics = report["grouped_cross_validation"]["encoder_overall"]
    if metrics["correct"] < 74:
        failures.append("cross_validation_correct_at_least_74")
    if (metrics["macro_recall"] or 0.0) < 0.9054:
        failures.append("cross_validation_macro_recall_at_least_0_9054")
    return not failures, failures


def seed_selection_key(attempt: dict) -> tuple:
    metrics = attempt["grouped_encoder"]
    return (
        metrics["correct"],
        metrics["macro_recall"] or 0.0,
        metrics["minimum_margin"] or -1.0,
    )


def independent_no_regression(candidate: dict, baseline: dict) -> dict:
    baseline_rows = {
        (row["image"], row["location"]): row for row in baseline["instances"]
    }
    regressions = []
    new_wrong_click_risks = []
    new_gray_clicks = []
    for row in candidate["instances"]:
        before = baseline_rows[(row["image"], row["location"])]
        comparison = {
            "image": row["image"],
            "location": row["location"],
            "expected_name": row["expected_name"],
            "before_top1": before["top1_name"],
            "after_top1": row["top1_name"],
        }
        if before["identity_correct"] and not row["identity_correct"]:
            regressions.append(comparison)
        if row["potential_wrong_target_click"] and not before["potential_wrong_target_click"]:
            new_wrong_click_risks.append(comparison)
        if (
            not row["expected_eligible"]
            and not row["expected_target_click_passed"]
            and before["expected_target_click_passed"]
        ):
            new_gray_clicks.append(comparison)

    metrics = candidate["metrics"]
    checks = {
        "identity_at_least_75": metrics["identity_correct"] >= 75,
        "pink_clicks_at_least_65": metrics["eligible_click_passed"] >= 65,
        "eligibility_at_least_82": metrics["eligibility_correct"] >= 82,
        "no_previously_correct_identity_regressions": not regressions,
        "no_new_wrong_card_click_risks": not new_wrong_click_risks,
        "no_new_gray_clicks": not new_gray_clicks,
        "cpu_p95_under_500ms": candidate["performance"]["p95_under_500_ms"],
        "models_under_25mb": candidate["performance"]["models_under_25_mb"],
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "identity_regressions": regressions,
        "new_wrong_card_click_risks": new_wrong_click_risks,
        "new_gray_clicks": new_gray_clicks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[20260731],
    )
    parser.add_argument("--output-root", type=Path, default=RUN_ROOT)
    parser.add_argument("--pretrain-epochs", type=int, default=100)
    parser.add_argument("--frozen-backbone-epochs", type=int, default=20)
    parser.add_argument("--fold-epochs", type=int, default=35)
    parser.add_argument("--final-epochs", type=int, default=80)
    parser.add_argument("--benchmark-runs", type=int, default=90)
    parser.add_argument("--no-promote", action="store_true")
    parser.add_argument(
        "--reuse-completed",
        action="store_true",
        help="Reuse a completed requested seed without retraining it.",
    )
    args = parser.parse_args()

    from develop_tools.student_recognition import train_student_models as training
    from develop_tools.student_recognition.evaluate_combined_top1 import (
        build_report as build_combined_report,
        render_markdown,
    )

    if {name: sha256(PRODUCTION / name) for name in IDENTITY_FILES} != ROLLBACK_HASHES:
        raise RuntimeError("Production identity bundle is not the audited rollback version")
    rollback = json.loads(ROLLBACK_REPORT.read_text(encoding="utf-8"))
    locator_before = {name: sha256(PRODUCTION / name) for name in LOCATOR_FILES}
    locator_diagnostic = json.loads(LOCATOR_DIAGNOSTIC.read_text(encoding="utf-8"))
    frozen_locator_metrics = {
        "architecture": "YOLOX-Nano",
        "frozen": True,
        "folds": locator_diagnostic["folds"],
    }
    training._train_student_encoder = _pretrained_trainer(
        training,
        args.frozen_backbone_epochs,
    )

    prior_independent_evaluations = 0
    if args.reuse_completed and SUMMARY_PATH.exists():
        previous_summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        prior_independent_evaluations = int(
            previous_summary.get("independent_evaluations", 0)
        )
    summary = {
        "version": 2,
        "classification": "alpha_aware_all_image_balanced_training_domain_selection",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_action": {"performed": True},
        "architecture": "torchvision-MobileNetV3-Small-ImageNet1K-V1",
        "environment": {
            "torch_version": training.torch.__version__,
            "opencv_version": training.cv2.__version__,
            "device": str(training.training_device()),
            "cuda_device": (
                training.torch.cuda.get_device_name(0)
                if training.torch.cuda.is_available()
                else None
            ),
            "onnx_opset": 12,
        },
        "data_artifacts": {
            path.relative_to(ROOT).as_posix(): {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in DATA_ARTIFACTS
        },
        "data_policy": {
            "raw_training_instances": 793,
            "identities": 270,
            "wikiru_alpha_preserved": True,
            "normalized_portrait_extent": 90,
            "all_images_visited_each_epoch": True,
            "independent_v1_used_for_training_seed_or_gallery_selection": False,
        },
        "seed_policy": {
            "seeds": args.seeds,
            "all_requested_seeds_complete_before_selection": True,
            "selection_order": ["five_fold_correct", "macro_recall", "minimum_margin"],
        },
        "schedule": {
            "pretrain_epochs": args.pretrain_epochs,
            "frozen_backbone_epochs": args.frozen_backbone_epochs,
            "fold_epochs": args.fold_epochs,
            "final_epochs": args.final_epochs,
        },
        "rollback_production_hashes": artifact_rows(PRODUCTION),
        "frozen_locator_hashes_before": locator_before,
        "attempts": [],
        "selected_seed": None,
        "independent_evaluations": prior_independent_evaluations,
        "promoted": False,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    candidates = []
    for seed in args.seeds:
        output = (args.output_root.resolve() / f"seed-{seed}").resolve()
        reusable = output / "validation_report.json"
        if args.reuse_completed and reusable.exists():
            report = json.loads(reusable.read_text(encoding="utf-8"))
            encoder_metadata = json.loads(
                (output / "student_encoder.json").read_text(encoding="utf-8")
            )
        else:
            output = fresh_directory(args.output_root, seed)
            atomic_copy(PRODUCTION, output, LOCATOR_FILES)
            diagnostics = training.train_encoder(
                output,
                epochs=args.fold_epochs,
                pretrain_epochs=args.pretrain_epochs,
                final_epochs=args.final_epochs,
                seed=seed,
            )
            diagnostics["metadata"].update(
                {
                    "architecture": "torchvision-MobileNetV3-Small-ImageNet1K-V1",
                    "backbone_pretrained": True,
                    "seed_pretrain_frozen_backbone_epochs": args.frozen_backbone_epochs,
                    "preprocessing_revision": "alpha-aware-normalized-extent-90-v2",
                    "sampling_revision": "all-images-identity-balanced-v2",
                }
            )
            encoder_metadata = diagnostics["metadata"]
            (output / "student_encoder.json").write_text(
                json.dumps(encoder_metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report = training.build_validation_report(
                output,
                seed,
                frozen_locator_metrics,
                diagnostics,
            )
        integrity_passed, integrity_failures = training_integrity(report)
        report["training_domain_promotion_gate"] = {
            "passed": integrity_passed,
            "failures": integrity_failures,
            "cpu_performance_used_for_seed_selection": False,
        }
        report["training_action"] = {
            "performed": True,
            "independent_v1_used_for_training_or_selection": False,
        }
        (output / "validation_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        attempt = {
            "seed": seed,
            "candidate_directory": output.relative_to(ROOT).as_posix(),
            "training_integrity_passed": integrity_passed,
            "training_integrity_failures": integrity_failures,
            "grouped_encoder": report["grouped_cross_validation"]["encoder_overall"],
            "gallery_policy": encoder_metadata["gallery_policy"],
            "gallery_policy_diagnostics": encoder_metadata["gallery_policy_diagnostics"],
            "training_replay": report["training_replay"],
            "end_to_end_replay": report["end_to_end_replay"],
            "performance_diagnostic_not_used_for_seed_selection": report["performance"],
            "artifacts": artifact_rows(output),
        }
        summary["attempts"].append(attempt)
        if integrity_passed:
            candidates.append((attempt, output, report))
        SUMMARY_PATH.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"seed": seed, "passed": integrity_passed, "failures": integrity_failures}), flush=True)

    if not candidates:
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        summary["promotion_failure"] = "no_training_domain_candidate_passed"
        SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    selected_attempt, selected_dir, selected_validation = max(
        candidates,
        key=lambda item: seed_selection_key(item[0]),
    )
    summary["selected_seed"] = selected_attempt["seed"]
    summary["selected_candidate"] = selected_dir.relative_to(ROOT).as_posix()
    atomic_copy(selected_dir, EXPERIMENT, MODEL_FILES)
    shutil.copy2(selected_dir / "validation_report.json", EXPERIMENT / "validation_report.json")

    # This is intentionally the first and only independent_v1 evaluation in the run.
    summary["independent_evaluations"] += 1
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    combined = build_combined_report(
        EXPERIMENT,
        args.benchmark_runs,
        baseline={"independent_v1": rollback},
        training_summary=summary,
        independent_blocks_completion=True,
    )
    strict = independent_no_regression(combined["independent_v1"], rollback)
    combined["strict_no_regression_promotion"] = strict
    combined["completed"] = bool(combined["completed"] and strict["passed"])
    candidate_json = Path(__file__).with_name("combined_top1_alpha_balanced_report.json")
    candidate_md = Path(__file__).with_name("combined_top1_alpha_balanced_report.md")
    candidate_json.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    candidate_md.write_text(render_markdown(combined), encoding="utf-8")

    if combined["completed"] and not args.no_promote:
        atomic_copy(selected_dir, PRODUCTION, IDENTITY_FILES)
        temporary_report = Path(__file__).with_name("validation_report.json.new")
        shutil.copy2(selected_dir / "validation_report.json", temporary_report)
        temporary_report.replace(Path(__file__).with_name("validation_report.json"))
        summary["promoted"] = True
    else:
        current_identity = {name: sha256(PRODUCTION / name) for name in IDENTITY_FILES}
        if current_identity != ROLLBACK_HASHES:
            raise RuntimeError("Failed candidate changed the rollback production bundle")

    locator_after = {name: sha256(PRODUCTION / name) for name in LOCATOR_FILES}
    if locator_after != locator_before:
        raise RuntimeError("Frozen YOLOX locator changed")
    summary.update(
        {
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "strict_no_regression_promotion": strict,
            "candidate_completed": combined["completed"],
            "frozen_locator_hashes_after": locator_after,
            "production_artifacts_after": artifact_rows(PRODUCTION),
        }
    )
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected_seed": summary["selected_seed"], "promoted": summary["promoted"], "strict": strict}, ensure_ascii=False, indent=2))
    return 0 if combined["completed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
