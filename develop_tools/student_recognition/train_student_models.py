"""Train and export the lightweight lesson/student models.

Run from the repository root with the development-only requirements installed:

    python develop_tools/student_recognition/train_student_models.py all
"""

import argparse
import collections
import hashlib
import json
import random
import shutil
import statistics
import sys
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.student_recognition.catalog import StudentCatalog
from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.lesson_locator import LessonLocator
from core.student_recognition.recognizer import StudentRecognizer
from core.student_recognition.service import StudentRecognitionService
from develop_tools.student_recognition.models import (
    LessonSegmentationNet,
    StudentEncoderTrainer,
)
from develop_tools.student_recognition.training_data import (
    load_historical_portraits,
    load_roster_montage_portraits,
)


FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
ANNOTATION_PATH = Path(__file__).with_name("lesson_locator_annotations.json")
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
RUNS_DIR = ROOT / ".training-runs" / "student_recognition"
REPORT_PATH = Path(__file__).with_name("validation_report.json")
SEED = 20260731
SAMPLES_PER_IDENTITY = 3

MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # cuDNN's deterministic stream path is unstable on the bundled Windows
    # driver (CUDNN_STATUS_BAD_PARAM_STREAM_MISMATCH after long runs). Seeds
    # still control sampling/initialisation; use the normal stable kernels.
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = True


def training_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_historical_templates() -> list[tuple[str, str, np.ndarray]]:
    return load_historical_portraits()


def load_labeled_target_crops() -> list[tuple[str, str, str, np.ndarray]]:
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    card_boxes = annotation["card_boxes"]
    geometry = annotation["avatar_geometry"]
    labeled_crops = []
    for image_name, image_annotation in annotation["images"].items():
        screenshot = cv2.imread(str(FIXTURE_DIR / image_name))
        if screenshot is None:
            raise FileNotFoundError(FIXTURE_DIR / image_name)
        for location, name in image_annotation.get("identity_labels", {}).items():
            card_index, avatar_slot = (int(value) for value in location.split(":"))
            card_x, card_y = card_boxes[card_index][:2]
            x1 = card_x + geometry["relative_x"][avatar_slot]
            y1 = card_y + geometry["relative_y"]
            crop = screenshot[
                y1:y1 + geometry["height"],
                x1:x1 + geometry["width"],
            ].copy()
            labeled_crops.append((name, image_name, location, crop))
    return labeled_crops


def load_runtime_labeled_target_crops(
    model_dir: Optional[Path] = None,
) -> list[tuple[str, str, str, np.ndarray]]:
    """Pair manual identities with the crops produced by the runtime locator."""
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    locator = LessonLocator(model_dir)
    labeled_crops = []
    for image_name, image_annotation in annotation["images"].items():
        screenshot = cv2.imread(str(FIXTURE_DIR / image_name))
        if screenshot is None:
            raise FileNotFoundError(FIXTURE_DIR / image_name)
        located = {
            f"{card.index}:{slot}": avatar.crop
            for card in locator.locate(screenshot)
            for slot, avatar in enumerate(card.avatars)
        }
        labels = image_annotation.get("identity_labels", {})
        if set(located) != set(labels):
            raise ValueError(
                f"Runtime locator positions do not match annotations for {image_name}"
            )
        for location, name in labels.items():
            labeled_crops.append((name, image_name, location, located[location]))
    return labeled_crops


def load_target_domain_portraits(validation_image: Optional[str] = None) -> tuple[
    list[tuple[str, str, np.ndarray]],
    list[tuple[str, str, np.ndarray]],
]:
    """Load manually labelled identities while keeping screenshots grouped.

    Returning portraits in the historical 33x30 representation lets the same
    augmentation pipeline cover both sources. When ``validation_image`` is
    provided, that complete screenshot is excluded from training so none of
    its augmented variants can leak into the validation fold.
    """
    train_portraits = []
    validation_portraits = []
    for name, image_name, location, crop in load_labeled_target_crops():
        # Match the runtime recognizer's undecorated base view.
        x2 = crop.shape[1] - max(5, round(crop.shape[1] * 0.12))
        y2 = crop.shape[0] - max(5, round(crop.shape[0] * 0.12))
        portrait = cv2.resize(
            crop[3:y2, 3:x2],
            (33, 30),
            interpolation=cv2.INTER_AREA,
        )
        item = (name, f"target:{image_name}:{location}", portrait)
        destination = validation_portraits if image_name == validation_image else train_portraits
        destination.append(item)
    return train_portraits, validation_portraits


def make_locator_mask(annotation: dict, image_name: str) -> np.ndarray:
    width, height = annotation["canonical_size"]
    mask = np.zeros((height, width), dtype=np.uint8)
    card_boxes = annotation["card_boxes"]
    image_annotation = annotation["images"][image_name]
    for card_index in image_annotation["card_indices"]:
        x1, y1, x2, y2 = card_boxes[card_index]
        cv2.rectangle(mask, (x1, y1), (x2 - 1, y2 - 1), 1, thickness=-1)
    geometry = annotation["avatar_geometry"]
    for card_index, avatar_slot, eligible in image_annotation["avatars"]:
        card_x, card_y = card_boxes[card_index][:2]
        x1 = card_x + geometry["relative_x"][avatar_slot]
        y1 = card_y + geometry["relative_y"]
        x2 = x1 + geometry["width"]
        y2 = y1 + geometry["height"]
        cv2.rectangle(mask, (x1, y1), (x2 - 1, y2 - 1), 2 if eligible else 3, thickness=-1)
    return mask


