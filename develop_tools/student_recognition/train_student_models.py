"""Train and export the lightweight lesson/student models.

Run from the repository root with the development-only requirements installed:

    python develop_tools/student_recognition/train_student_models.py all
"""

import argparse
import collections
import json
import random
import sys
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
SEED = 20260731

MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


def seed_everything() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)


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


def load_runtime_labeled_target_crops() -> list[tuple[str, str, str, np.ndarray]]:
    """Pair manual identities with the crops produced by the runtime locator."""
    annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    locator = LessonLocator()
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
    seed_everything()
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
                "plain_avatar_ratio_threshold": 0.50,
                "augmentation_scale_range": [0.70, 1.40],
                "single_frame_no_scroll": True,
                "training_images": sorted(dataset.annotation["images"]),
                "training_image_count": len(dataset.annotation["images"]),
                "training_avatar_count": sum(
                    len(image["avatars"])
                    for image in dataset.annotation["images"].values()
                ),
                "eligible_avatar_count": sum(
                    eligible
                    for image in dataset.annotation["images"].values()
                    for _, _, eligible in image["avatars"]
                ),
                "plain_avatar_count": sum(
                    not eligible
                    for image in dataset.annotation["images"].values()
                    for _, _, eligible in image["avatars"]
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _train_student_encoder(
    templates,
    epochs: int,
    label: str,
    initial_encoder_state=None,
):
    seed_everything()
    names = sorted({name for name, _, _ in templates})
    label_to_index = {name: index for index, name in enumerate(names)}
    dataset = HistoricalStudentDataset(templates, label_to_index)
    loader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=0)
    model = StudentEncoderTrainer(len(names))
    if initial_encoder_state is not None:
        model.encoder.load_state_dict(initial_encoder_state)
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
            print(
                f"encoder {label} epoch={epoch:03d} "
                f"loss={running_loss / len(loader):.5f}"
            )
    return model.encoder.eval(), names


def _build_gallery(encoder, templates, catalog):
    with torch.no_grad():
        prototype_inputs = torch.from_numpy(
            np.stack(
                [_student_view(image, False) for _, _, image in templates]
            ).astype(np.float32)
        )
        prototype_embeddings = encoder(prototype_inputs).cpu().numpy().astype(np.float32)

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
    gallery_matrix = np.asarray(gallery_embeddings, dtype=np.float32)
    gallery_matrix /= np.maximum(
        np.linalg.norm(gallery_matrix, axis=1, keepdims=True),
        1e-12,
    )
    return gallery_matrix, np.asarray(gallery_ids)


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


def _accepted_metrics(results, verified_ids, similarity_threshold, margin_threshold):
    accepted = [
        result
        for result in results
        if result["predicted_id"] in verified_ids
        and result["score"] >= similarity_threshold
        and result["margin"] >= margin_threshold
    ]
    accepted_correct = sum(
        result["predicted_id"] == result["expected_id"] for result in accepted
    )
    top1_correct = sum(
        result["predicted_id"] == result["expected_id"] for result in results
    )
    unknown = [result for result in results if not result["expected_known"]]
    unknown_accepted = sum(result in accepted for result in unknown)
    return {
        "count": len(results),
        "top1_accuracy": top1_correct / len(results) if results else None,
        "accepted_count": len(accepted),
        "accepted_precision": accepted_correct / len(accepted) if accepted else None,
        "accepted_recall": accepted_correct / len(results) if results else None,
        "unknown_count": len(unknown),
        "unknown_false_accept_rate": (
            unknown_accepted / len(unknown) if unknown else 0.0
        ),
    }


