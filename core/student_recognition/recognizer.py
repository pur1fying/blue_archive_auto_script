import json
from pathlib import Path
from typing import Iterable, Optional, Sequence

import cv2
import numpy as np

from core.student_recognition.catalog import StudentCatalog
from core.student_recognition.lesson_locator import MODEL_DIR
from core.student_recognition.types import BoundingBox, StudentPrediction


class StudentRecognizer:
    """ONNX embedding inference with global Top-1 prototype ranking."""

    def __init__(self, catalog: StudentCatalog, model_dir: Optional[Path] = None):
        self.catalog = catalog
        self.model_dir = Path(model_dir) if model_dir else MODEL_DIR
        self.net = None
        self.gallery_embeddings = np.empty((0, 128), dtype=np.float32)
        self.gallery_ids = np.empty((0,), dtype=str)
        self.metadata = {
            "input_width": 96,
            "input_height": 96,
            "similarity_threshold": 0.60,
            "margin_threshold": 0.0,
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        }
        self._load()

    @property
    def available(self) -> bool:
        return self.net is not None and len(self.gallery_ids) > 0

    @property
    def supported_ids(self) -> set[str]:
        """Return every catalog identity that has at least one prototype.

        Kept for API compatibility.  A student's validation/source status is
        diagnostic only and must never suppress a better global Top-1 match.
        """
        return set(self.catalog.records) & set(self.gallery_ids.tolist())

    @property
    def prototype_only_ids(self) -> set[str]:
        support = self.metadata.get("student_support", {})
        if not isinstance(support, dict):
            return set()
        return {
            student_id
            for student_id, detail in support.items()
            if isinstance(detail, dict)
            and detail.get("status") in {"historical_only", "roster_only"}
            and student_id in self.supported_ids
        }

    def support_status(self, student_id: str) -> str:
        support = self.metadata.get("student_support", {})
        if isinstance(support, dict):
            detail = support.get(student_id)
            if isinstance(detail, dict) and isinstance(detail.get("status"), str):
                return detail["status"]
        return "gallery_only" if student_id in self.supported_ids else "no_prototype"

    @property
    def seed_ids(self) -> set[str]:
        return set(self.gallery_ids.tolist())

    def _load(self) -> None:
        model_path = self.model_dir / "student_encoder.onnx"
        gallery_path = self.model_dir / "gallery.npz"
        metadata_path = self.model_dir / "student_encoder.json"
        if metadata_path.exists():
            try:
                self.metadata.update(json.loads(metadata_path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        if not model_path.exists() or not gallery_path.exists():
            return
        try:
            self.net = cv2.dnn.readNetFromONNX(str(model_path))
            gallery = np.load(str(gallery_path), allow_pickle=False)
            embeddings = np.asarray(gallery["embeddings"], dtype=np.float32)
            ids = np.asarray(gallery["student_ids"]).astype(str)
            if embeddings.ndim != 2 or len(embeddings) != len(ids):
                raise ValueError("Invalid student gallery")
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.gallery_embeddings = embeddings / np.maximum(norms, 1e-12)
            self.gallery_ids = ids
        except (cv2.error, OSError, ValueError, KeyError):
            self.net = None
            self.gallery_embeddings = np.empty((0, 128), dtype=np.float32)
            self.gallery_ids = np.empty((0,), dtype=str)

    def identify(
        self,
        crops: Sequence[np.ndarray],
        server: str,
        candidates: Optional[Iterable[str]] = None,
        eligible: Optional[Sequence[bool]] = None,
        boxes: Optional[Sequence[BoundingBox]] = None,
    ) -> list[StudentPrediction]:
        if not crops:
            return []
        eligible_values = list(eligible) if eligible is not None else [False] * len(crops)
        box_values = list(boxes) if boxes is not None else [None] * len(crops)
        if not self.available:
            return [
                StudentPrediction(None, None, 0.0, 0.0, False, flag, box)
                for flag, box in zip(eligible_values, box_values)
            ]

        # Always rank globally. ``server`` and ``candidates`` remain in the
        # signature for callers, but neither narrows the identity gallery.
        allowed_ids = set(self.catalog.records) & self.seed_ids
        gallery_mask = np.array([sid in allowed_ids for sid in self.gallery_ids], dtype=bool)
        if not np.any(gallery_mask):
            return [
                StudentPrediction(None, None, 0.0, 0.0, False, flag, box)
                for flag, box in zip(eligible_values, box_values)
            ]

        valid_indices = [
            index
            for index, crop in enumerate(crops)
            if isinstance(crop, np.ndarray)
            and crop.ndim == 3
            and crop.shape[0] > 1
            and crop.shape[1] > 1
            and crop.shape[2] == 3
            and crop.size > 0
        ]
        predictions = [
            StudentPrediction(
                None,
                None,
                0.0,
                0.0,
                False,
                eligible_values[index],
                box_values[index],
            )
            for index in range(len(crops))
        ]
        if not valid_indices:
            return predictions
        try:
            embeddings = self._embed_views([crops[index] for index in valid_indices])
        except (cv2.error, ValueError, IndexError):
            return predictions
        gallery_embeddings = self.gallery_embeddings[gallery_mask]
        gallery_ids = self.gallery_ids[gallery_mask]
        similarity = np.max(embeddings @ gallery_embeddings.T, axis=1)
        threshold = float(self.metadata["similarity_threshold"])
        for result_index, row in zip(valid_indices, similarity):
            per_student: dict[str, float] = {}
            for sid, score in zip(gallery_ids, row):
                per_student[sid] = max(per_student.get(sid, -1.0), float(score))
            ranked = sorted(per_student.items(), key=lambda item: item[1], reverse=True)
            sid, score = ranked[0]
            second_score = ranked[1][1] if len(ranked) > 1 else -1.0
            margin = score - second_score
            accepted = score >= threshold
            record = self.catalog.record(sid)
            predictions[result_index] = StudentPrediction(
                student_id=sid,
                name=record.canonical_name if record else None,
                score=score,
                margin=margin,
                accepted=accepted,
                eligible=eligible_values[result_index],
                bbox=box_values[result_index],
                support_status=self.support_status(sid),
            )
        return predictions

    def _embed_views(self, crops: Sequence[np.ndarray]) -> np.ndarray:
        width = int(self.metadata["input_width"])
        height = int(self.metadata["input_height"])
        mean = np.asarray(self.metadata["mean"], dtype=np.float32).reshape(1, 1, 3)
        std = np.asarray(self.metadata["std"], dtype=np.float32).reshape(1, 1, 3)
        inputs = []
        for crop in crops:
            for view in self._portrait_views(crop):
                rgb = cv2.cvtColor(self._letterbox(view, width, height), cv2.COLOR_BGR2RGB)
                normalized = (rgb.astype(np.float32) / 255.0 - mean) / std
                inputs.append(normalized.transpose(2, 0, 1))
        blob = np.stack(inputs).astype(np.float32)
        self.net.setInput(blob)
        embeddings = np.asarray(self.net.forward(), dtype=np.float32)
        embeddings = embeddings.reshape(len(crops), -1, embeddings.shape[-1])
        norms = np.linalg.norm(embeddings, axis=2, keepdims=True)
        return embeddings / np.maximum(norms, 1e-12)

    @staticmethod
    def _letterbox(image: np.ndarray, width: int, height: int) -> np.ndarray:
        source_height, source_width = image.shape[:2]
        scale = min(width / source_width, height / source_height)
        target_width = max(1, round(source_width * scale))
        target_height = max(1, round(source_height * scale))
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        resized = cv2.resize(
            image,
            (target_width, target_height),
            interpolation=interpolation,
        )
        canvas = np.full((height, width, 3), 220, dtype=np.uint8)
        x = (width - target_width) // 2
        y = (height - target_height) // 2
        canvas[y:y + target_height, x:x + target_width] = resized
        return canvas

    @staticmethod
    def _portrait_views(crop: np.ndarray) -> list[np.ndarray]:
        """Remove UI decoration and produce scale/translation views.

        Historical templates cover only the inner head artwork. Evaluating a
        few deterministic inner windows lets the CNN compare the same content
        even when a new UI frame changes the outer crop.
        """
        height, width = crop.shape[:2]
        x1 = min(3, max(0, width - 1))
        y1 = min(3, max(0, height - 1))
        x2 = max(x1 + 1, width - max(5, round(width * 0.12)))
        y2 = max(y1 + 1, height - max(5, round(height * 0.12)))
        inner = crop[y1:y2, x1:x2]
        inner_height, inner_width = inner.shape[:2]
        views = [inner]
        for ratio, x_ratio, y_ratio in (
            (0.86, 0.0, 0.0),
            (0.86, 1.0, 0.0),
            (0.78, 0.5, 0.0),
            (0.78, 0.5, 1.0),
        ):
            view_width = max(8, round(inner_width * ratio))
            view_height = max(8, round(inner_height * ratio))
            offset_x = round((inner_width - view_width) * x_ratio)
            offset_y = round((inner_height - view_height) * y_ratio)
            views.append(
                inner[offset_y:offset_y + view_height, offset_x:offset_x + view_width]
            )
        return views