class LocatorDataset(Dataset):
    def __init__(
        self,
        image_size=(320, 180),
        repeats=8,
        included_images: Optional[set[str]] = None,
    ):
        self.annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
        self.items = []
        self.image_names = []
        for image_name in self.annotation["images"]:
            if included_images is not None and image_name not in included_images:
                continue
            image = cv2.imread(str(FIXTURE_DIR / image_name))
            if image is None:
                raise FileNotFoundError(FIXTURE_DIR / image_name)
            self.items.append((image, make_locator_mask(self.annotation, image_name)))
            self.image_names.append(image_name)
        self.image_size = image_size
        self.repeats = repeats

    def __len__(self):
        return len(self.items) * self.repeats

    def __getitem__(self, index):
        image, mask = self.items[index % len(self.items)]
        image = image.copy()
        mask = mask.copy()
        height, width = image.shape[:2]
        scale = random.uniform(0.70, 1.40)
        tx = random.uniform(-0.08, 0.08) * width
        ty = random.uniform(-0.08, 0.08) * height
        transform = np.asarray(
            ((scale, 0, (1 - scale) * width / 2 + tx), (0, scale, (1 - scale) * height / 2 + ty)),
            dtype=np.float32,
        )
        image = cv2.warpAffine(
            image,
            transform,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101,
        )
        mask = cv2.warpAffine(
            mask,
            transform,
            (width, height),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        contrast = random.uniform(0.85, 1.15)
        brightness = random.uniform(-15, 15)
        image = np.clip(image.astype(np.float32) * contrast + brightness, 0, 255).astype(np.uint8)
        target_width, target_height = self.image_size
        image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        mask = cv2.resize(mask, (target_width, target_height), interpolation=cv2.INTER_NEAREST)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return torch.from_numpy(image.transpose(2, 0, 1)), torch.from_numpy(mask.astype(np.int64))


def _student_view(image: np.ndarray, randomize: bool) -> np.ndarray:
    canvas_size = 96
    canvas = np.full((canvas_size, canvas_size, 3), random.randint(205, 235), dtype=np.uint8)
    scale = 3.0 * random.uniform(0.70, 1.40) if randomize else 3.0
    aspect_ratio = random.uniform(0.90, 1.10) if randomize else 1.0
    width = max(16, round(image.shape[1] * scale * aspect_ratio ** 0.5))
    height = max(15, round(image.shape[0] * scale / aspect_ratio ** 0.5))
    interpolation = random.choice((cv2.INTER_AREA, cv2.INTER_LINEAR, cv2.INTER_CUBIC))
    resized = cv2.resize(image, (width, height), interpolation=interpolation)
    x = random.randint(min(0, canvas_size - width), max(0, canvas_size - width)) if randomize else (canvas_size - width) // 2
    y = random.randint(min(0, canvas_size - height), max(0, canvas_size - height)) if randomize else (canvas_size - height) // 2
    source_x1 = max(0, -x)
    source_y1 = max(0, -y)
    target_x1 = max(0, x)
    target_y1 = max(0, y)
    copy_width = min(width - source_x1, canvas_size - target_x1)
    copy_height = min(height - source_y1, canvas_size - target_y1)
    canvas[target_y1:target_y1 + copy_height, target_x1:target_x1 + copy_width] = resized[
        source_y1:source_y1 + copy_height,
        source_x1:source_x1 + copy_width,
    ]
    if randomize and random.random() < 0.25:
        canvas = cv2.GaussianBlur(canvas, (3, 3), 0)
    if randomize:
        if random.random() < 0.30:
            cv2.rectangle(
                canvas,
                (0, 0),
                (canvas_size - 1, canvas_size - 1),
                random.choice(((244, 84, 166), (255, 112, 187), (245, 145, 210))),
                thickness=random.choice((1, 2, 3)),
            )
        if random.random() < 0.30:
            radius = random.randint(7, 12)
            center = (
                random.randint(canvas_size - 18, canvas_size - 9),
                random.randint(canvas_size - 18, canvas_size - 9),
            )
            cv2.circle(canvas, center, radius, (245, 88, 175), thickness=-1)
            cv2.putText(
                canvas,
                str(random.randint(1, 99)),
                (center[0] - radius, center[1] + 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.25,
                (255, 255, 255),
                thickness=1,
                lineType=cv2.LINE_AA,
            )
        if random.random() < 0.20:
            occlusion_width = random.randint(5, 16)
            occlusion_height = random.randint(5, 14)
            occlusion_x = random.randint(0, canvas_size - occlusion_width)
            occlusion_y = random.randint(0, canvas_size - occlusion_height)
            cv2.rectangle(
                canvas,
                (occlusion_x, occlusion_y),
                (occlusion_x + occlusion_width, occlusion_y + occlusion_height),
                (random.randint(180, 235),) * 3,
                thickness=-1,
            )
        if randomize and random.random() < 0.35:
            # Roster portraits contain small class/attack icons in the upper
            # corners. Randomly suppress them so identity cannot hinge on UI.
            corner = random.choice(("left", "right", "both"))
            cover = random.randint(12, 22)
            fill = (random.randint(185, 235),) * 3
            if corner in ("left", "both"):
                cv2.rectangle(canvas, (0, 0), (cover, cover), fill, thickness=-1)
            if corner in ("right", "both"):
                cv2.rectangle(
                    canvas,
                    (canvas_size - cover - 1, 0),
                    (canvas_size - 1, cover),
                    fill,
                    thickness=-1,
                )
        hsv = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= random.uniform(0.80, 1.20)
        hsv[:, :, 2] *= random.uniform(0.90, 1.10)
        canvas = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
        canvas = np.clip(
            canvas.astype(np.float32) * random.uniform(0.85, 1.15) + random.uniform(-12, 12),
            0,
            255,
        ).astype(np.uint8)
        if random.random() < 0.25:
            quality = random.randint(45, 92)
            success, encoded = cv2.imencode(
                ".jpg",
                canvas,
                (cv2.IMWRITE_JPEG_QUALITY, quality),
            )
            if success:
                canvas = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) / 255.0 - MEAN) / STD
    return normalized.transpose(2, 0, 1)


def _runtime_student_views(crop: np.ndarray) -> np.ndarray:
    views = []
    for view in StudentRecognizer._portrait_views(crop):
        letterboxed = StudentRecognizer._letterbox(view, 96, 96)
        rgb = cv2.cvtColor(letterboxed, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 255.0 - MEAN) / STD
        views.append(normalized.transpose(2, 0, 1))
    return np.stack(views).astype(np.float32)


class IdentityBalancedStudentDataset(Dataset):
    """Give every identity exactly the same number of augmented draws."""

    SOURCE_ORDER = ("target:", "roster:", "history:")

    def __init__(
        self,
        templates,
        label_to_index,
        samples_per_identity: int = SAMPLES_PER_IDENTITY,
    ):
        grouped = collections.defaultdict(list)
        for item in templates:
            grouped[item[0]].append(item)
        self.names = sorted(grouped)
        self.templates_by_name = {}
        for name in self.names:
            by_source = collections.defaultdict(list)
            for item in grouped[name]:
                source_kind = item[1].split(":", 1)[0] + ":"
                by_source[source_kind].append(item)
            self.templates_by_name[name] = dict(by_source)
        self.label_to_index = label_to_index
        self.samples_per_identity = samples_per_identity

    def __len__(self):
        return len(self.names) * self.samples_per_identity

    def __getitem__(self, index):
        identity_index, source_slot = divmod(index, self.samples_per_identity)
        name = self.names[identity_index]
        by_source = self.templates_by_name[name]
        preferred = self.SOURCE_ORDER[source_slot % len(self.SOURCE_ORDER)]
        templates = by_source.get(preferred)
        if not templates:
            available = [
                by_source[source]
                for source in self.SOURCE_ORDER
                if by_source.get(source)
            ]
            templates = available[source_slot % len(available)]
        _, _, image = random.choice(templates)
        views = np.stack((_student_view(image, True), _student_view(image, True))).astype(np.float32)
        return torch.from_numpy(views), self.label_to_index[name]