def _calibrate_verification(results, candidate_ids):
    score_thresholds = [value / 100 for value in range(60, 100)]
    margin_thresholds = [value / 100 for value in range(1, 31)]
    best = None
    for similarity_threshold in score_thresholds:
        for margin_threshold in margin_thresholds:
            verified_ids = set()
            for student_id in candidate_ids:
                samples = [
                    result
                    for result in results
                    if result["expected_known"]
                    and result["expected_id"] == student_id
                ]
                if samples and all(
                    result["predicted_id"] == student_id
                    and result["score"] >= similarity_threshold
                    and result["margin"] >= margin_threshold
                    for result in samples
                ):
                    verified_ids.add(student_id)
            if not verified_ids:
                continue
            metrics = _accepted_metrics(
                results,
                verified_ids,
                similarity_threshold,
                margin_threshold,
            )
            if metrics["accepted_precision"] != 1.0:
                continue
            if metrics["unknown_false_accept_rate"] > 0.005:
                continue
            objective = (
                len(verified_ids),
                metrics["accepted_count"],
                similarity_threshold + margin_threshold,
            )
            if best is None or objective > best[0]:
                best = (
                    objective,
                    similarity_threshold,
                    margin_threshold,
                    verified_ids,
                    metrics,
                )
    if best is None:
        return 1.0, 1.0, set(), _accepted_metrics(results, set(), 1.0, 1.0)
    return best[1], best[2], best[3], best[4]


def _filter_final_verified(
    verified_ids,
    results,
    similarity_threshold,
    margin_threshold,
):
    verified_ids = set(verified_ids)
    while True:
        rejected = set()
        for student_id in verified_ids:
            own_samples = [
                result for result in results if result["expected_id"] == student_id
            ]
            if not own_samples or not all(
                result["predicted_id"] == student_id
                and result["score"] >= similarity_threshold
                and result["margin"] >= margin_threshold
                for result in own_samples
            ):
                rejected.add(student_id)
        for result in results:
            if (
                result["predicted_id"] in verified_ids
                and result["score"] >= similarity_threshold
                and result["margin"] >= margin_threshold
                and result["predicted_id"] != result["expected_id"]
            ):
                rejected.add(result["predicted_id"])
        if not rejected:
            return verified_ids
        verified_ids -= rejected


def _student_support_metadata(
    target_groups,
    prototype_only_ids,
    verified_ids,
    cross_validation_results,
    final_results,
    similarity_threshold,
    margin_threshold,
):
    metadata = {}
    verified_ids = set(verified_ids)
    prototype_only_ids = set(prototype_only_ids)
    for student_id in sorted(target_groups):
        if student_id in prototype_only_ids:
            status = "prototype_only"
            reasons = ["single_target_group_without_historical_seed"]
        elif student_id in verified_ids:
            status = "verified"
            reasons = ["passed_grouped_and_final_validation"]
        else:
            status = "verification_failed"
            reasons = []
            for prefix, results in (
                ("grouped", cross_validation_results),
                ("final", final_results),
            ):
                samples = [
                    result
                    for result in results
                    if result["expected_id"] == student_id
                ]
                if not samples:
                    reasons.append(f"{prefix}_sample_missing")
                    continue
                if any(result["predicted_id"] != student_id for result in samples):
                    reasons.append(f"{prefix}_top1_mismatch")
                if any(result["score"] < similarity_threshold for result in samples):
                    reasons.append(f"{prefix}_below_similarity_threshold")
                if any(result["margin"] < margin_threshold for result in samples):
                    reasons.append(f"{prefix}_below_margin_threshold")
            if not reasons:
                reasons.append("removed_by_false_accept_safety_filter")
        metadata[student_id] = {
            "status": status,
            "validation_groups": sorted(target_groups[student_id]),
            "reasons": reasons,
        }
    return metadata


