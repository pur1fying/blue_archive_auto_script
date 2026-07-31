from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x1 + self.width // 2, self.y1 + self.height // 2)

    def contains(self, point: Tuple[int, int]) -> bool:
        return self.x1 <= point[0] <= self.x2 and self.y1 <= point[1] <= self.y2


@dataclass
class StudentPrediction:
    student_id: Optional[str]
    name: Optional[str]
    score: float
    margin: float
    accepted: bool
    eligible: bool = False
    bbox: Optional[BoundingBox] = None


@dataclass
class StudentAvatar:
    bbox: BoundingBox
    eligible: bool
    crop: np.ndarray = field(repr=False)
    prediction: Optional[StudentPrediction] = None


@dataclass
class LessonCard:
    index: int
    bbox: BoundingBox
    click_point: Tuple[int, int]
    avatars: list[StudentAvatar] = field(default_factory=list)
    available: Optional[bool] = None
