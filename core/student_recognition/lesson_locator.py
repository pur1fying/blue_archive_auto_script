import json
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from core.student_recognition.types import BoundingBox, LessonCard, StudentAvatar


MODEL_DIR = Path(__file__).resolve().parents[2] / "src" / "models" / "student_recognition"


class LessonLocator:
    """Locate lesson cards and visible student portraits.

    The ONNX segmentation model is preferred. A conservative geometry fallback
    keeps the task usable when model assets are absent or rejected.
    """

    CARD_CLASS = 1
    ELIGIBLE_AVATAR_CLASS = 2
    PLAIN_AVATAR_CLASS = 3

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = Path(model_dir) if model_dir else MODEL_DIR
        self.net = None
        self.metadata = {
            "backend": "segmentation",
            "input_width": 640,
            "input_height": 360,
            "minimum_cards": 1,
            "plain_avatar_ratio_threshold": 0.50,
        }
        self.last_backend = "uninitialized"
        self._load_model()

    @property
    def model_available(self) -> bool:
        return self.net is not None

    def _load_model(self) -> None:
        model_path = self.model_dir / "lesson_locator.onnx"
        metadata_path = self.model_dir / "lesson_locator.json"
        if metadata_path.exists():
            try:
                self.metadata.update(json.loads(metadata_path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        if not model_path.exists():
            return
        try:
            self.net = cv2.dnn.readNetFromONNX(str(model_path))
        except cv2.error:
            self.net = None

    def locate(self, image: np.ndarray) -> list[LessonCard]:
        if image is None or image.ndim != 3 or image.size == 0:
            return []
        if self.net is not None:
            try:
                cards = self._locate_with_model(image)
                if len(cards) >= int(self.metadata.get("minimum_cards", 1)):
                    self.last_backend = "onnx"
                    return cards
            except (cv2.error, ValueError, IndexError):
                pass
        self.last_backend = "geometry-fallback"
        return self._locate_with_geometry(image)

    def _locate_with_model(self, image: np.ndarray) -> list[LessonCard]:
        if self.metadata.get("backend") == "yolox":
            return self._locate_with_yolox(image)
        height, width = image.shape[:2]
        input_width = int(self.metadata["input_width"])
        input_height = int(self.metadata["input_height"])
        blob = cv2.dnn.blobFromImage(
            image,
            scalefactor=1.0 / 255.0,
            size=(input_width, input_height),
            mean=(0, 0, 0),
            swapRB=True,
            crop=False,
        )
        self.net.setInput(blob)
        output = self.net.forward()
        if output.ndim != 4 or output.shape[0] != 1:
            raise ValueError(f"Unexpected lesson locator output: {output.shape}")
        class_map = np.argmax(output[0], axis=0).astype(np.uint8)
        return self._cards_from_segmentation(
            image,
            class_map,
            input_width,
            input_height,
        )

    def _locate_with_yolox(self, image: np.ndarray) -> list[LessonCard]:
        """Decode a static YOLOX output without adding a runtime dependency."""
        image_height, image_width = image.shape[:2]
        input_width = int(self.metadata["input_width"])
        input_height = int(self.metadata["input_height"])
        ratio = min(input_width / image_width, input_height / image_height)
        resized_width = max(1, round(image_width * ratio))
        resized_height = max(1, round(image_height * ratio))
        resized = cv2.resize(
            image,
            (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )
        padded = np.full((input_height, input_width, 3), 114, dtype=np.uint8)
        padded[:resized_height, :resized_width] = resized
        blob = cv2.dnn.blobFromImage(
            padded,
            scalefactor=1.0,
            size=(input_width, input_height),
            mean=(0, 0, 0),
            swapRB=False,
            crop=False,
        )
        self.net.setInput(blob)
        output = np.asarray(self.net.forward())
        if output.ndim != 3 or output.shape[0] != 1:
            raise ValueError(f"Unexpected YOLOX locator output: {output.shape}")
        detections = output[0]
        if detections.shape[0] == 8 and detections.shape[1] != 8:
            detections = detections.T
        if detections.shape[1] != 8:
            raise ValueError(f"Unexpected YOLOX detection width: {detections.shape}")

        class_names = self.metadata.get(
            "class_names",
            ["lesson_card", "eligible_avatar", "plain_avatar"],
        )
        thresholds = self.metadata.get("confidence_thresholds", {})
        nms_threshold = float(self.metadata.get("nms_threshold", 0.50))
        scored_boxes_by_class: list[list[tuple[BoundingBox, float]]] = [[], [], []]
        for class_index, class_name in enumerate(class_names):
            class_scores = detections[:, 4] * detections[:, 5 + class_index]
            confidence_threshold = float(thresholds.get(class_name, 0.20))
            candidate_indices = np.flatnonzero(class_scores >= confidence_threshold)
            if candidate_indices.size == 0:
                continue
            nms_boxes = []
            scores = []
            raw_boxes = []
            for detection_index in candidate_indices:
                center_x, center_y, box_width, box_height = detections[detection_index, :4]
                x1 = float(center_x - box_width / 2.0)
                y1 = float(center_y - box_height / 2.0)
                nms_boxes.append([x1, y1, float(box_width), float(box_height)])
                scores.append(float(class_scores[detection_index]))
                raw_boxes.append((x1, y1, x1 + float(box_width), y1 + float(box_height)))
            kept = cv2.dnn.NMSBoxes(
                nms_boxes,
                scores,
                confidence_threshold,
                nms_threshold,
            )
            for kept_index in np.asarray(kept).reshape(-1):
                x1, y1, x2, y2 = raw_boxes[int(kept_index)]
                scaled = BoundingBox(
                    max(0, min(image_width - 1, round(x1 / ratio))),
                    max(0, min(image_height - 1, round(y1 / ratio))),
                    max(1, min(image_width, round(x2 / ratio))),
                    max(1, min(image_height, round(y2 / ratio))),
                )
                if scaled.width >= 4 and scaled.height >= 4:
                    scored_boxes_by_class[class_index].append(
                        (scaled, scores[int(kept_index)])
                    )

        # Eligibility classes are mutually exclusive views of the same avatar.
        # Suppress their overlaps jointly so one portrait cannot be emitted once
        # as pink and again as gray by neighbouring anchors.
        avatar_candidates = [
            (box, score, class_index)
            for class_index in (1, 2)
            for box, score in scored_boxes_by_class[class_index]
        ]
        boxes_by_class: list[list[BoundingBox]] = [
            [box for box, _ in scored_boxes_by_class[0]],
            [],
            [],
        ]
        if avatar_candidates:
            avatar_nms_boxes = [
                [box.x1, box.y1, box.width, box.height]
                for box, _, _ in avatar_candidates
            ]
            avatar_scores = [score for _, score, _ in avatar_candidates]
            kept_avatars = cv2.dnn.NMSBoxes(
                avatar_nms_boxes,
                avatar_scores,
                min(
                    float(thresholds.get("eligible_avatar", 0.20)),
                    float(thresholds.get("plain_avatar", 0.20)),
                ),
                nms_threshold,
            )
            for kept_index in np.asarray(kept_avatars).reshape(-1):
                box, _, class_index = avatar_candidates[int(kept_index)]
                boxes_by_class[class_index].append(box)

        cards = self._assemble_cards(
            image,
            boxes_by_class[0],
            boxes_by_class[1],
            boxes_by_class[2],
        )
        if len(cards) < int(self.metadata.get("minimum_cards", 1)):
            raise ValueError("Incomplete YOLOX lesson locator result")
        return cards

    def _cards_from_segmentation(
        self,
        image: np.ndarray,
        class_map: np.ndarray,
        input_width: int,
        input_height: int,
    ) -> list[LessonCard]:
        avatar_mask = np.isin(
            class_map,
            (self.ELIGIBLE_AVATAR_CLASS, self.PLAIN_AVATAR_CLASS),
        )
        group_boxes = self._component_boxes(
            avatar_mask,
            min_area=max(40, int(input_width * input_height * 0.002)),
            max_area=int(input_width * input_height * 0.03),
        )
        group_boxes = [
            box
            for box in group_boxes
            if box.y1 > input_height * 0.25
            and box.y2 < input_height * 0.92
            and box.width > input_width * 0.03
            and box.height > input_height * 0.045
        ]
        if len(group_boxes) < int(self.metadata.get("minimum_cards", 1)):
            raise ValueError("Incomplete lesson locator result")

        median_height = float(np.median([box.height for box in group_boxes]))
        # The portrait slot pitch is 72/1280 of the canonical UI width.
        # Deriving it from mask height rounded 17.25 down to 17 and shifted
        # the third crop several pixels left on tightly joined components.
        pitch = max(8, round(input_width * 72 / 1280))
        column_anchors = self._cluster_anchors(
            [box.x1 for box in group_boxes],
            # Three adjacent avatars can be split into a 2-avatar component
            # and a 1-avatar component with a gap just over two pitches.
            # Keep those fragments in one lesson-card column.
            tolerance=pitch * 2.6,
            leading_edge=True,
        )
        row_anchors = self._cluster_anchors(
            [box.y1 for box in group_boxes],
            tolerance=median_height * 1.5,
        )
        if len(column_anchors) > 3 or len(row_anchors) > 3:
            raise ValueError("Unexpected lesson locator grid")

        cards_by_index: dict[int, LessonCard] = {}
        image_height, image_width = image.shape[:2]
        for group in sorted(group_boxes, key=lambda box: (box.y1, box.x1)):
            column = int(np.argmin(np.abs(np.asarray(column_anchors) - group.x1)))
            row = int(np.argmin(np.abs(np.asarray(row_anchors) - group.y1)))
            index = row * 3 + column
            card = cards_by_index.get(index)
            if card is None:
                model_card = BoundingBox(
                    max(0, round(column_anchors[column] - median_height * 0.25)),
                    max(0, round(row_anchors[row] - median_height * 1.20)),
                    min(input_width, round(column_anchors[column] + median_height * 5.25)),
                    min(input_height, round(row_anchors[row] + median_height * 1.20)),
                )
                card_box = self._scale_model_box(
                    model_card,
                    image_width,
                    image_height,
                    input_width,
                    input_height,
                )
                card = LessonCard(index=index, bbox=card_box, click_point=card_box.center)
                cards_by_index[index] = card

            slot_count = max(1, min(3, round(group.width / pitch)))
            for slot in range(slot_count):
                model_x = group.x1 + slot * pitch
                model_y = row_anchors[row]
                status_patch = class_map[
                    max(0, round(model_y - 1)):min(
                        input_height,
                        round(model_y + median_height + 2),
                    ),
                    max(0, model_x - 1):min(input_width, model_x + pitch),
                ]
                eligible_pixels = int(
                    np.count_nonzero(status_patch == self.ELIGIBLE_AVATAR_CLASS)
                )
                plain_pixels = int(
                    np.count_nonzero(status_patch == self.PLAIN_AVATAR_CLASS)
                )
                plain_ratio = plain_pixels / max(1, eligible_pixels + plain_pixels)
                avatar_box = self._scale_avatar_box(
                    model_x,
                    round(model_y),
                    image_width,
                    image_height,
                    input_width,
                    input_height,
                )
                crop = image[
                    avatar_box.y1:avatar_box.y2,
                    avatar_box.x1:avatar_box.x2,
                ].copy()
                if crop.size:
                    card.avatars.append(
                        StudentAvatar(
                            bbox=avatar_box,
                            eligible=plain_ratio
                            < float(self.metadata["plain_avatar_ratio_threshold"]),
                            crop=crop,
                        )
                    )
        cards = sorted(cards_by_index.values(), key=lambda card: card.index)
        for card in cards:
            card.avatars.sort(key=lambda avatar: avatar.bbox.center[0])
        return cards

    @staticmethod
    def _cluster_anchors(
        values: list[int],
        tolerance: float,
        leading_edge: bool = False,
    ) -> list[int]:
        groups: list[list[int]] = []
        for value in sorted(values):
            if not groups or value - np.mean(groups[-1]) > tolerance:
                groups.append([value])
            else:
                groups[-1].append(value)
        if leading_edge:
            return [min(group) for group in groups]
        return [round(float(np.median(group))) for group in groups]

    @staticmethod
    def _scale_model_box(
        box: BoundingBox,
        width: int,
        height: int,
        input_width: int,
        input_height: int,
    ) -> BoundingBox:
        return BoundingBox(
            round(box.x1 * width / input_width),
            round(box.y1 * height / input_height),
            round(box.x2 * width / input_width),
            round(box.y2 * height / input_height),
        )

    @staticmethod
    def _scale_avatar_box(
        model_x: int,
        model_y: int,
        width: int,
        height: int,
        input_width: int,
        input_height: int,
    ) -> BoundingBox:
        # The segmentation output is quarter-resolution at the default input,
        # so a detected leading edge quantizes down by up to one canonical UI
        # pixel. Restore that sub-cell offset, then use the UI-relative portrait
        # size. Position remains model-derived while the crop is stable across
        # screenshot resolutions and matches the labelled 62x58 content window.
        x1 = round(model_x * width / input_width) + max(1, round(width / 1280))
        y1 = round(model_y * height / input_height) + max(1, round(height / 720))
        avatar_width = max(2, round(width * 62 / 1280))
        avatar_height = max(2, round(height * 58 / 720))
        return BoundingBox(
            max(0, x1),
            max(0, y1),
            min(width, x1 + avatar_width),
            min(height, y1 + avatar_height),
        )

    @staticmethod
    def _component_boxes(mask: np.ndarray, min_area: int, max_area: int) -> list[BoundingBox]:
        binary = np.asarray(mask, dtype=np.uint8) * 255
        count, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        boxes: list[BoundingBox] = []
        for x, y, width, height, area in stats[1:count]:
            if min_area <= area <= max_area:
                boxes.append(BoundingBox(int(x), int(y), int(x + width), int(y + height)))
        return boxes

    def _assemble_cards(
        self,
        image: np.ndarray,
        card_boxes: list[BoundingBox],
        eligible_boxes: list[BoundingBox],
        plain_boxes: list[BoundingBox],
    ) -> list[LessonCard]:
        height, width = image.shape[:2]
        cards: list[LessonCard] = []
        occupied_indices: set[int] = set()
        for box in sorted(card_boxes, key=lambda value: (value.center[1], value.center[0])):
            index = self._grid_index(box.center, width, height)
            if index in occupied_indices:
                continue
            occupied_indices.add(index)
            cards.append(LessonCard(index=index, bbox=box, click_point=box.center))

        for box, eligible in [
            *((box, True) for box in eligible_boxes),
            *((box, False) for box in plain_boxes),
        ]:
            card = self._card_for_point(cards, box.center)
            if card is None:
                continue
            x1 = max(0, box.x1)
            y1 = max(0, box.y1)
            x2 = min(width, box.x2)
            y2 = min(height, box.y2)
            crop = image[y1:y2, x1:x2].copy()
            if crop.size:
                card.avatars.append(StudentAvatar(box, eligible, crop))
        for card in cards:
            card.avatars.sort(key=lambda avatar: avatar.bbox.center[0])
        return sorted(cards, key=lambda card: card.index)

    @staticmethod
    def _card_for_point(cards: list[LessonCard], point: tuple[int, int]) -> Optional[LessonCard]:
        containing = [card for card in cards if card.bbox.contains(point)]
        if containing:
            return containing[0]
        if not cards:
            return None
        return min(
            cards,
            key=lambda card: (card.click_point[0] - point[0]) ** 2 + (card.click_point[1] - point[1]) ** 2,
        )

    @staticmethod
    def _grid_index(point: tuple[int, int], width: int, height: int) -> int:
        expected_x = np.array([0.232, 0.500, 0.768]) * width
        expected_y = np.array([0.350, 0.560, 0.770]) * height
        column = int(np.argmin(np.abs(expected_x - point[0])))
        row = int(np.argmin(np.abs(expected_y - point[1])))
        return row * 3 + column

    def _locate_with_geometry(self, image: np.ndarray) -> list[LessonCard]:
        original_height, original_width = image.shape[:2]
        canonical = cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)
        cards: list[LessonCard] = []
        for row, card_y in enumerate((181, 332, 483)):
            for column, card_x in enumerate((129, 473, 817)):
                card_patch = canonical[card_y:card_y + 143, card_x:card_x + 337]
                if not self._looks_like_card(card_patch):
                    continue
                canonical_box = BoundingBox(card_x, card_y, card_x + 337, card_y + 143)
                card = LessonCard(
                    index=row * 3 + column,
                    bbox=self._scale_box(canonical_box, original_width, original_height),
                    click_point=self._scale_point(canonical_box.center, original_width, original_height),
                )
                for slot in range(3):
                    avatar_x = card_x + 20 + slot * 72
                    avatar_y = card_y + 76
                    avatar_patch = canonical[avatar_y:avatar_y + 58, avatar_x:avatar_x + 62]
                    if not self._looks_like_avatar(avatar_patch):
                        continue
                    eligible = self._has_affection_frame(avatar_patch)
                    canonical_avatar_box = BoundingBox(
                        avatar_x,
                        avatar_y,
                        avatar_x + 62,
                        avatar_y + 58,
                    )
                    box = self._scale_box(canonical_avatar_box, original_width, original_height)
                    crop = image[box.y1:box.y2, box.x1:box.x2].copy()
                    card.avatars.append(StudentAvatar(box, eligible, crop))
                cards.append(card)
        return cards

    @staticmethod
    def _looks_like_card(patch: np.ndarray) -> bool:
        if patch.shape[0] < 100 or patch.shape[1] < 200:
            return False
        upper = patch[5:65, 10:-10]
        return float(upper.mean()) > 180 and float(upper.std()) > 22

    @staticmethod
    def _looks_like_avatar(patch: np.ndarray) -> bool:
        if patch.size == 0:
            return False
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        return float(patch.std()) > 25 and float(hsv[:, :, 1].mean()) > 15

    @staticmethod
    def _has_affection_frame(patch: np.ndarray) -> bool:
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        pink = cv2.inRange(hsv, np.array((145, 70, 150)), np.array((179, 255, 255)))
        return int(np.count_nonzero(pink)) >= 20

    @staticmethod
    def _scale_point(point: tuple[int, int], width: int, height: int) -> tuple[int, int]:
        return (round(point[0] * width / 1280), round(point[1] * height / 720))

    @classmethod
    def _scale_box(cls, box: BoundingBox, width: int, height: int) -> BoundingBox:
        x1, y1 = cls._scale_point((box.x1, box.y1), width, height)
        x2, y2 = cls._scale_point((box.x2, box.y2), width, height)
        return BoundingBox(x1, y1, x2, y2)
