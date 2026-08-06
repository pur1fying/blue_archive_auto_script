"""Train and promote the Wikiru-augmented MobileNetV3 identity component.

The YOLOX lesson locator is frozen.  Seed retries are decided exclusively by
training-domain integrity and replay checks; the sealed target-domain regression
fixtures are deliberately absent from this module.
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


PRODUCTION_MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
RUN_ROOT = ROOT / ".training-runs" / "student_recognition" / "wikiru270"
EXPERIMENT_DIR = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "experiments"
    / "yolox_mobilenetv3_wikiru270_top1"
)
SUMMARY_REPORT = (
    ROOT / "develop_tools" / "student_recognition" / "wikiru270_training_report.json"
)
LOCATOR_DIAGNOSTIC = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "yolox_locator_grouped_diagnostic.json"
)
MODEL_FILES = (
    "lesson_locator.onnx",
    "lesson_locator.json",
    "student_encoder.onnx",
    "student_encoder.json",
    "gallery.npz",
)
LOCATOR_FILES = ("lesson_locator.onnx", "lesson_locator.json")
DATA_ARTIFACTS = (
    ROOT / "develop_tools" / "student_recognition" / "data" / "historical_portraits" / "manifest.json",
    ROOT / "develop_tools" / "student_recognition" / "data" / "wikiru_portraits" / "manifest.json",
    ROOT / "develop_tools" / "student_recognition" / "data" / "roster_montages" / "roster_montage_annotations.json",
    ROOT / "develop_tools" / "student_recognition" / "lesson_locator_annotations.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_rows(directory: Path) -> dict:
    return {
        name: {
            "bytes": (directory / name).stat().st_size,
            "sha256": _sha256(directory / name),
        }
        for name in MODEL_FILES
    }


def _fresh_seed_directory(root: Path, seed: int) -> Path:
    root = root.resolve()
    output = (root / f"seed-{seed}").resolve()
    if root not in output.parents:
        raise ValueError(f"Unsafe candidate directory: {output}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def _copy_bundle(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in MODEL_FILES:
        temporary = destination / f"{name}.new"
        shutil.copy2(source / name, temporary)
        temporary.replace(destination / name)


def _attempt_summary(report: dict, output_dir: Path) -> dict:
    encoder = report["training_replay"]
    end_to_end = report["end_to_end_replay"]
    return {
        "seed": report["environment"]["seed"],
        "candidate_directory": str(output_dir.relative_to(ROOT)).replace("\\", "/"),
        "completed": report["completed"],
        "hard_failures": report["hard_failures"],
        "grouped_encoder": report["grouped_cross_validation"]["encoder_overall"],
        "training_replay": encoder,
        "end_to_end_replay": end_to_end,
        "performance": report["performance"],
        "resources": report["resources"],
        "artifacts": _artifact_rows(output_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[20260731, 20260801, 20260802],
    )
    parser.add_argument("--output-root", type=Path, default=RUN_ROOT)
    parser.add_argument("--pretrain-epochs", type=int, default=100)
    parser.add_argument("--frozen-backbone-epochs", type=int, default=20)
    parser.add_argument("--fold-epochs", type=int, default=35)
    parser.add_argument("--final-epochs", type=int, default=80)
    parser.add_argument("--no-promote", action="store_true")
    args = parser.parse_args()

    from develop_tools.student_recognition import train_student_models as training

    locator_before = {name: _sha256(PRODUCTION_MODEL_DIR / name) for name in LOCATOR_FILES}
    locator_diagnostic = json.loads(LOCATOR_DIAGNOSTIC.read_text(encoding="utf-8"))
    frozen_locator_metrics = {
        "architecture": "YOLOX-Nano",
        "frozen": True,
        "source_report": str(LOCATOR_DIAGNOSTIC.relative_to(ROOT)).replace("\\", "/"),
        "folds": locator_diagnostic["folds"],
    }
    training._train_student_encoder = _pretrained_trainer(
        training,
        args.frozen_backbone_epochs,
    )

    summary = {
        "version": 1,
        "classification": "wikiru270_mobilenetv3_training_and_training_domain_selection",
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
            str(path.relative_to(ROOT)).replace("\\", "/"): {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in DATA_ARTIFACTS
        },
        "frozen_locator": {
            "architecture": "YOLOX-Nano",
            "hashes_before": locator_before,
            "retrained": False,
        },
        "seed_policy": {
            "ordered_seeds": args.seeds,
            "stop_at_first_training_domain_pass": True,
            "independent_v1_used_for_seed_selection": False,
        },
        "schedule": {
            "pretrain_epochs": args.pretrain_epochs,
            "frozen_backbone_epochs": args.frozen_backbone_epochs,
            "fold_epochs": args.fold_epochs,
            "final_epochs": args.final_epochs,
        },
        "attempts": [],
        "selected_seed": None,
        "promoted": False,
    }
    SUMMARY_REPORT.parent.mkdir(parents=True, exist_ok=True)

    selected = None
    for seed in args.seeds:
        output_dir = _fresh_seed_directory(args.output_root, seed)
        for name in LOCATOR_FILES:
            shutil.copy2(PRODUCTION_MODEL_DIR / name, output_dir / name)

        diagnostics = training.train_encoder(
            output_dir,
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
                "wikiru270_training_run": True,
            }
        )
        (output_dir / "student_encoder.json").write_text(
            json.dumps(diagnostics["metadata"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report = training.build_validation_report(
            output_dir,
            seed,
            frozen_locator_metrics,
            diagnostics,
        )
        report["training_action"] = {
            "performed": True,
            "independent_v1_used_for_training_or_selection": False,
        }
        report["frozen_locator_hashes"] = locator_before
        (output_dir / "validation_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary["attempts"].append(_attempt_summary(report, output_dir))
        SUMMARY_REPORT.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "seed": seed,
                    "completed": report["completed"],
                    "hard_failures": report["hard_failures"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if report["completed"]:
            selected = (output_dir, report)
            break

    if selected is None:
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        SUMMARY_REPORT.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError("No seed passed the training-domain hard acceptance checks")

    selected_dir, selected_report = selected
    _copy_bundle(selected_dir, EXPERIMENT_DIR)
    shutil.copy2(selected_dir / "validation_report.json", EXPERIMENT_DIR / "validation_report.json")
    if not args.no_promote:
        training._promote_candidate(selected_dir, selected_report)

    locator_after = {name: _sha256(PRODUCTION_MODEL_DIR / name) for name in LOCATOR_FILES}
    if locator_after != locator_before:
        raise RuntimeError("Frozen YOLOX locator hashes changed during identity promotion")
    summary.update(
        {
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "selected_seed": selected_report["environment"]["seed"],
            "selected_candidate": str(selected_dir.relative_to(ROOT)).replace("\\", "/"),
            "promoted": not args.no_promote,
            "production_artifacts": _artifact_rows(PRODUCTION_MODEL_DIR),
        }
    )
    summary["frozen_locator"]["hashes_after"] = locator_after
    SUMMARY_REPORT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
