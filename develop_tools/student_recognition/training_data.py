"""Read the checked-in portrait seed library used by model training.

This module performs no augmentation or training. It only validates and loads
the immutable source images committed under ``data/``.
"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


DATA_DIR = Path(__file__).with_name("data")
HISTORICAL_DIR = DATA_DIR / "historical_portraits"
ROSTER_DIR = DATA_DIR / "roster_montages"
HISTORICAL_MANIFEST = HISTORICAL_DIR / "manifest.json"
ROSTER_ANNOTATIONS = ROSTER_DIR / "roster_montage_annotations.json"


def _checked_image(path: Path, expected_sha256: str) -> np.ndarray:
    raw = path.read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Training image checksum mismatch: {path} "
            f"({actual_sha256} != {expected_sha256})"
        )
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Training image cannot be decoded: {path}")
    return image


def load_historical_portraits(
    manifest_path: Path = HISTORICAL_MANIFEST,
) -> list[tuple[str, str, np.ndarray]]:
    """Load the 177 distinct portraits exported from Git object history."""
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    directory = manifest_path.parent
    portraits = []
    seen_blobs = set()
    for row in rows:
        blob_hash = row["git_blob"]
        if blob_hash in seen_blobs:
            raise ValueError(f"Duplicate historical Git blob: {blob_hash}")
        seen_blobs.add(blob_hash)
        image = _checked_image(directory / row["file"], row["sha256"])
        portraits.append((row["label"], f"history:{blob_hash}", image))
    return portraits


def load_roster_montage_portraits(
    annotation_path: Path = ROSTER_ANNOTATIONS,
) -> list[tuple[str, str, np.ndarray]]:
    """Crop one selected portrait per catalog identity from the EN montages.

    The Chinese and Japanese montages are retained as auditable name evidence.
    Their pixels are intentionally not duplicated in the identity seed set.
    For the two alternate illustrations in the montage, only the explicitly
    selected first form is returned.
    """
    annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
    directory = annotation_path.parent
    language = annotation["training_pixel_language"]
    checked_images = {}
    for row in annotation["files"]:
        image = _checked_image(directory / row["file"], row["sha256"])
        if image.shape[:2] != (row["height"], row["width"]):
            raise ValueError(f"Roster montage dimensions changed: {row['file']}")
        checked_images[(row["language"], row["image_index"])] = image
    images = {
        image_index: image
        for (file_language, image_index), image in checked_images.items()
        if file_language == language
    }

    origin_x, origin_y = annotation["grid"]["origin"]
    step_x, step_y = annotation["grid"]["step"]
    width, height = annotation["grid"]["portrait_size"]
    portraits = []
    seen_names = set()
    for row in annotation["entries"]:
        if not row["include_for_identity_training"]:
            continue
        name = row["config_name"]
        if name in seen_names:
            raise ValueError(f"Duplicate selected roster identity: {name}")
        seen_names.add(name)
        x1 = origin_x + (row["column"] - 1) * step_x
        y1 = origin_y + (row["row"] - 1) * step_y
        crop = images[row["image_index"]][y1:y1 + height, x1:x1 + width].copy()
        if crop.shape[:2] != (height, width):
            raise ValueError(
                f"Roster crop outside image: image {row['image_index']} "
                f"row {row['row']} column {row['column']}"
            )
        crop = cv2.resize(crop, (33, 30), interpolation=cv2.INTER_AREA)
        source = (
            f"roster:{language}:{row['image_index']}:"
            f"{row['row']}:{row['column']}"
        )
        portraits.append((name, source, crop))
    return portraits


def load_seed_portraits() -> list[tuple[str, str, np.ndarray]]:
    """Load all committed historical and roster seed portraits."""
    return load_historical_portraits() + load_roster_montage_portraits()
