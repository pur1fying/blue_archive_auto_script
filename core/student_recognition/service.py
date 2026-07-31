from pathlib import Path
from typing import Iterable, Optional

import numpy as np

from core.student_recognition.catalog import StudentCatalog
from core.student_recognition.lesson_locator import LessonLocator
from core.student_recognition.recognizer import StudentRecognizer
from core.student_recognition.types import LessonCard


class StudentRecognitionService:
    def __init__(self, student_rows: Iterable[dict], model_dir: Optional[Path] = None):
        self.catalog = StudentCatalog(student_rows)
        self.lesson_locator = LessonLocator(model_dir)
        self.recognizer = StudentRecognizer(self.catalog, model_dir)

    @property
    def identity_available(self) -> bool:
        return self.recognizer.available

    def recognize_lesson(
        self,
        image: np.ndarray,
        server: str,
        candidates: Optional[Iterable[str]] = None,
    ) -> list[LessonCard]:
        cards = self.lesson_locator.locate(image)
        avatars = [avatar for card in cards for avatar in card.avatars]
        predictions = self.recognizer.identify(
            [avatar.crop for avatar in avatars],
            server=server,
            candidates=candidates,
            eligible=[avatar.eligible for avatar in avatars],
            boxes=[avatar.bbox for avatar in avatars],
        )
        for avatar, prediction in zip(avatars, predictions):
            avatar.prediction = prediction
        return cards

    @staticmethod
    def select_priority_card(
        cards: Iterable[LessonCard],
        statuses: list[str],
        priorities: Iterable[str],
    ) -> Optional[LessonCard]:
        """Return the first safe card for the highest-priority student."""
        ordered_cards = sorted(cards, key=lambda card: card.index)
        for target_name in priorities:
            for card in ordered_cards:
                if card.index >= len(statuses) or statuses[card.index] != "available":
                    continue
                for avatar in card.avatars:
                    prediction = avatar.prediction
                    if (
                        avatar.eligible
                        and prediction is not None
                        and prediction.accepted
                        and prediction.name == target_name
                    ):
                        return card
        return None
