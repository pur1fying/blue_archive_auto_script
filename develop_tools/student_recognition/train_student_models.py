"""Train and export the lightweight lesson/student models.

Run from the repository root with the development-only requirements installed:

    python develop_tools/student_recognition/train_student_models.py all
"""

import argparse
import collections
import json
import os
import random
import subprocess
import sys
from pathlib import Path

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
from core.student_recognition.recognizer import StudentRecognizer
from develop_tools.student_recognition.models import (
    LessonSegmentationNet,
    StudentEncoderTrainer,
)


FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
ANNOTATION_PATH = Path(__file__).with_name("lesson_locator_annotations.json")
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
SEED = 20260731

HISTORICAL_SOURCES = (
    ("CN", "870ddc335^"),
    ("JP", "d36428149^"),
    ("Global_en-us", "683039fce^"),
)
TARGET_VALIDATION_IMAGE = "new_ui_2.png"

MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


def seed_everything() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)


def load_historical_templates() -> list[tuple[str, str, np.ndarray]]:
    templates = []
    seen_blobs = set()
    for server, revision in HISTORICAL_SOURCES:
        root = f"src/images/{server}/lesson_affection"
        output = subprocess.check_output(
            ["git", "ls-tree", "-r", revision, "--", root],
            cwd=ROOT,
        )
        for line in output.splitlines():
            metadata, path = line.split(b"\t", 1)
            blob_hash = metadata.split()[2].decode()
            if blob_hash in seen_blobs:
                continue
            seen_blobs.add(blob_hash)
            name = os.path.splitext(os.path.basename(path.decode()))[0]
            raw = subprocess.check_output(
                ["git", "cat-file", "blob", blob_hash],
                cwd=ROOT,
            )
            image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if image is not None:
                templates.append((name, blob_hash, image))
    return templates


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