def supervised_contrastive_loss(embeddings, labels, temperature=0.10):
    similarity = embeddings @ embeddings.T / temperature
    identity = torch.eye(len(labels), device=labels.device, dtype=torch.bool)
    positive = labels[:, None].eq(labels[None, :]) & ~identity
    logits = similarity - similarity.max(dim=1, keepdim=True).values.detach()
    exp_logits = torch.exp(logits) * ~identity
    log_probability = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp_min(1e-12))
    positive_count = positive.sum(dim=1).clamp_min(1)
    return -((log_probability * positive).sum(dim=1) / positive_count).mean()


def _fit_locator(
    included_images: set[str],
    epochs: int,
    seed: int,
    label: str,
):
    seed_everything(seed)
    dataset = LocatorDataset(included_images=included_images)
    loader = DataLoader(dataset, batch_size=6, shuffle=True, num_workers=0)
    device = training_device()
    model = LessonSegmentationNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    class_weights = torch.tensor((0.15, 1.0, 4.0, 7.0), device=device)
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = F.cross_entropy(logits, masks, weight=class_weights)
            loss.backward()
            optimizer.step()
            running_loss += float(loss)
        if epoch % 10 == 0 or epoch == epochs - 1:
            print(
                f"locator {label} epoch={epoch:03d} "
                f"loss={running_loss / len(loader):.5f}"
            )
    return model.to("cpu").eval(), dataset


