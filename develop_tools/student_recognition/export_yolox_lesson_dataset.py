"""Build an isolated COCO dataset for the YOLOX lesson-locator experiment.

Only the five manually labelled ``new_ui`` training fixtures are accepted as
input.  The sealed ``lesson_independent_v1`` comparison set is intentionally
not imported, enumerated, or accepted by this module.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ANNOTATION_PATH = Path(__file__).with_name("lesson_locator_annotations.json")
FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
DEFAULT_OUTPUT = ROOT / ".training-runs" / "student_recognition" / "yolox_dataset"
EXPECTED_IMAGES = tuple(f"new_ui_{index}.png" for index in range(1, 6))
CATEGORIES = (
    {"id": 1, "name": "lesson_card", "supercategory": "lesson"},
    {"id": 2, "name": "eligible_avatar", "supercategory": "avatar"},
    {"id": 3, "name": "plain_avatar", "supercategory": "avatar"},
)


def _objects(annotation: dict, image_name: str) -> list[tuple[int, list[float]]]:
    image_annotation = annotation["images"][image_name]
    objects: list[tuple[int, list[float]]] = []
    for card_index in image_annotation["card_indices"]:
        objects.append((1, [float(value) for value in annotation["card_boxes"][card_index]]))
    geometry = annotation["avatar_geometry"]
    for card_index, slot, eligible in image_annotation["avatars"]:
        card_x, card_y = annotation["card_boxes"][card_index][:2]
        x1 = card_x + geometry["relative_x"][slot]
        y1 = card_y + geometry["relative_y"]
        objects.append(
            (
                2 if eligible else 3,
                [float(x1), float(y1), float(x1 + geometry["width"]), float(y1 + geometry["height"])],
            )
        )
    return objects


def _augment(
    image: np.ndarray,
    objects: list[tuple[int, list[float]]],
    rng: random.Random,
) -> tuple[np.ndarray, list[tuple[int, list[float]]]]:
    height, width = image.shape[:2]
    scale = rng.uniform(0.85, 1.15)
    translate_x = rng.uniform(-0.035, 0.035) * width
    translate_y = rng.uniform(-0.035, 0.035) * height
    matrix = np.asarray(
        [[scale, 0.0, (1.0 - scale) * width / 2.0 + translate_x],
         [0.0, scale, (1.0 - scale) * height / 2.0 + translate_y]],
        dtype=np.float32,
    )
    transformed = cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=rng.choice((cv2.INTER_AREA, cv2.INTER_LINEAR, cv2.INTER_CUBIC)),
        borderMode=cv2.BORDER_REFLECT_101,
    )
    alpha = rng.uniform(0.82, 1.18)
    beta = rng.uniform(-18.0, 18.0)
    transformed = cv2.convertScaleAbs(transformed, alpha=alpha, beta=beta)
    if rng.random() < 0.25:
        transformed = cv2.GaussianBlur(transformed, (3, 3), rng.uniform(0.1, 0.8))

    transformed_objects = []
    for category_id, (x1, y1, x2, y2) in objects:
        points = np.asarray(((x1, y1, 1.0), (x2, y2, 1.0)), dtype=np.float32)
        mapped = points @ matrix.T
        nx1 = float(np.clip(mapped[0, 0], 0, width - 1))
        ny1 = float(np.clip(mapped[0, 1], 0, height - 1))
        nx2 = float(np.clip(mapped[1, 0], 1, width))
        ny2 = float(np.clip(mapped[1, 1], 1, height))
        if nx2 - nx1 >= 4 and ny2 - ny1 >= 4:
            transformed_objects.append((category_id, [nx1, ny1, nx2, ny2]))
    return transformed, transformed_objects


def _write_coco(
    directory: Path,
    split: str,
    records: list[tuple[str, np.ndarray, list[tuple[int, list[float]]]]],
) -> dict:
    image_dir = directory / f"{split}2017"
    image_dir.mkdir(parents=True, exist_ok=True)
    images = []
    annotations = []
    annotation_id = 1
    for image_id, (file_name, image, objects) in enumerate(records, start=1):
        path = image_dir / file_name
        if not cv2.imwrite(str(path), image):
            raise OSError(f"Unable to write {path}")
        height, width = image.shape[:2]
        images.append({"id": image_id, "file_name": file_name, "width": width, "height": height})
        for category_id, (x1, y1, x2, y2) in objects:
            box_width = x2 - x1
            box_height = y2 - y1
            annotations.append(
                {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": [x1, y1, box_width, box_height],
                    "area": box_width * box_height,
                    "iscrowd": 0,
                }
            )
            annotation_id += 1
    payload = {
        "info": {
            "description": "BAAS lesson-locator YOLOX experiment",
            "version": "1",
        },
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": list(CATEGORIES),
    }
    annotation_dir = directory / "annotations"
    annotation_dir.mkdir(parents=True, exist_ok=True)
    (annotation_dir / f"instances_{split}2017.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def export_dataset(
    output_dir: Path = DEFAULT_OUTPUT,
    validation_image: str | None = None,
    augmentations_per_image: int = 16,
    seed: int = 20260731,
) -> dict:
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    image_names = tuple(sorted(annotation["images"]))
    if image_names != EXPECTED_IMAGES:
        raise ValueError(f"Unexpected lesson training fixtures: {image_names}")
    if validation_image is not None and validation_image not in image_names:
        raise ValueError(f"Unknown validation image: {validation_image}")

    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    train_records = []
    validation_records = []
    for image_index, image_name in enumerate(image_names):
        image = cv2.imread(str(FIXTURE_DIR / image_name), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(FIXTURE_DIR / image_name)
        objects = _objects(annotation, image_name)
        record = (image_name, image, objects)
        if image_name == validation_image:
            validation_records.append(record)
            continue
        train_records.append(record)
        for augmentation_index in range(augmentations_per_image):
            rng = random.Random(seed + image_index * 1000 + augmentation_index)
            augmented_image, augmented_objects = _augment(image, objects, rng)
            train_records.append(
                (
                    f"{Path(image_name).stem}_aug_{augmentation_index:03d}.png",
                    augmented_image,
                    augmented_objects,
                )
            )
    if not validation_records:
        # The final all-data run does not use this duplicate for model selection;
        # YOLOX still requires a syntactically valid validation annotation.
        image_name = image_names[0]
        image = cv2.imread(str(FIXTURE_DIR / image_name), cv2.IMREAD_COLOR)
        validation_records.append((image_name, image, _objects(annotation, image_name)))

    train_payload = _write_coco(output_dir, "train", train_records)
    validation_payload = _write_coco(output_dir, "val", validation_records)
    manifest = {
        "version": 1,
        "source_annotation": ANNOTATION_PATH.relative_to(ROOT).as_posix(),
        "source_images": list(image_names),
        "validation_image": validation_image,
        "augmentations_per_training_image": augmentations_per_image,
        "seed": seed,
        "training_image_count": len(train_payload["images"]),
        "validation_image_count": len(validation_payload["images"]),
        "original_card_count": sum(len(value["card_indices"]) for value in annotation["images"].values()),
        "original_avatar_count": sum(len(value["avatars"]) for value in annotation["images"].values()),
        "categories": list(CATEGORIES),
        "independent_comparison_data_included": False,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validation-image", choices=EXPECTED_IMAGES)
    parser.add_argument("--augmentations-per-image", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260731)
    args = parser.parse_args()
    print(
        json.dumps(
            export_dataset(
                output_dir=args.output,
                validation_image=args.validation_image,
                augmentations_per_image=args.augmentations_per_image,
                seed=args.seed,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
