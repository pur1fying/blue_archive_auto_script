from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)


@dataclass
class StudentPrediction:
    student_id: Optional[str]
    name: Optional[str]
    score: float
    margin: float
    accepted: bool


@dataclass
class StudentAvatar:
    slot_index: int
    bbox: BoundingBox
    eligible: bool
    crop: np.ndarray = field(repr=False)
    prediction: Optional[StudentPrediction] = None


@dataclass
class LessonCard:
    index: int
    bbox: BoundingBox
    click_point: tuple[int, int]
    state: str
    avatars: list[StudentAvatar] = field(default_factory=list)
