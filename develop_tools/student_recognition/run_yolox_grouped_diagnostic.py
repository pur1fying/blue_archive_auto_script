"""Run five screenshot-grouped YOLOX diagnostics without independent data."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

from export_yolox_lesson_dataset import (
    EXPECTED_IMAGES,
    export_dataset,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(__file__).with_name("yolox_locator_grouped_diagnostic.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yolox-root", type=Path, required=True)
    parser.add_argument("--pretrained", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--augmentations-per-image", type=int, default=4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    runs_root = ROOT / ".training-runs" / "student_recognition" / "yolox_grouped"
    outputs = runs_root / "outputs"
    results = []
    for fold_index, held_out in enumerate(EXPECTED_IMAGES, start=1):
        dataset = runs_root / f"fold_{fold_index}_dataset"
        manifest = export_dataset(
            dataset,
            validation_image=held_out,
            augmentations_per_image=args.augmentations_per_image,
        )
        experiment_name = f"baas_yolox_grouped_fold_{fold_index}"
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(args.yolox_root.resolve())
        environment["BAAS_YOLOX_DATASET"] = str(dataset.resolve())
        environment["BAAS_YOLOX_OUTPUT"] = str(outputs.resolve())
        command = [
            str(args.python.resolve()),
            str((args.yolox_root / "tools" / "train.py").resolve()),
            "-f",
            str(Path(__file__).with_name("yolox_lesson_exp.py").resolve()),
            "-expn",
            experiment_name,
            "-d",
            "1",
            "-b",
            "8",
            "--fp16",
            "-c",
            str(args.pretrained.resolve()),
            "-l",
            "tensorboard",
            "max_epoch",
            str(args.epochs),
            "eval_interval",
            str(args.epochs),
            "no_aug_epochs",
            "0",
        ]
        subprocess.run(command, cwd=ROOT, env=environment, check=True)
        checkpoint_path = outputs / experiment_name / "best_ckpt.pth"
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        results.append(
            {
                "fold": fold_index,
                "held_out_image": held_out,
                "training_source_images": [
                    name for name in EXPECTED_IMAGES if name != held_out
                ],
                "training_image_count_with_augmentations": manifest["training_image_count"],
                "held_out_image_count": manifest["validation_image_count"],
                "ap_50_95": float(checkpoint.get("best_ap", checkpoint.get("ap", 0.0))),
                "checkpoint_sha256": sha256(checkpoint_path),
            }
        )
    report = {
        "version": 1,
        "classification": "training_domain_grouped_diagnostic_not_independent_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "architecture": "YOLOX-Nano",
        "epochs_per_fold": args.epochs,
        "augmentations_per_training_image": args.augmentations_per_image,
        "source_images": list(EXPECTED_IMAGES),
        "independent_comparison_data_included": False,
        "folds": results,
        "mean_ap_50_95": sum(item["ap_50_95"] for item in results) / len(results),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