def _write_locator_metadata(directory: Path, dataset: LocatorDataset) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    annotation = dataset.annotation
    (directory / "lesson_locator.json").write_text(
        json.dumps(
            {
                "version": 2,
                "input_width": 320,
                "input_height": 180,
                "classes": ["background", "lesson_card", "eligible_avatar", "plain_avatar"],
                "minimum_cards": 6,
                "plain_avatar_ratio_threshold": 0.50,
                "augmentation_scale_range": [0.70, 1.40],
                "single_frame_no_scroll": True,
                "training_images": sorted(dataset.image_names),
                "training_image_count": len(dataset.items),
                "training_avatar_count": sum(
                    len(annotation["images"][name]["avatars"])
                    for name in dataset.image_names
                ),
                "eligible_avatar_count": sum(
                    eligible
                    for name in dataset.image_names
                    for image in [annotation["images"][name]]
                    for _, _, eligible in image["avatars"]
                ),
                "plain_avatar_count": sum(
                    not eligible
                    for name in dataset.image_names
                    for image in [annotation["images"][name]]
                    for _, _, eligible in image["avatars"]
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _export_locator(model, directory: Path, dataset: LocatorDataset) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros((1, 3, 180, 320), dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy,
        directory / "lesson_locator.onnx",
        input_names=["image"],
        output_names=["segmentation_logits"],
        dynamic_axes={"image": {0: "batch"}, "segmentation_logits": {0: "batch"}},
        opset_version=12,
    )
    _write_locator_metadata(directory, dataset)


def train_locator(
    output_dir: Path,
    epochs: int = 80,
    fold_epochs: int = 35,
    seed: int = SEED,
) -> dict:
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    image_names = sorted(annotation["images"])
    fold_metrics = {}
    for fold_index, validation_image in enumerate(image_names):
        included = set(image_names) - {validation_image}
        model, dataset = _fit_locator(
            included,
            fold_epochs,
            seed + fold_index,
            f"fold:{validation_image}",
        )
        fold_dir = output_dir / "folds" / "locator" / validation_image.removesuffix(".png")
        _export_locator(model, fold_dir, dataset)
        image = cv2.imread(str(FIXTURE_DIR / validation_image))
        locator = LessonLocator(fold_dir)
        cards = locator.locate(image)
        expected = annotation["images"][validation_image]
        fold_metrics[validation_image] = {
            "card_count": len(cards),
            "avatar_count": sum(len(card.avatars) for card in cards),
            "eligible_avatar_count": sum(
                avatar.eligible for card in cards for avatar in card.avatars
            ),
            "expected_card_count": len(expected["card_indices"]),
            "expected_avatar_count": len(expected["avatars"]),
            "expected_eligible_avatar_count": sum(row[2] for row in expected["avatars"]),
            "backend": locator.last_backend,
        }

    model, dataset = _fit_locator(set(image_names), epochs, seed, "final")
    _export_locator(model, output_dir, dataset)
    return fold_metrics


def _train_student_encoder(
    templates,
    epochs: int,
    label: str,
    initial_encoder_state=None,
    seed: int = SEED,
    checkpoint_path: Optional[Path] = None,
):
    seed_everything(seed)
    names = sorted({name for name, _, _ in templates})
    label_to_index = {name: index for index, name in enumerate(names)}
    dataset = IdentityBalancedStudentDataset(templates, label_to_index)
    loader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=0)
    device = training_device()
    model = StudentEncoderTrainer(len(names)).to(device)
    if initial_encoder_state is not None:
        model.encoder.load_state_dict(initial_encoder_state)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    start_epoch = 0
    if checkpoint_path is not None and checkpoint_path.exists():
        checkpoint = torch.load(
            checkpoint_path,
            map_location=device,
            weights_only=True,
        )
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        start_epoch = int(checkpoint["epoch"]) + 1
        print(f"encoder {label} resume_epoch={start_epoch:03d}")
    model.train()
    for epoch in range(start_epoch, epochs):
        running_loss = 0.0
        for views, labels in loader:
            views = views.to(device)
            labels = labels.to(device)
            batch_size = len(labels)
            images = views.reshape(batch_size * 2, 3, 96, 96)
            expanded_labels = labels.repeat_interleave(2)
            optimizer.zero_grad()
            embeddings, logits = model(images)
            classification_loss = F.cross_entropy(logits, expanded_labels)
            contrastive_loss = supervised_contrastive_loss(embeddings, expanded_labels)
            loss = classification_loss + 0.20 * contrastive_loss
            loss.backward()
            optimizer.step()
            running_loss += float(loss)
        if epoch % 5 == 0 or epoch == epochs - 1:
            print(
                f"encoder {label} epoch={epoch:03d} "
                f"loss={running_loss / len(loader):.5f}"
            )
            if checkpoint_path is not None:
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(
                    {
                        "epoch": epoch,
                        "model": model.state_dict(),
                        "optimizer": optimizer.state_dict(),
                    },
                    checkpoint_path,
                )
    return model.encoder.to("cpu").eval(), names


def _select_prototype_templates(templates, catalog):
    grouped = collections.defaultdict(lambda: collections.defaultdict(list))
    for name, source, image in templates:
        record = catalog.resolve(name)
        if record is None:
            continue
        source_kind = source.split(":", 1)[0]
        grouped[record.student_id][source_kind].append((name, source, image))

    selected = []
    for student_id in sorted(catalog.records):
        sources = grouped.get(student_id, {})
        target = sorted(sources.get("target", []), key=lambda item: item[1])
        roster = sorted(sources.get("roster", []), key=lambda item: item[1])
        history = sorted(sources.get("history", []), key=lambda item: item[1])
        choices = []
        if target:
            choices.extend(target[:2])
            choices.extend(roster[:1])
            if len(choices) < 3:
                choices.extend(history[: 3 - len(choices)])
        else:
            choices.extend(roster[:1])
            choices.extend(history[:2])
        selected.extend(choices[:3])
    return selected


def _opencv_embeddings(model_path: Path, inputs: np.ndarray) -> np.ndarray:
    net = cv2.dnn.readNetFromONNX(str(model_path))
    net.setInput(np.asarray(inputs, dtype=np.float32))
    embeddings = np.asarray(net.forward(), dtype=np.float32)
    return embeddings / np.maximum(
        np.linalg.norm(embeddings, axis=1, keepdims=True),
        1e-12,
    )


def _build_gallery(encoder, templates, catalog, model_path: Optional[Path] = None):
    selected = _select_prototype_templates(templates, catalog)
    prototype_inputs = np.stack(
        [
            _runtime_student_views(image)[0]
            if source.startswith("target:")
            else _student_view(image, False)
            for _, source, image in selected
        ]
    ).astype(np.float32)
    if model_path is None:
        with torch.no_grad():
            prototype_embeddings = encoder(
                torch.from_numpy(prototype_inputs)
            ).cpu().numpy().astype(np.float32)
    else:
        prototype_embeddings = _opencv_embeddings(model_path, prototype_inputs)

    prototypes_by_student = collections.defaultdict(list)
    prototype_sources = collections.defaultdict(list)
    for (name, source, _), embedding in zip(selected, prototype_embeddings):
        record = catalog.resolve(name)
        if record is not None:
            prototypes_by_student[record.student_id].append(embedding)
            prototype_sources[record.student_id].append(source)

    gallery_embeddings = []
    gallery_ids = []
    for student_id in sorted(prototypes_by_student):
        for embedding in prototypes_by_student[student_id]:
            gallery_embeddings.append(embedding)
            gallery_ids.append(student_id)
    gallery_matrix = np.asarray(gallery_embeddings, dtype=np.float32)
    gallery_matrix /= np.maximum(
        np.linalg.norm(gallery_matrix, axis=1, keepdims=True),
        1e-12,
    )
    return gallery_matrix, np.asarray(gallery_ids), dict(prototype_sources)


def _rank_embeddings(embeddings, items, gallery_matrix, gallery_ids, catalog):
    embeddings = embeddings.reshape(len(items), -1, embeddings.shape[-1])
    embeddings /= np.maximum(
        np.linalg.norm(embeddings, axis=2, keepdims=True),
        1e-12,
    )
    similarity = np.max(embeddings @ gallery_matrix.T, axis=1)
    known_ids = set(gallery_ids.tolist())
    results = []
    for row, (name, image_name, location, _) in zip(similarity, items):
        expected = catalog.resolve(name)
        per_student = collections.defaultdict(lambda: -1.0)
        for student_id, score in zip(gallery_ids, row):
            per_student[student_id] = max(per_student[student_id], float(score))
        ranked = sorted(per_student.items(), key=lambda item: item[1], reverse=True)
        predicted_id, score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else -1.0
        expected_id = expected.student_id if expected is not None else None
        results.append(
            {
                "image": image_name,
                "location": location,
                "expected_id": expected_id,
                "predicted_id": predicted_id,
                "score": score,
                "margin": score - second_score,
                "expected_known": expected_id in known_ids,
            }
        )
    return results


def _score_with_torch(encoder, items, gallery_matrix, gallery_ids, catalog):
    if not items:
        return []
    inputs = np.concatenate([_runtime_student_views(crop) for _, _, _, crop in items])
    with torch.no_grad():
        embeddings = encoder(torch.from_numpy(inputs)).cpu().numpy().astype(np.float32)
    return _rank_embeddings(embeddings, items, gallery_matrix, gallery_ids, catalog)


def _score_with_opencv(model_path, items, gallery_matrix, gallery_ids, catalog):
    if not items:
        return []
    inputs = np.concatenate([_runtime_student_views(crop) for _, _, _, crop in items])
    net = cv2.dnn.readNetFromONNX(str(model_path))
    net.setInput(inputs)
    embeddings = np.asarray(net.forward(), dtype=np.float32)
    return _rank_embeddings(embeddings, items, gallery_matrix, gallery_ids, catalog)


def _export_encoder(encoder, model_path: Path) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros((1, 3, 96, 96), dtype=torch.float32)
    torch.onnx.export(
        encoder,
        dummy,
        model_path,
        input_names=["student_portrait"],
        output_names=["embedding"],
        dynamic_axes={"student_portrait": {0: "batch"}, "embedding": {0: "batch"}},
        opset_version=12,
    )


def _top1_metrics(results) -> dict:
    count = len(results)
    correct = sum(row["predicted_id"] == row["expected_id"] for row in results)
    identity_scores = collections.defaultdict(list)
    for row in results:
        identity_scores[row["expected_id"]].append(
            row["predicted_id"] == row["expected_id"]
        )
    macro_recall = (
        float(np.mean([np.mean(values) for values in identity_scores.values()]))
        if identity_scores
        else None
    )
    return {
        "count": count,
        "correct": correct,
        "top1_accuracy": correct / count if count else None,
        "macro_recall": macro_recall,
        "minimum_score": min((row["score"] for row in results), default=None),
        "minimum_margin": min((row["margin"] for row in results), default=None),
    }


def _score_portraits_with_opencv(
    model_path: Path,
    portraits,
    gallery_matrix,
    gallery_ids,
    catalog,
):
    if not portraits:
        return []
    inputs = np.stack(
        [_student_view(image, False) for _, _, image in portraits]
    ).astype(np.float32)
    embeddings = _opencv_embeddings(model_path, inputs)
    items = [
        (name, source, "", image)
        for name, source, image in portraits
    ]
    return _rank_embeddings(embeddings, items, gallery_matrix, gallery_ids, catalog)


def _source_support_metadata(
    catalog,
    target_groups,
    historical_ids,
    prototype_sources,
):
    metadata = {}
    for student_id, record in sorted(catalog.records.items()):
        if student_id in target_groups:
            status = "target_fixture"
        elif student_id in historical_ids:
            status = "historical_only"
        elif student_id in prototype_sources:
            status = "roster_only"
        else:
            status = "no_prototype"
        metadata[student_id] = {
            "name": record.canonical_name,
            "status": status,
            "validation_groups": sorted(target_groups.get(student_id, set())),
            "prototype_sources": prototype_sources.get(student_id, []),
        }
    return metadata


def train_encoder(
    output_dir: Path,
    epochs: int = 35,
    pretrain_epochs: int = 105,
    final_epochs: int = 105,
    seed: int = SEED,
) -> dict:
    historical_templates = load_historical_templates()
    roster_templates = load_roster_montage_portraits()
    seed_templates = historical_templates + roster_templates
    labeled_crops = load_labeled_target_crops()
    runtime_labeled_crops = load_runtime_labeled_target_crops(output_dir)
    target_portraits, _ = load_target_domain_portraits()
    target_gallery_templates = [
        (name, f"target:{image_name}:{location}", crop)
        for name, image_name, location, crop in runtime_labeled_crops
    ]
    catalog = StudentCatalog(json.loads(STATIC_DEFAULT_CONFIG)["student_names"])

    historical_ids = {
        record.student_id
        for name, _, _ in historical_templates
        if (record := catalog.resolve(name)) is not None
    }
    target_groups = collections.defaultdict(set)
    for name, image_name, _, _ in labeled_crops:
        record = catalog.resolve(name)
        if record is None:
            raise ValueError(f"Unknown manually labelled student: {name}")
        target_groups[record.student_id].add(image_name)
    target_ids = set(target_groups)
    if len(catalog.records) != 265 or len(target_ids) != 74:
        raise ValueError(
            f"Unexpected catalog/target identity count: {len(catalog.records)}/{len(target_ids)}"
        )

    pretrained_encoder, _ = _train_student_encoder(
        seed_templates,
        pretrain_epochs,
        "seed-pretrain",
        seed=seed,
        checkpoint_path=output_dir / "checkpoints" / "seed-pretrain.pt",
    )
    pretrained_state = {
        name: value.detach().clone()
        for name, value in pretrained_encoder.state_dict().items()
    }

    cross_validation_results = []
    fold_metrics = {}
    image_names = sorted({image_name for _, image_name, _, _ in labeled_crops})
    for fold_index, validation_image in enumerate(image_names):
        target_train, _ = load_target_domain_portraits(validation_image)
        fold_templates = seed_templates + target_train
        fold_gallery_templates = seed_templates + [
            item
            for item in target_gallery_templates
            if not item[1].startswith(f"target:{validation_image}:")
        ]
        fold_encoder, _ = _train_student_encoder(
            fold_templates,
            epochs,
            f"fold:{validation_image}",
            pretrained_state,
            seed=seed + fold_index + 10,
            checkpoint_path=(
                output_dir
                / "checkpoints"
                / f"encoder-fold-{validation_image.removesuffix('.png')}.pt"
            ),
        )
        fold_dir = output_dir / "folds" / "encoder" / validation_image.removesuffix(".png")
        fold_model_path = fold_dir / "student_encoder.onnx"
        _export_encoder(fold_encoder, fold_model_path)
        fold_gallery, fold_ids, _ = _build_gallery(
            fold_encoder,
            fold_gallery_templates,
            catalog,
            fold_model_path,
        )
        validation_items = [
            item for item in runtime_labeled_crops if item[1] == validation_image
        ]
        fold_results = _score_with_opencv(
            fold_model_path,
            validation_items,
            fold_gallery,
            fold_ids,
            catalog,
        )
        cross_validation_results.extend(fold_results)
        fold_metrics[validation_image] = _top1_metrics(fold_results)

    templates = seed_templates + target_portraits
    gallery_templates = seed_templates + target_gallery_templates
    encoder, names = _train_student_encoder(
        templates,
        final_epochs,
        "final",
        pretrained_state,
        seed=seed + 100,
        checkpoint_path=output_dir / "checkpoints" / "encoder-final.pt",
    )
    model_path = output_dir / "student_encoder.onnx"
    _export_encoder(encoder, model_path)
    gallery_embeddings, gallery_ids, prototype_sources = _build_gallery(
        encoder,
        gallery_templates,
        catalog,
        model_path,
    )
    np.savez_compressed(
        output_dir / "gallery.npz",
        embeddings=gallery_embeddings,
        student_ids=gallery_ids,
    )

    final_results = _score_with_opencv(
        model_path,
        labeled_crops,
        gallery_embeddings,
        gallery_ids,
        catalog,
    )
    roster_results = _score_portraits_with_opencv(
        model_path,
        roster_templates,
        gallery_embeddings,
        gallery_ids,
        catalog,
    )
    historical_results = _score_portraits_with_opencv(
        model_path,
        historical_templates,
        gallery_embeddings,
        gallery_ids,
        catalog,
    )

    comparison_inputs = np.stack(
        [_student_view(image, False) for _, _, image in templates[:64]]
    ).astype(np.float32)
    with torch.no_grad():
        torch_embeddings = encoder(torch.from_numpy(comparison_inputs)).numpy()
    opencv_embeddings = _opencv_embeddings(model_path, comparison_inputs)
    cosine_difference = float(
        np.max(np.abs(1.0 - np.sum(torch_embeddings * opencv_embeddings, axis=1)))
    )

    support_metadata = _source_support_metadata(
        catalog,
        target_groups,
        historical_ids,
        prototype_sources,
    )
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    eligible_avatar_count = sum(
        eligible
        for image in annotation["images"].values()
        for _, _, eligible in image["avatars"]
    )
    target_avatar_count = sum(
        len(image["avatars"])
        for image in annotation["images"].values()
    )
    metadata = {
        "version": 2,
        "architecture": "MobileNetV2-0.5",
        "input_width": 96,
        "input_height": 96,
        "embedding_size": 128,
        "mean": MEAN.tolist(),
        "std": STD.tolist(),
        "margin_threshold": 0.0,
        "identity_click_policy": "valid_global_top1",
        "margin_is_click_gate": False,
        "support_status_is_click_gate": False,
        "global_top1_catalog_size": len(catalog.records),
        "training_source": "committed-git-history+committed-roster-montage+user-manual-target-domain",
        "historical_blob_count": len(historical_templates),
        "historical_identity_count": len(historical_ids),
        "roster_montage_portrait_count": len(roster_templates),
        "target_domain_training_count": len(target_portraits),
        "identity_balanced_samples_per_epoch": SAMPLES_PER_IDENTITY,
        "pretraining_epochs": pretrain_epochs,
        "cross_validation_epochs": epochs,
        "final_training_epochs": final_epochs,
        "training_seed": seed,
        "target_avatar_count": target_avatar_count,
        "target_identity_count": len(target_ids),
        "eligible_avatar_count": eligible_avatar_count,
        "plain_avatar_count": target_avatar_count - eligible_avatar_count,
        "augmentation_scale_range": [0.70, 1.40],
        "horizontal_flip": False,
        "student_support": support_metadata,
        "validation_groups": image_names,
        "validation_fold_metrics": fold_metrics,
        "cross_validation_metrics": _top1_metrics(cross_validation_results),
        "all_labeled_target_metrics": _top1_metrics(final_results),
        "roster_replay_metrics": _top1_metrics(roster_results),
        "historical_replay_metrics": _top1_metrics(historical_results),
        "torch_opencv_max_cosine_difference": cosine_difference,
        "label_count": len(names),
        "gallery_identity_count": len(set(gallery_ids.tolist())),
        "gallery_prototype_count": len(gallery_ids),
    }
    (output_dir / "student_encoder.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "metadata": metadata,
        "cross_validation_results": cross_validation_results,
        "manual_target_results": final_results,
        "roster_results": roster_results,
        "historical_results": historical_results,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_names(catalog, student_ids) -> list[str]:
    return sorted(
        catalog.record(student_id).canonical_name
        for student_id in student_ids
        if catalog.record(student_id) is not None
    )


def _evaluate_locator_folds(model_dir: Path) -> dict:
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    metrics = {}
    for image_name, expected in annotation["images"].items():
        fold_dir = model_dir / "folds" / "locator" / image_name.removesuffix(".png")
        locator = LessonLocator(fold_dir)
        image = cv2.imread(str(FIXTURE_DIR / image_name))
        cards = locator.locate(image)
        metrics[image_name] = {
            "card_count": len(cards),
            "avatar_count": sum(len(card.avatars) for card in cards),
            "eligible_avatar_count": sum(
                avatar.eligible for card in cards for avatar in card.avatars
            ),
            "expected_card_count": len(expected["card_indices"]),
            "expected_avatar_count": len(expected["avatars"]),
            "expected_eligible_avatar_count": sum(row[2] for row in expected["avatars"]),
            "backend": locator.last_backend,
        }
    return metrics


def build_validation_report(
    model_dir: Path,
    seed: int,
    locator_fold_metrics: dict,
    encoder_diagnostics: dict,
) -> dict:
    if not locator_fold_metrics:
        locator_fold_metrics = _evaluate_locator_folds(model_dir)
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    student_rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    catalog = StudentCatalog(student_rows)
    historical = load_historical_templates()
    roster = load_roster_montage_portraits()
    historical_ids = {
        catalog.resolve(name).student_id for name, _, _ in historical
    }
    target_groups = collections.defaultdict(set)
    target_eligibility = collections.defaultdict(list)
    for image_name, image_annotation in annotation["images"].items():
        flags = {
            f"{card}:{slot}": eligible
            for card, slot, eligible in image_annotation["avatars"]
        }
        for location, name in image_annotation["identity_labels"].items():
            student_id = catalog.resolve(name).student_id
            target_groups[student_id].add(image_name)
            target_eligibility[student_id].append(flags[location])
    target_ids = set(target_groups)
    roster_ids = {
        catalog.resolve(name).student_id for name, _, _ in roster
    }

    service = StudentRecognitionService(student_rows, model_dir)
    locator_scale_results = []
    locator_failures = []
    for image_name, expected in annotation["images"].items():
        original = cv2.imread(str(FIXTURE_DIR / image_name))
        for scale in (0.70, 0.85, 1.00, 1.15, 1.40):
            resized = cv2.resize(
                original,
                (round(original.shape[1] * scale), round(original.shape[0] * scale)),
                interpolation=cv2.INTER_LINEAR,
            )
            cards = service.lesson_locator.locate(resized)
            actual = {
                f"{card.index}:{slot}": avatar.eligible
                for card in cards
                for slot, avatar in enumerate(card.avatars)
            }
            expected_flags = {
                f"{card}:{slot}": eligible
                for card, slot, eligible in expected["avatars"]
            }
            click_points_safe = all(
                card.bbox.contains(card.click_point) for card in cards
            )
            passed = (
                service.lesson_locator.last_backend == "onnx"
                and [card.index for card in cards] == expected["card_indices"]
                and actual == expected_flags
                and click_points_safe
            )
            row = {
                "image": image_name,
                "scale": scale,
                "backend": service.lesson_locator.last_backend,
                "card_count": len(cards),
                "avatar_count": len(actual),
                "eligible_avatar_count": sum(actual.values()),
                "click_points_safe": click_points_safe,
                "passed": passed,
            }
            locator_scale_results.append(row)
            if not passed:
                locator_failures.append(row)

    instances = []
    click_passed_instances = []
    gray_blocked_instances = []
    top1_failures = []
    invalid_prediction_failures = []
    click_failures = []
    wrong_card_clicks = []
    gray_wrong_clicks = []
    gray_identity_failures = []
    for image_name, expected in annotation["images"].items():
        image = cv2.imread(str(FIXTURE_DIR / image_name))
        cards = service.recognize_lesson(image, "CN")
        card_map = {card.index: card for card in cards}
        statuses = ["available"] * 9
        expected_flags = {
            f"{card}:{slot}": eligible
            for card, slot, eligible in expected["avatars"]
        }
        for location, expected_name in expected["identity_labels"].items():
            card_index, slot = (int(value) for value in location.split(":"))
            avatar = card_map[card_index].avatars[slot]
            prediction = avatar.prediction
            eligible = expected_flags[location]
            selected = service.select_priority_card(cards, statuses, [expected_name])
            selected_index = selected.index if selected is not None else None
            row = {
                "image": image_name,
                "card": card_index,
                "slot": slot,
                "location": location,
                "student": expected_name,
                "expected_eligible": eligible,
                "located_eligible": avatar.eligible,
                "top1": prediction.name if prediction else None,
                "score": prediction.score if prediction else 0.0,
                "margin": prediction.margin if prediction else 0.0,
                "accepted": prediction.accepted if prediction else False,
                "support_status": prediction.support_status if prediction else "no_prototype",
                "selected_card": selected_index,
                "expected_card": card_index if eligible else None,
                "click_point": list(card_map[card_index].click_point),
            }
            instances.append(row)
            if prediction is None or prediction.name != expected_name:
                top1_failures.append(row)
                if not eligible:
                    gray_identity_failures.append(row)
            if prediction is None or not prediction.accepted:
                invalid_prediction_failures.append(row)
            if eligible:
                if selected_index == card_index:
                    click_passed_instances.append(row)
                else:
                    click_failures.append(row)
                    if selected_index is not None:
                        wrong_card_clicks.append(row)
            else:
                if selected_index is None:
                    gray_blocked_instances.append(row)
                else:
                    gray_wrong_clicks.append(row)

    click_passed_students = sorted({row["student"] for row in click_passed_instances})
    gray_blocked_students = sorted({row["student"] for row in gray_blocked_instances})
    expected_click_students = _canonical_names(
        catalog,
        {
            student_id
            for student_id, flags in target_eligibility.items()
            if any(flags)
        },
    )
    gray_only_ids = {
        student_id
        for student_id, flags in target_eligibility.items()
        if flags and not any(flags)
    }
    gray_only_students = _canonical_names(catalog, gray_only_ids)

    gallery = np.load(str(model_dir / "gallery.npz"), allow_pickle=False)
    gallery_ids = np.asarray(gallery["student_ids"]).astype(str)
    gallery_unique_ids = set(gallery_ids.tolist())

    benchmark_image = cv2.imread(str(FIXTURE_DIR / "new_ui_5.png"))
    for _ in range(5):
        service.recognize_lesson(benchmark_image, "CN")
    timings = []
    for _ in range(30):
        started = time.perf_counter()
        service.recognize_lesson(benchmark_image, "CN")
        timings.append((time.perf_counter() - started) * 1000.0)
    performance = {
        "warmup_runs": 5,
        "measured_runs": 30,
        "mean_ms": statistics.mean(timings),
        "p95_ms": float(np.percentile(timings, 95)),
        "max_ms": max(timings),
    }

    model_files = [
        model_dir / name
        for name in (
            "lesson_locator.onnx",
            "lesson_locator.json",
            "student_encoder.onnx",
            "student_encoder.json",
            "gallery.npz",
        )
    ]
    resources = {
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in model_files
        },
        "total_bytes": sum(path.stat().st_size for path in model_files),
        "limit_bytes": 25 * 1024 * 1024,
    }
    encoder_metadata = encoder_diagnostics["metadata"]
    hard_failures = []
    conditions = {
        "catalog_265": len(catalog.records) == 265,
        "history_177_122": len(historical) == 177 and len(historical_ids) == 122,
        "roster_265": len(roster) == 265 and len(roster_ids) == 265,
        "target_81_74": len(instances) == 81 and len(target_ids) == 74,
        "eligibility_71_10": (
            sum(row["expected_eligible"] for row in instances) == 71
            and sum(not row["expected_eligible"] for row in instances) == 10
        ),
        "gallery_265": len(gallery_unique_ids) == 265,
        "opencv_4_8_1": cv2.__version__ == "4.8.1",
        "runtime_models_load": (
            service.lesson_locator.model_available and service.identity_available
        ),
        "locator_all_scales": not locator_failures,
        "annotated_target_top1_81": (
            encoder_metadata["all_labeled_target_metrics"]["count"] == 81
            and encoder_metadata["all_labeled_target_metrics"]["correct"] == 81
        ),
        "target_top1_81": not top1_failures and len(instances) == 81,
        "target_predictions_valid": not invalid_prediction_failures,
        "pink_clicks_71": (
            not click_failures
            and not wrong_card_clicks
            and len(click_passed_instances) == 71
            and len(click_passed_students) == 65
            and sum(
                row["image"] in {"new_ui_1.png", "new_ui_2.png", "new_ui_3.png"}
                for row in click_passed_instances
            ) == 42
            and sum(
                row["image"] in {"new_ui_4.png", "new_ui_5.png"}
                for row in click_passed_instances
            ) == 29
        ),
        "gray_blocked_10": (
            not gray_identity_failures
            and not gray_wrong_clicks
            and len(gray_blocked_instances) == 10
            and len(gray_blocked_students) == 9
        ),
        "roster_replay_265": (
            encoder_metadata["roster_replay_metrics"]["correct"] == 265
        ),
        "torch_opencv_match": (
            encoder_metadata["torch_opencv_max_cosine_difference"] <= 1e-4
        ),
        "cpu_p95_under_500ms": performance["p95_ms"] <= 500.0,
        "resources_under_25mb": resources["total_bytes"] <= resources["limit_bytes"],
    }
    hard_failures.extend(name for name, passed in conditions.items() if not passed)

    historical_only_ids = historical_ids - target_ids
    roster_only_ids = roster_ids - target_ids - historical_ids
    no_prototype_ids = set(catalog.records) - gallery_unique_ids
    runtime_top1_correct = sum(row["student"] == row["top1"] for row in instances)
    runtime_replay = {
        "count": len(instances),
        "correct": runtime_top1_correct,
        "top1_accuracy": runtime_top1_correct / len(instances),
        "minimum_score": min(row["score"] for row in instances),
        "minimum_margin": min(row["margin"] for row in instances),
    }
    click_coverage = {
        "passed_instances": len(click_passed_instances),
        "passed_students": len(click_passed_students),
        "first_three_images_passed_instances": sum(
            row["image"] in {"new_ui_1.png", "new_ui_2.png", "new_ui_3.png"}
            for row in click_passed_instances
        ),
        "last_two_images_passed_instances": sum(
            row["image"] in {"new_ui_4.png", "new_ui_5.png"}
            for row in click_passed_instances
        ),
        "gray_blocked_instances": len(gray_blocked_instances),
        "gray_wrong_clicks": len(gray_wrong_clicks),
    }
    report = {
        "version": 2,
        "completed": not hard_failures,
        "hard_acceptance": conditions,
        "hard_failures": hard_failures,
        "environment": {
            "seed": seed,
            "opencv_version": cv2.__version__,
            "torch_version": torch.__version__,
            "device": str(training_device()),
            "cuda_device": (
                torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
            ),
            "onnx_opset": 12,
        },
        "data_counts": {
            "catalog_students": len(catalog.records),
            "historical_portraits": len(historical),
            "historical_identities": len(historical_ids),
            "roster_portraits": len(roster),
            "lesson_instances": len(instances),
            "lesson_identities": len(target_ids),
            "eligible_instances": sum(row["expected_eligible"] for row in instances),
            "plain_instances": sum(not row["expected_eligible"] for row in instances),
        },
        "training_replay": {
            "lesson_annotated_crops": encoder_metadata["all_labeled_target_metrics"],
            "roster_portraits": encoder_metadata["roster_replay_metrics"],
            "historical_portraits": encoder_metadata["historical_replay_metrics"],
        },
        "end_to_end_replay": {
            "lesson_runtime_crops": runtime_replay,
            "click_coverage": click_coverage,
        },
        "grouped_cross_validation": {
            "encoder": encoder_metadata["validation_fold_metrics"],
            "encoder_overall": encoder_metadata["cross_validation_metrics"],
            "locator": locator_fold_metrics,
            "is_independent_external_validation": False,
            "note": "Each lesson screenshot is held out as a group, while roster/history seed art remains available.",
        },
        "locator_scale_results": locator_scale_results,
        "performance": performance,
        "resources": resources,
        "click_passed_students": click_passed_students,
        "expected_click_students": expected_click_students,
        "click_passed_instances": click_passed_instances,
        "gray_blocked_students": gray_blocked_students,
        "gray_only_students": gray_only_students,
        "gray_blocked_instances": gray_blocked_instances,
        "target_fixture_students": _canonical_names(catalog, target_ids),
        "historical_only_no_fixture": _canonical_names(catalog, historical_only_ids),
        "roster_only_no_fixture": _canonical_names(catalog, roster_only_ids),
        "no_prototype_students": _canonical_names(catalog, no_prototype_ids),
        "top1_failures": top1_failures,
        "invalid_prediction_failures": invalid_prediction_failures,
        "click_failures": click_failures,
        "wrong_card_clicks": wrong_card_clicks,
        "gray_identity_failures": gray_identity_failures,
        "gray_wrong_clicks": gray_wrong_clicks,
        "locator_failures": locator_failures,
        "disclosures": [
            "81/81 lesson and 265/265 roster checks are training-data replay, not independent external validation.",
            "The 65 click-passed students are coverage from the five checked-in lesson screenshots only.",
            "Grouped folds exclude one lesson screenshot and its augmentations, but retain roster/history seed art.",
            "No emulator was connected and no lesson ticket was consumed.",
        ],
    }
    return report


def _promote_candidate(model_dir: Path, report: dict) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        "lesson_locator.onnx",
        "lesson_locator.json",
        "student_encoder.onnx",
        "student_encoder.json",
        "gallery.npz",
    ):
        temporary = MODEL_DIR / f"{name}.new"
        shutil.copy2(model_dir / name, temporary)
        temporary.replace(MODEL_DIR / name)
    temporary_report = REPORT_PATH.with_suffix(".json.new")
    temporary_report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_report.replace(REPORT_PATH)


def _run_seed(args, seed: int, final_epochs: int, suffix: str = "") -> tuple[Path, dict]:
    directory_name = f"seed-{seed}" + (f"-{suffix}" if suffix else "")
    output_dir = Path(args.output_dir) if args.output_dir else RUNS_DIR / directory_name
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    locator_fold_metrics = train_locator(
        output_dir,
        epochs=args.locator_epochs,
        fold_epochs=args.locator_fold_epochs,
        seed=seed,
    )
    encoder_diagnostics = train_encoder(
        output_dir,
        epochs=args.encoder_epochs,
        pretrain_epochs=args.pretrain_epochs,
        final_epochs=final_epochs,
        seed=seed,
    )
    report = build_validation_report(
        output_dir,
        seed,
        locator_fold_metrics,
        encoder_diagnostics,
    )
    (output_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"seed={seed} completed={report['completed']} "
        f"hard_failures={report['hard_failures']}"
    )
    return output_dir, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("locator", "encoder", "validate", "all"))
    parser.add_argument("--locator-epochs", type=int, default=80)
    parser.add_argument("--locator-fold-epochs", type=int, default=35)
    parser.add_argument("--encoder-epochs", type=int, default=35)
    parser.add_argument("--pretrain-epochs", type=int, default=105)
    parser.add_argument("--final-epochs", type=int, default=105)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[20260731, 20260801, 20260802],
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--no-promote", action="store_true")
    args = parser.parse_args()

    if args.target != "all":
        output_dir = args.output_dir or RUNS_DIR / f"seed-{args.seeds[0]}"
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.target == "locator":
            train_locator(
                output_dir,
                args.locator_epochs,
                args.locator_fold_epochs,
                args.seeds[0],
            )
        elif args.target == "encoder":
            train_encoder(
                output_dir,
                args.encoder_epochs,
                args.pretrain_epochs,
                args.final_epochs,
                args.seeds[0],
            )
        else:
            metadata = json.loads(
                (output_dir / "student_encoder.json").read_text(encoding="utf-8")
            )
            report = build_validation_report(
                output_dir,
                args.seeds[0],
                {},
                {"metadata": metadata},
            )
            (output_dir / "validation_report.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            if report["completed"] and not args.no_promote:
                _promote_candidate(output_dir, report)
            if not report["completed"]:
                raise RuntimeError(
                    "Candidate failed hard acceptance: "
                    + ", ".join(report["hard_failures"])
                )
        return

    attempts = []
    for seed in args.seeds:
        output_dir, report = _run_seed(args, seed, args.final_epochs)
        attempts.append((output_dir, report))
        if report["completed"]:
            if not args.no_promote:
                _promote_candidate(output_dir, report)
            return

    best_directory, best_report = max(
        attempts,
        key=lambda item: (
            item[1]["grouped_cross_validation"]["encoder_overall"]["macro_recall"] or 0.0,
            item[1]["grouped_cross_validation"]["encoder_overall"]["top1_accuracy"] or 0.0,
            -item[1]["performance"]["p95_ms"],
        ),
    )
    extended_seed = best_report["environment"]["seed"]
    extended_dir, extended_report = _run_seed(
        args,
        extended_seed,
        175,
        suffix="extended",
    )
    if extended_report["completed"] and not args.no_promote:
        _promote_candidate(extended_dir, extended_report)
        return
    raise RuntimeError(
        "No candidate passed hard acceptance: "
        + ", ".join(extended_report["hard_failures"])
    )


if __name__ == "__main__":
    main()
