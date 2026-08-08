from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import numpy as np

from core.student_recognition.catalog import StudentCatalog
from core.student_recognition.fixed_layout import FixedLessonLayout
from core.student_recognition.model_downloader import ModelDownloadError, ensure_model_files
from core.student_recognition.recognizer import StudentRecognizer
from core.student_recognition.types import LessonCard


class StudentRecognitionService:
    def __init__(
        self,
        student_rows: Iterable[dict],
        project_root: Path,
        model_dir: Optional[Path] = None,
        catalog: Optional[StudentCatalog] = None,
    ):
        self.catalog = catalog if catalog is not None else StudentCatalog(student_rows)
        self.layout = FixedLessonLayout()
        self.load_error: Optional[str] = None
        try:
            resolved_model_dir = model_dir or ensure_model_files(project_root)
            self.recognizer = StudentRecognizer(self.catalog, resolved_model_dir)
            if not self.recognizer.available:
                self.load_error = "student model package is invalid"
        except ModelDownloadError as error:
            self.load_error = str(error)
            self.recognizer = None

    @property
    def available(self) -> bool:
        return self.recognizer is not None and self.recognizer.available

    def recognize_lesson(
        self,
        image: np.ndarray,
        statuses: list[str],
        server: str = "",
    ) -> list[LessonCard]:
        cards = self.layout.locate(image, statuses)
        if not self.available:
            return cards
        avatars = [avatar for card in cards for avatar in card.avatars]
        predictions = self.recognizer.identify(
            [avatar.crop for avatar in avatars], server=server
        )
        for avatar, prediction in zip(avatars, predictions):
            avatar.prediction = prediction
        return cards

    @staticmethod
    def select_priority_card(
        cards: Iterable[LessonCard], priorities: Iterable[str]
    ) -> Optional[LessonCard]:
        ordered = sorted(cards, key=lambda card: card.index)
        for target in priorities:
            for card in ordered:
                if card.state != "available":
                    continue
                for avatar in card.avatars:
                    prediction = avatar.prediction
                    if avatar.eligible and prediction and prediction.accepted and prediction.name == target:
                        return card
        return None