def train_encoder(epochs: int = 35) -> None:
    historical_templates = load_historical_templates()
    roster_templates = load_roster_montage_portraits()
    seed_templates = historical_templates + roster_templates
    labeled_crops = load_runtime_labeled_target_crops()
    target_portraits, _ = load_target_domain_portraits()
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
    independent_candidate_ids = {
        student_id
        for student_id, image_names in target_groups.items()
        if student_id in historical_ids or len(image_names) > 1
    }
    prototype_only_ids = target_ids - independent_candidate_ids
    if not target_ids:
        raise ValueError("No manually labelled target identities were loaded")

    pretrained_encoder, _ = _train_student_encoder(
        seed_templates,
        max(epochs * 3, epochs),
        "historical-pretrain",
    )
    pretrained_state = {
        name: value.detach().clone()
        for name, value in pretrained_encoder.state_dict().items()
    }

    cross_validation_results = []
    fold_metrics = {}
    image_names = sorted({image_name for _, image_name, _, _ in labeled_crops})
    for validation_image in image_names:
        target_train, _ = load_target_domain_portraits(validation_image)
        fold_templates = seed_templates + target_train
        fold_encoder, _ = _train_student_encoder(
            fold_templates,
            epochs,
            f"fold:{validation_image}",
            pretrained_state,
        )
        fold_gallery, fold_ids = _build_gallery(fold_encoder, fold_templates, catalog)
        validation_items = [
            item for item in labeled_crops if item[1] == validation_image
        ]
        fold_results = _score_with_torch(
            fold_encoder,
            validation_items,
            fold_gallery,
            fold_ids,
            catalog,
        )
        cross_validation_results.extend(fold_results)
        fold_metrics[validation_image] = {
            "count": len(fold_results),
            "known_identity_count": sum(
                result["expected_known"] for result in fold_results
            ),
            "top1_accuracy": sum(
                result["predicted_id"] == result["expected_id"]
                for result in fold_results
            ) / len(fold_results),
        }

    (
        similarity_threshold,
        margin_threshold,
        verified_student_ids,
        cross_validation_metrics,
    ) = _calibrate_verification(
        cross_validation_results,
        independent_candidate_ids,
    )

    templates = seed_templates + target_portraits
    final_training_templates = seed_templates + target_portraits * 3
    final_training_epochs = max(epochs * 3, epochs)
    encoder, names = _train_student_encoder(
        final_training_templates,
        final_training_epochs,
        "final",
        pretrained_state,
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
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

    gallery_embeddings, gallery_ids = _build_gallery(encoder, templates, catalog)
    np.savez_compressed(
        MODEL_DIR / "gallery.npz",
        embeddings=gallery_embeddings,
        student_ids=gallery_ids,
    )

    final_results = _score_with_opencv(
        MODEL_DIR / "student_encoder.onnx",
        labeled_crops,
        gallery_embeddings,
        gallery_ids,
        catalog,
    )
    verified_student_ids = _filter_final_verified(
        verified_student_ids,
        final_results,
        similarity_threshold,
        margin_threshold,
    )
    final_metrics = _accepted_metrics(
        final_results,
        verified_student_ids,
        similarity_threshold,
        margin_threshold,
    )
    verification_failed_ids = independent_candidate_ids - verified_student_ids
    support_metadata = _student_support_metadata(
        target_groups,
        prototype_only_ids,
        verified_student_ids,
        cross_validation_results,
        final_results,
        similarity_threshold,
        margin_threshold,
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
    print("cross-validation:", cross_validation_metrics)
    print("final OpenCV target data:", final_metrics)
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
                "similarity_threshold": similarity_threshold,
                "margin_threshold": margin_threshold,
                "training_source": "committed-git-history+committed-roster-montage+user-manual-target-domain",
                "historical_blob_count": len(historical_templates),
                "roster_montage_portrait_count": len(roster_templates),
                "target_domain_training_count": len(target_portraits),
                "target_domain_training_repeat": 3,
                "final_training_epochs": final_training_epochs,
                "target_avatar_count": target_avatar_count,
                "target_identity_count": len(target_ids),
                "eligible_avatar_count": eligible_avatar_count,
                "plain_avatar_count": target_avatar_count - eligible_avatar_count,
                "independent_validation_candidate_count": len(independent_candidate_ids),
                "augmentation_scale_range": [0.70, 1.40],
                "horizontal_flip": False,
                "verified_student_ids": sorted(verified_student_ids),
                "verified_student_count": len(verified_student_ids),
                "prototype_only_student_ids": sorted(prototype_only_ids),
                "prototype_only_student_count": len(prototype_only_ids),
                "verification_failed_student_ids": sorted(verification_failed_ids),
                "verification_failed_student_count": len(verification_failed_ids),
                "student_support": support_metadata,
                "validation_groups": image_names,
                "validation_fold_metrics": fold_metrics,
                "cross_validation_metrics": cross_validation_metrics,
                "all_labeled_target_metrics": final_metrics,
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
