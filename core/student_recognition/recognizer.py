from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Sequence

import cv2
import numpy as np

from core.student_recognition.catalog import StudentCatalog
from core.student_recognition.types import StudentPrediction


class StudentRecognizer:
    """OpenCV ONNX inference with global per-identity Top-1 ranking."""

    def __init__(self, catalog: StudentCatalog, model_dir: Path):
        self.catalog = catalog
        self.model_dir = model_dir
        self.net = None
        self.gallery_embeddings = np.empty((0, 128), dtype=np.float32)
        self.gallery_ids = np.empty((0,), dtype=str)
        self.metadata: dict = {}
        self._load()

    @property
    def available(self) -> bool:
        return self.net is not None and len(self.gallery_ids) > 0

    def _load(self) -> None:
        try:
            self.metadata = json.loads(
                (self.model_dir / "student_encoder.json").read_text(encoding="utf-8")
            )
            expected_width = int(self.metadata["embedding_size"])
            self.net = cv2.dnn.readNetFromONNX(
                str(self.model_dir / "student_encoder.onnx")
            )
            gallery = np.load(self.model_dir / "gallery.npz", allow_pickle=False)
            embeddings = np.asarray(gallery["embeddings"], dtype=np.float32)
            ids = np.asarray(gallery["student_ids"]).astype(str)
            if embeddings.ndim != 2 or embeddings.shape[1] != expected_width or len(ids) != len(embeddings):
                raise ValueError("Invalid student gallery")
            if not set(ids).issubset(self.catalog.records):
                raise ValueError("Gallery contains unknown student ids")
            embeddings /= np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12)
            self.gallery_embeddings = embeddings
            self.gallery_ids = ids
        except (OSError, ValueError, TypeError, KeyError, cv2.error, json.JSONDecodeError):
            self.net = None
            self.gallery_embeddings = np.empty((0, 128), dtype=np.float32)
            self.gallery_ids = np.empty((0,), dtype=str)

    def identify(
        self,
        crops: Sequence[np.ndarray],
        server: str = "",
        candidates: Optional[Iterable[str]] = None,
    ) -> list[StudentPrediction]:
        del server, candidates
        empty = StudentPrediction(None, None, 0.0, 0.0, False)
        predictions = [empty for _ in crops]
        if not crops or not self.available:
            return predictions
        valid = [
            index for index, crop in enumerate(crops)
            if isinstance(crop, np.ndarray) and crop.ndim == 3 and crop.shape[2] == 3 and crop.size > 0
        ]
        if not valid:
            return predictions
        try:
            views_per_crop = [self._portrait_views(crops[index]) for index in valid]
            blob = np.stack(
                [self._student_view(view) for views in views_per_crop for view in views]
            )
            self.net.setInput(blob)
            embeddings = np.asarray(self.net.forward(), dtype=np.float32)
            view_count = len(views_per_crop[0])
            if (
                embeddings.ndim != 2
                or embeddings.shape != (len(valid) * view_count, self.gallery_embeddings.shape[1])
            ):
                return predictions
            embeddings /= np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12)
            embeddings = embeddings.reshape(len(valid), view_count, -1)
            similarity = np.max(embeddings @ self.gallery_embeddings.T, axis=1)
        except (cv2.error, ValueError, IndexError):
            return predictions
        for result_index, scores in zip(valid, similarity):
            best_by_id: dict[str, float] = {}
            for sid, score in zip(self.gallery_ids, scores):
                best_by_id[sid] = max(best_by_id.get(sid, -1.0), float(score))
            ranked = sorted(best_by_id.items(), key=lambda item: item[1], reverse=True)
            sid, score = ranked[0]
            margin = score - ranked[1][1] if len(ranked) > 1 else score
            predictions[result_index] = StudentPrediction(
                sid,
                self.catalog.records[sid].canonical_name,
                score,
                margin,
                True,
            )
        return predictions

    def _student_view(self, crop: np.ndarray) -> np.ndarray:
        size = int(self.metadata.get("input_width", 96))
        height, width = crop.shape[:2]
        scale = min(size / width, size / height)
        target = (max(1, round(width * scale)), max(1, round(height * scale)))
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        resized = cv2.resize(crop, target, interpolation=interpolation)
        canvas = np.full((size, size, 3), 220, dtype=np.uint8)
        x = (size - target[0]) // 2
        y = (size - target[1]) // 2
        canvas[y:y + target[1], x:x + target[0]] = resized
        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        mean = np.asarray(self.metadata.get("mean", [0.485, 0.456, 0.406]), dtype=np.float32)
        std = np.asarray(self.metadata.get("std", [0.229, 0.224, 0.225]), dtype=np.float32)
        return ((rgb - mean) / std).transpose(2, 0, 1).astype(np.float32)

    @staticmethod
    def _portrait_views(crop: np.ndarray) -> list[np.ndarray]:
        """Remove the frame and evaluate deterministic inner translations."""
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
