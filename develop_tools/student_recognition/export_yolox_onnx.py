"""Export the trained YOLOX lesson locator as a static OpenCV ONNX model."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch
from torch import nn


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yolox-root", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--experiment", type=Path, default=Path(__file__).with_name("yolox_lesson_exp.py"))
    args = parser.parse_args()

    sys.path.insert(0, str(args.yolox_root.resolve()))
    from yolox.exp import get_exp
    from yolox.models.network_blocks import SiLU
    from yolox.utils import replace_module

    experiment = get_exp(str(args.experiment), None)
    model = experiment.get_model().eval()
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint.get("model", checkpoint))
    model = replace_module(model, nn.SiLU, SiLU)
    model.head.decode_in_inference = True

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "lesson_locator.onnx"
    dummy = torch.zeros(1, 3, experiment.test_size[0], experiment.test_size[1])
    torch.onnx.export(
        model,
        dummy,
        output_path,
        input_names=["images"],
        output_names=["detections"],
        opset_version=12,
        do_constant_folding=True,
    )
    metadata = {
        "version": 2,
        "backend": "yolox",
        "architecture": "YOLOX-Nano",
        "input_width": experiment.test_size[1],
        "input_height": experiment.test_size[0],
        "class_names": ["lesson_card", "eligible_avatar", "plain_avatar"],
        "confidence_thresholds": {
            "lesson_card": 0.20,
            "eligible_avatar": 0.20,
            "plain_avatar": 0.20
        },
        "nms_threshold": 0.50,
        "minimum_cards": 1,
        "preprocessing": "top_left_letterbox_114_bgr_0_255",
        "decoded_output": True,
        "opset": 12,
        "source": {
            "repository": "https://github.com/Megvii-BaseDetection/YOLOX",
            "commit": "6ddff4824372906469a7fae2dc3206c7aa4bbaee",
            "license": "Apache-2.0"
        },
        "sha256": sha256(output_path),
    }
    (args.output_dir / "lesson_locator.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
