import json
import tempfile
import time
import unittest
from pathlib import Path

import cv2
import numpy as np

from core.config.default_config import STATIC_DEFAULT_CONFIG
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
STATIC_CONFIG = json.loads(STATIC_DEFAULT_CONFIG)


class LessonLocatorGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
        cls.locator = LessonLocator()

    def test_all_visible_students_are_located_without_scroll(self):
        expected_total = 0
        actual_total = 0
        identity_labels = []
        for image_name, expected in self.annotation["images"].items():
            with self.subTest(image=image_name):
                image = cv2.imread(str(FIXTURE_DIR / image_name))
                cards = self.locator.locate(image)
                avatars = [avatar for card in cards for avatar in card.avatars]
                expected_total += len(expected["avatars"])
                actual_total += len(avatars)
                identity_labels.extend(expected["identity_labels"].values())
                self.assertEqual(len(expected["avatars"]), len(expected["identity_labels"]))
                self.assertEqual(
                    {f"{card_index}:{slot}" for card_index, slot, _ in expected["avatars"]},
                    set(expected["identity_labels"]),
                )
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
        self.assertEqual(47, len(identity_labels))
        self.assertEqual(45, len(set(identity_labels)))
        self.assertEqual(
            45,
            sum(
                eligible
                for image in self.annotation["images"].values()
                for _, _, eligible in image["avatars"]
            ),
        )

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
        recognizer = StudentRecognizer(StudentCatalog(STATIC_CONFIG["student_names"]))
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
                if prediction.student_id in recognizer.prototype_only_ids:
                    self.assertEqual("prototype_only", prediction.support_status)
                    self.assertFalse(prediction.accepted)
                if not prediction.accepted:
                    continue
                accepted_total += 1
                key = f"{card_index}:{slot}"
                self.assertIn(key, labels)
                self.assertEqual(labels[key], prediction.name)
        self.assertGreater(accepted_total, 0)

    def test_real_gray_and_prototype_only_targets_do_not_select(self):
        service = StudentRecognitionService(STATIC_CONFIG["student_names"])
        gray_cards = service.recognize_lesson(
            cv2.imread(str(FIXTURE_DIR / "new_ui_3.png")),
            "CN",
        )
        self.assertIsNone(
            service.select_priority_card(gray_cards, ["available"] * 9, ["Moe"])
        )

        prototype_cards = service.recognize_lesson(
            cv2.imread(str(FIXTURE_DIR / "new_ui_1.png")),
            "CN",
        )
        self.assertIsNone(
            service.select_priority_card(
                prototype_cards,
                ["available"] * 9,
                ["Ichika"],
            )
        )

    def test_every_verified_target_is_recognized(self):
        recognizer = StudentRecognizer(StudentCatalog(STATIC_CONFIG["student_names"]))
        found = set()
        for image_name in self.annotation["images"]:
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
        self.assertEqual(
            recognizer.supported_ids,
            {
                recognizer.catalog.resolve(name).student_id
                for name in found
            },
        )

    def test_end_to_end_cpu_target_is_under_500ms(self):
        recognizer = StudentRecognizer(StudentCatalog(STATIC_CONFIG["student_names"]))
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
        cls.catalog = StudentCatalog(STATIC_CONFIG["student_names"])

    def test_duplicate_names_are_collapsed(self):
        rows = STATIC_CONFIG["student_names"]
        self.assertEqual(199, len(rows))
        self.assertEqual(199, len({row["Global_name"] for row in rows}))
        self.assertEqual(199, len(self.catalog.records))
        self.assertEqual(
            1,
            sum(row["Global_name"] == "Hoshino (Battle)" for row in rows),
        )
        self.assertEqual("hoshino_battle", self.catalog.resolve("Hoshino (Battle)").student_id)

    def test_server_implementation_counts(self):
        self.assertEqual(199, len(self.catalog.implemented_ids("CN")))
        self.assertEqual(199, len(self.catalog.implemented_ids("Global_en-us")))
        self.assertEqual(199, len(self.catalog.implemented_ids("JP")))

    def test_alias_and_server_validation(self):
        canonical, unknown, unavailable = self.catalog.validate_names(
            ["柚子", "not-a-student"],
            "CN",
        )
        self.assertEqual(["Yuzu"], canonical)
        self.assertEqual(["not-a-student"], unknown)
        self.assertEqual([], unavailable)

    def test_new_students_are_available(self):
        expected = {
            "Asuna (School)",
            "Karin (School)",
            "Marina (Qipao)",
            "Neru (School)",
            "Noa (Pajamas)",
            "Reijo",
        }
        self.assertEqual(
            expected,
            {self.catalog.resolve(name).canonical_name for name in expected},
        )

    def test_generated_static_config_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / "static.json"
            generated.write_text(STATIC_DEFAULT_CONFIG, encoding="utf-8")
            self.assertEqual(
                STATIC_CONFIG["student_names"],
                json.loads(generated.read_text(encoding="utf-8"))["student_names"],
            )

    def test_model_assets_load_when_present(self):
        recognizer = StudentRecognizer(self.catalog)
        model_path = ROOT / "src" / "models" / "student_recognition" / "student_encoder.onnx"
        gallery_path = ROOT / "src" / "models" / "student_recognition" / "gallery.npz"
        if model_path.exists() and gallery_path.exists():
            self.assertTrue(recognizer.available)
            self.assertLessEqual(len(recognizer.supported_ids), 29)
            self.assertGreater(float(recognizer.metadata["margin_threshold"]), 0.0)
            self.assertEqual(
                {
                    "atsuko_swimsuit",
                    "chise_swimsuit",
                    "hinata",
                    "ichika",
                    "junko",
                    "karin_school",
                    "kotama_camp",
                    "marina_qipao",
                    "midori_maid",
                    "mutsuki",
                    "neru_school",
                    "noa_pajamas",
                    "nonomi_swimsuit",
                    "reijo",
                    "sumire",
                    "yoshimi_band",
                },
                recognizer.prototype_only_ids,
            )
            self.assertTrue(
                recognizer.supported_ids.isdisjoint(recognizer.prototype_only_ids)
            )
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