def load_target_domain_portraits() -> tuple[
    list[tuple[str, str, np.ndarray]],
    list[tuple[str, str, np.ndarray]],
]:
    """Load cross-checked identities while keeping one screenshot as a group.

    Returning portraits in the historical 33x30 representation lets the same
    augmentation pipeline cover both sources without leaking augmented copies
    of the validation screenshot into training.
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
        destination = validation_portraits if image_name == TARGET_VALIDATION_IMAGE else train_portraits
        destination.append(item)
    return train_portraits, validation_portraits


def make_locator_mask(annotation: dict, image_name: str) -> np.ndarray:
    width, height = annotation["canonical_size"]
    mask = np.zeros((height, width), dtype=np.uint8)
    card_boxes = annotation["card_boxes"]
    for x1, y1, x2, y2 in card_boxes:
        cv2.rectangle(mask, (x1, y1), (x2 - 1, y2 - 1), 1, thickness=-1)
    geometry = annotation["avatar_geometry"]
    for card_index, avatar_slot, eligible in annotation["images"][image_name]["avatars"]:
        card_x, card_y = card_boxes[card_index][:2]
        x1 = card_x + geometry["relative_x"][avatar_slot]
        y1 = card_y + geometry["relative_y"]
        x2 = x1 + geometry["width"]
        y2 = y1 + geometry["height"]
        cv2.rectangle(mask, (x1, y1), (x2 - 1, y2 - 1), 2 if eligible else 3, thickness=-1)
    return mask


class LocatorDataset(Dataset):
    def __init__(self, image_size=(320, 180), repeats=8):
        self.annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
        self.items = []
        for image_name in self.annotation["images"]:
            image = cv2.imread(str(FIXTURE_DIR / image_name))
            if image is None:
                raise FileNotFoundError(FIXTURE_DIR / image_name)
            self.items.append((image, make_locator_mask(self.annotation, image_name)))
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


class HistoricalStudentDataset(Dataset):
    def __init__(self, templates, label_to_index):
        self.templates = templates
        self.label_to_index = label_to_index

    def __len__(self):
        return len(self.templates)

    def __getitem__(self, index):
        name, _, image = self.templates[index]
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


def train_locator(epochs: int = 80) -> None:
    dataset = LocatorDataset()
    loader = DataLoader(dataset, batch_size=6, shuffle=True, num_workers=0)
    model = LessonSegmentationNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    class_weights = torch.tensor((0.15, 1.0, 4.0, 7.0))
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for images, masks in loader:
            optimizer.zero_grad()
            logits = model(images)
            loss = F.cross_entropy(logits, masks, weight=class_weights)
            loss.backward()
            optimizer.step()
            running_loss += float(loss)
        if epoch % 10 == 0 or epoch == epochs - 1:
            print(f"locator epoch={epoch:03d} loss={running_loss / len(loader):.5f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.eval()
    dummy = torch.zeros((1, 3, 180, 320), dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy,
        MODEL_DIR / "lesson_locator.onnx",
        input_names=["image"],
        output_names=["segmentation_logits"],
        dynamic_axes={"image": {0: "batch"}, "segmentation_logits": {0: "batch"}},
        opset_version=12,
    )
    (MODEL_DIR / "lesson_locator.json").write_text(
        json.dumps(
            {
                "version": 1,
                "input_width": 320,
                "input_height": 180,
                "classes": ["background", "lesson_card", "eligible_avatar", "plain_avatar"],
                "minimum_cards": 6,
                "augmentation_scale_range": [0.70, 1.40],
                "single_frame_no_scroll": True,
                "training_images": sorted(dataset.annotation["images"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def train_encoder(epochs: int = 35) -> None:
    historical_templates = load_historical_templates()
    target_train, target_validation = load_target_domain_portraits()
    templates = historical_templates + target_train
    names = sorted({name for name, _, _ in templates})
    label_to_index = {name: index for index, name in enumerate(names)}
    dataset = HistoricalStudentDataset(templates, label_to_index)
    loader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=0)
    model = StudentEncoderTrainer(len(names))
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for views, labels in loader:
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
            print(f"encoder epoch={epoch:03d} loss={running_loss / len(loader):.5f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    encoder = model.encoder.eval()
    dummy = torch.zeros((1, 3, 96, 96), dtype=torch.float32)
    torch.onnx.export(
        encoder,
        dummy,
        MODEL_DIR / "student_encoder.onnx",
        input_names=["student_portrait"],
        output_names=["embedding"],
        dynamic_axes={"student_portrait": {0: "batch"}, "embedding": {0: "batch"}},
        opset_version=12,
    )

    with torch.no_grad():
        prototype_inputs = torch.from_numpy(
            np.stack([_student_view(image, False) for _, _, image in templates]).astype(np.float32)
        )
        prototype_embeddings = encoder(prototype_inputs).cpu().numpy().astype(np.float32)

    with (ROOT / "config" / "static.json").open("r", encoding="utf-8") as file:
        catalog = StudentCatalog(json.load(file)["student_names"])
    prototypes_by_student = collections.defaultdict(list)
    prototype_items = list(zip(templates, prototype_embeddings))
    prototype_items.sort(key=lambda item: not item[0][1].startswith("target:"))
    for (name, _, _), embedding in prototype_items:
        record = catalog.resolve(name)
        if record is not None and len(prototypes_by_student[record.student_id]) < 3:
            prototypes_by_student[record.student_id].append(embedding)
    gallery_embeddings = []
    gallery_ids = []
    for student_id in sorted(prototypes_by_student):
        for embedding in prototypes_by_student[student_id]:
            gallery_embeddings.append(embedding)
            gallery_ids.append(student_id)
    np.savez_compressed(
        MODEL_DIR / "gallery.npz",
        embeddings=np.asarray(gallery_embeddings, dtype=np.float32),
        student_ids=np.asarray(gallery_ids),
    )
    verified_student_ids = sorted(
        {
            record.student_id
            for name, _, _ in target_train
            if (record := catalog.resolve(name)) is not None
        }
    )
    gallery_matrix = np.asarray(gallery_embeddings, dtype=np.float32)
    gallery_matrix /= np.maximum(np.linalg.norm(gallery_matrix, axis=1, keepdims=True), 1e-12)
    labeled_crops = load_labeled_target_crops()

    opencv_encoder = cv2.dnn.readNetFromONNX(str(MODEL_DIR / "student_encoder.onnx"))
    cn_mask = np.asarray(
        [student_id in catalog.implemented_ids("CN") for student_id in gallery_ids],
        dtype=bool,
    )
    evaluation_gallery = gallery_matrix[cn_mask]
    evaluation_ids = np.asarray(gallery_ids)[cn_mask]

    def evaluate(items):
        metrics = {
            "count": len(items),
            "top1_accuracy": None,
            "accepted_count": 0,
            "accepted_precision": None,
            "accepted_recall": None,
        }
        if not items:
            return metrics
        inputs = np.concatenate(
            [_runtime_student_views(crop) for _, _, _, crop in items]
        )
        opencv_encoder.setInput(inputs)
        embeddings = np.asarray(opencv_encoder.forward(), dtype=np.float32)
        embeddings = embeddings.reshape(len(items), -1, embeddings.shape[-1])
        embeddings /= np.maximum(
            np.linalg.norm(embeddings, axis=2, keepdims=True),
            1e-12,
        )
        similarity = np.max(embeddings @ evaluation_gallery.T, axis=1)
        top1_correct = 0
        accepted_correct = 0
        accepted_count = 0
        for row, (name, _, _, _) in zip(similarity, items):
            expected = catalog.resolve(name)
            per_student = collections.defaultdict(lambda: -1.0)
            for student_id, score in zip(evaluation_ids, row):
                per_student[student_id] = max(per_student[student_id], float(score))
            ranked = sorted(per_student.items(), key=lambda item: item[1], reverse=True)
            predicted_id, score = ranked[0]
            margin = score - ranked[1][1]
            correct = expected is not None and predicted_id == expected.student_id
            top1_correct += int(correct)
            accepted = (
                predicted_id in verified_student_ids
                and score >= 0.94
                and margin >= 0.10
            )
            accepted_count += int(accepted)
            accepted_correct += int(accepted and correct)
        metrics.update(
            top1_accuracy=top1_correct / len(items),
            accepted_count=accepted_count,
            accepted_precision=accepted_correct / accepted_count if accepted_count else None,
            accepted_recall=accepted_correct / len(items),
        )
        return metrics

    validation_metrics = evaluate(
        [item for item in labeled_crops if item[1] == TARGET_VALIDATION_IMAGE]
    )
    target_metrics = evaluate(labeled_crops)
    print("target validation:", validation_metrics)
    print("all labeled target data:", target_metrics)
    (MODEL_DIR / "student_encoder.json").write_text(
        json.dumps(
            {
                "version": 1,
                "architecture": "MobileNetV2-0.5",
                "input_width": 96,
                "input_height": 96,
                "embedding_size": 128,
                "mean": MEAN.tolist(),
                "std": STD.tolist(),
                "similarity_threshold": 0.94,
                "margin_threshold": 0.10,
                "training_source": "deduplicated-git-history+crosschecked-target-domain",
                "historical_blob_count": len(historical_templates),
                "target_domain_training_count": len(target_train),
                "augmentation_scale_range": [0.70, 1.40],
                "horizontal_flip": False,
                "verified_student_ids": verified_student_ids,
                "validation_group": TARGET_VALIDATION_IMAGE,
                "validation_metrics": validation_metrics,
                "all_labeled_target_metrics": target_metrics,
                "label_count": len(names),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("locator", "encoder", "all"))
    parser.add_argument("--locator-epochs", type=int, default=80)
    parser.add_argument("--encoder-epochs", type=int, default=35)
    args = parser.parse_args()
    seed_everything()
    if args.target in ("locator", "all"):
        train_locator(args.locator_epochs)
    if args.target in ("encoder", "all"):
        train_encoder(args.encoder_epochs)


if __name__ == "__main__":
    main()
