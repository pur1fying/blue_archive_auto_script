import json
import tempfile
import time
import unittest
from pathlib import Path

import cv2
import numpy as np

from core.student_recognition import (
    BoundingBox,
    LessonCard,
    LessonLocator,
    StudentAvatar,
    StudentCatalog,
    StudentPrediction,
    StudentRecognitionService,
    StudentRecognizer,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
ANNOTATION_PATH = ROOT / "develop_tools" / "student_recognition" / "lesson_locator_annotations.json"


class LessonLocatorGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
        cls.locator = LessonLocator()

    def test_all_visible_students_are_located_without_scroll(self):
        expected_total = 0
        actual_total = 0
        for image_name, expected in self.annotation["images"].items():
            with self.subTest(image=image_name):
                image = cv2.imread(str(FIXTURE_DIR / image_name))
                cards = self.locator.locate(image)
                avatars = [avatar for card in cards for avatar in card.avatars]
                expected_total += len(expected["avatars"])
                actual_total += len(avatars)
                self.assertEqual(8, len(cards))
                self.assertEqual(len(expected["avatars"]), len(avatars))
                self.assertEqual(
                    sum(item[2] for item in expected["avatars"]),
                    sum(avatar.eligible for avatar in avatars),
                )
                expected_per_card = [
                    sum(item[0] == card_index for item in expected["avatars"])
                    for card_index in range(8)
                ]
                self.assertEqual(expected_per_card, [len(card.avatars) for card in cards])
                self.assertEqual(list(range(8)), [card.index for card in cards])
                for card in cards:
                    self.assertTrue(card.bbox.contains(card.click_point))
                    for avatar in card.avatars:
                        self.assertTrue(card.bbox.contains(avatar.bbox.center))
        self.assertEqual(47, expected_total)
        self.assertEqual(47, actual_total)

    def test_onnx_locator_handles_resolution_scaling(self):
        image = cv2.imread(str(FIXTURE_DIR / "new_ui_2.png"))
        for scale in (0.75, 1.0, 1.4):
            with self.subTest(scale=scale):
                resized = cv2.resize(
                    image,
                    (round(image.shape[1] * scale), round(image.shape[0] * scale)),
                    interpolation=cv2.INTER_LINEAR,
                )
                cards = self.locator.locate(resized)
                self.assertEqual("onnx", self.locator.last_backend)
                self.assertEqual(8, len(cards))
                self.assertEqual(16, sum(len(card.avatars) for card in cards))
                self.assertEqual(15, sum(avatar.eligible for card in cards for avatar in card.avatars))

    def test_geometry_fallback_handles_resolution_scaling(self):
        locator = LessonLocator(ROOT / "missing-model-directory")
        image = cv2.imread(str(FIXTURE_DIR / "new_ui_2.png"))
        for scale in (0.75, 1.0, 1.4):
            with self.subTest(scale=scale):
                resized = cv2.resize(
                    image,
                    (round(image.shape[1] * scale), round(image.shape[0] * scale)),
                    interpolation=cv2.INTER_LINEAR,
                )
                cards = locator.locate(resized)
                self.assertEqual(8, len(cards))
                self.assertEqual(16, sum(len(card.avatars) for card in cards))
                self.assertEqual(15, sum(avatar.eligible for card in cards for avatar in card.avatars))

    def test_invite_flow_has_no_swipe(self):
        source = (ROOT / "module" / "lesson.py").read_text(encoding="utf-8")
        invite_source = source.split("def invite_favor_student", 1)[1].split(
            "def get_student_recognition_service",
            1,
        )[0]
        self.assertNotIn(".swipe(", invite_source)
        self.assertNotIn("update_screenshot_array", invite_source)
        self.assertNotIn("get_favor_student_detect_region", source)

    def test_verified_identity_predictions_are_safe(self):
        static_config = json.loads((ROOT / "config" / "static.json").read_text(encoding="utf-8"))
        recognizer = StudentRecognizer(StudentCatalog(static_config["student_names"]))
        accepted_total = 0
        for image_name, expected in self.annotation["images"].items():
            image = cv2.imread(str(FIXTURE_DIR / image_name))
            cards = self.locator.locate(image)
            locations = [
                (card.index, slot, avatar)
                for card in cards
                for slot, avatar in enumerate(card.avatars)
            ]
            predictions = recognizer.identify(
                [avatar.crop for _, _, avatar in locations],
                "CN",
                eligible=[avatar.eligible for _, _, avatar in locations],
            )
            labels = expected.get("identity_labels", {})
            for (card_index, slot, _), prediction in zip(locations, predictions):
                if not prediction.accepted:
                    continue
                accepted_total += 1
                key = f"{card_index}:{slot}"
                self.assertIn(key, labels)
                self.assertEqual(labels[key], prediction.name)
            if image_name == "new_ui_2.png":
                self.assertFalse(any(prediction.accepted for prediction in predictions))
        self.assertGreaterEqual(accepted_total, 11)

    def test_default_targets_are_recognized(self):
        static_config = json.loads((ROOT / "config" / "static.json").read_text(encoding="utf-8"))
        recognizer = StudentRecognizer(StudentCatalog(static_config["student_names"]))
        found = set()
        for image_name in ("new_ui_1.png", "new_ui_3.png"):
            image = cv2.imread(str(FIXTURE_DIR / image_name))
            avatars = [
                avatar
                for card in self.locator.locate(image)
                for avatar in card.avatars
            ]
            predictions = recognizer.identify(
                [avatar.crop for avatar in avatars],
                "CN",
            )
            found.update(
                prediction.name
                for prediction in predictions
                if prediction.accepted
            )
        self.assertTrue({"Yuzu", "Yuzu (Maid)"}.issubset(found))

    def test_end_to_end_cpu_target_is_under_500ms(self):
        static_config = json.loads((ROOT / "config" / "static.json").read_text(encoding="utf-8"))
        recognizer = StudentRecognizer(StudentCatalog(static_config["student_names"]))
        image = cv2.imread(str(FIXTURE_DIR / "new_ui_3.png"))
        self.locator.locate(image)  # warm OpenCV's DNN backend
        start = time.perf_counter()
        cards = self.locator.locate(image)
        avatars = [avatar for card in cards for avatar in card.avatars]
        recognizer.identify([avatar.crop for avatar in avatars], "CN")
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertLess(elapsed_ms, 500)


class StudentCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        static_config = json.loads((ROOT / "config" / "static.json").read_text(encoding="utf-8"))
        cls.catalog = StudentCatalog(static_config["student_names"])

    def test_duplicate_names_are_collapsed(self):
        self.assertEqual(193, len(self.catalog.records))
        self.assertEqual("hoshino_battle", self.catalog.resolve("Hoshino (Battle)").student_id)

    def test_server_implementation_counts(self):
        self.assertEqual(136, len(self.catalog.implemented_ids("CN")))
        self.assertEqual(172, len(self.catalog.implemented_ids("Global_en-us")))
        self.assertEqual(193, len(self.catalog.implemented_ids("JP")))

    def test_alias_and_server_validation(self):
        canonical, unknown, unavailable = self.catalog.validate_names(
            ["柚子", "not-a-student"],
            "CN",
        )
        self.assertEqual(["Yuzu"], canonical)
        self.assertEqual(["not-a-student"], unknown)
        self.assertEqual([], unavailable)

    def test_model_assets_load_when_present(self):
        recognizer = StudentRecognizer(self.catalog)
        model_path = ROOT / "src" / "models" / "student_recognition" / "student_encoder.onnx"
        gallery_path = ROOT / "src" / "models" / "student_recognition" / "gallery.npz"
        if model_path.exists() and gallery_path.exists():
            self.assertTrue(recognizer.available)
            self.assertEqual(14, len(recognizer.supported_ids))
            self.assertEqual(122, len(recognizer.seed_ids))
            self.assertGreater(len(recognizer.seed_ids), len(recognizer.supported_ids))

    def test_corrupt_models_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            model_dir = Path(directory)
            (model_dir / "student_encoder.onnx").write_bytes(b"not-an-onnx-model")
            np.savez_compressed(
                model_dir / "gallery.npz",
                embeddings=np.zeros((1, 128), dtype=np.float32),
                student_ids=np.asarray(["yuzu"]),
            )
            recognizer = StudentRecognizer(self.catalog, model_dir)
            self.assertFalse(recognizer.available)

            (model_dir / "lesson_locator.onnx").write_bytes(b"not-an-onnx-model")
            locator = LessonLocator(model_dir)
            image = cv2.imread(str(FIXTURE_DIR / "new_ui_1.png"))
            self.assertEqual(8, len(locator.locate(image)))
            self.assertEqual("geometry-fallback", locator.last_backend)


class LessonPrioritySelectionTest(unittest.TestCase):
    @staticmethod
    def make_card(index, name, eligible=True, accepted=True):
        box = BoundingBox(0, 0, 100, 100)
        avatar = StudentAvatar(
            bbox=BoundingBox(5, 5, 45, 45),
            eligible=eligible,
            crop=np.zeros((40, 40, 3), dtype=np.uint8),
            prediction=StudentPrediction(
                student_id=name.lower(),
                name=name,
                score=0.99,
                margin=0.20,
                accepted=accepted,
                eligible=eligible,
            ),
        )
        return LessonCard(index=index, bbox=box, click_point=box.center, avatars=[avatar])

    def test_priority_order_beats_card_order(self):
        cards = [self.make_card(1, "Secondary"), self.make_card(5, "Primary")]
        statuses = ["available"] * 9
        selected = StudentRecognitionService.select_priority_card(
            cards,
            statuses,
            ["Primary", "Secondary"],
        )
        self.assertEqual(5, selected.index)

    def test_duplicate_target_uses_first_available_card(self):
        cards = [self.make_card(5, "Yuzu"), self.make_card(2, "Yuzu")]
        selected = StudentRecognitionService.select_priority_card(
            cards,
            ["available"] * 9,
            ["Yuzu"],
        )
        self.assertEqual(2, selected.index)

    def test_gray_locked_and_low_confidence_targets_are_ignored(self):
        cards = [
            self.make_card(0, "Yuzu", eligible=False),
            self.make_card(1, "Yuzu"),
            self.make_card(2, "Yuzu", accepted=False),
        ]
        statuses = ["available", "lock", "available"] + ["no activity"] * 6
        self.assertIsNone(
            StudentRecognitionService.select_priority_card(cards, statuses, ["Yuzu"])
        )
        self.assertIsNone(
            StudentRecognitionService.select_priority_card(
                cards,
                ["available"] * 9,
                ["Missing"],
            )
        )


if __name__ == "__main__":
    unittest.main()
