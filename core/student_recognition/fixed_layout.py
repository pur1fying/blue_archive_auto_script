from __future__ import annotations

import cv2
import numpy as np

from core.student_recognition.types import BoundingBox, LessonCard, StudentAvatar


class FixedLessonLayout:
    """Parse the 1280x720 all-lessons dialog without an object detector."""

    CARD_X = (129, 473, 817)
    CARD_Y = (181, 332, 483)
    CARD_WIDTH = 337
    CARD_HEIGHT = 143
    AVATAR_OFFSET_X = 20
    AVATAR_OFFSET_Y = 76
    AVATAR_STEP_X = 72
    AVATAR_WIDTH = 62
    AVATAR_HEIGHT = 58

    @staticmethod
    def normalize(image: np.ndarray) -> np.ndarray:
        if not isinstance(image, np.ndarray) or image.ndim != 3 or image.size == 0:
            raise ValueError("Invalid lesson screenshot")
        if image.shape[:2] == (720, 1280):
            return image
        return cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)

    def card_box(self, index: int) -> BoundingBox:
        if not 0 <= index < 9:
            raise IndexError(index)
        row, column = divmod(index, 3)
        x1, y1 = self.CARD_X[column], self.CARD_Y[row]
        return BoundingBox(x1, y1, x1 + self.CARD_WIDTH, y1 + self.CARD_HEIGHT)

    def avatar_box(self, card_index: int, slot_index: int) -> BoundingBox:
        if not 0 <= slot_index < 3:
            raise IndexError(slot_index)
        card = self.card_box(card_index)
        x1 = card.x1 + self.AVATAR_OFFSET_X + slot_index * self.AVATAR_STEP_X
        y1 = card.y1 + self.AVATAR_OFFSET_Y
        return BoundingBox(x1, y1, x1 + self.AVATAR_WIDTH, y1 + self.AVATAR_HEIGHT)

    @staticmethod
    def avatar_present(patch: np.ndarray) -> bool:
        if patch.shape[:2] != (58, 62):
            return False
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        return float(patch.std()) > 25.0 and float(hsv[:, :, 1].mean()) > 15.0

    @staticmethod
    def affection_eligible(patch: np.ndarray) -> bool:
        """A pink frame must appear on at least two independent outer sides."""
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        # Ignore rounded corners so one coloured artwork edge cannot leak into
        # the two perpendicular edge measurements.
        sides = (
            hsv[:2, 3:-3, :],
            hsv[-2:, 3:-3, :],
            hsv[3:-3, :2, :],
            hsv[3:-3, -2:, :],
        )
        pink_sides = 0
        for side in sides:
            pixels = side.reshape(-1, 3)
            pink = (
                (pixels[:, 0] >= 145)
                & (pixels[:, 0] <= 179)
                & (pixels[:, 1] >= 65)
                & (pixels[:, 2] >= 140)
            )
            pink_sides += float(pink.mean()) >= 0.005
        return pink_sides >= 2

    def locate(self, image: np.ndarray, statuses: list[str]) -> list[LessonCard]:
        normalized = self.normalize(image)
        cards: list[LessonCard] = []
        for card_index, state in enumerate(statuses[:9]):
            if state not in {"available", "done"}:
                continue
            card_box = self.card_box(card_index)
            card = LessonCard(card_index, card_box, card_box.center, state)
            for slot_index in range(3):
                box = self.avatar_box(card_index, slot_index)
                crop = normalized[box.y1:box.y2, box.x1:box.x2].copy()
                if self.avatar_present(crop):
                    card.avatars.append(
                        StudentAvatar(
                            slot_index=slot_index,
                            bbox=box,
                            eligible=self.affection_eligible(crop),
                            crop=crop,
                        )
                    )
            if card.avatars:
                cards.append(card)
        return cards
