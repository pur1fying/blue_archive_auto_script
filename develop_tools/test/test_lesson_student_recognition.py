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
from develop_tools.student_recognition.training_data import (
    HISTORICAL_MANIFEST,
    ROSTER_ANNOTATIONS,
    load_historical_portraits,
    load_roster_montage_portraits,
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
                self.assertEqual(expected["card_indices"], [card.index for card in cards])
                self.assertEqual(len(expected["avatars"]), len(avatars))
                self.assertEqual(
                    {
                        f"{card_index}:{slot}": eligible
                        for card_index, slot, eligible in expected["avatars"]
                    },
                    {
                        f"{card.index}:{slot}": avatar.eligible
                        for card in cards
                        for slot, avatar in enumerate(card.avatars)
                    },
                )
                expected_per_card = [
                    sum(item[0] == card_index for item in expected["avatars"])
                    for card_index in expected["card_indices"]
                ]
                self.assertEqual(expected_per_card, [len(card.avatars) for card in cards])
                for card in cards:
                    self.assertTrue(card.bbox.contains(card.click_point))
                    for avatar in card.avatars:
                        self.assertTrue(card.bbox.contains(avatar.bbox.center))
        self.assertEqual(81, expected_total)
        self.assertEqual(81, actual_total)
        self.assertEqual(81, len(identity_labels))
        self.assertEqual(72, len(set(identity_labels)))
        self.assertEqual(
            71,
            sum(
                eligible
                for image in self.annotation["images"].values()
                for _, _, eligible in image["avatars"]
            ),
        )

    def test_onnx_locator_handles_resolution_scaling(self):
        for image_name, expected in self.annotation["images"].items():
            image = cv2.imread(str(FIXTURE_DIR / image_name))
            for scale in (0.70, 1.0, 1.40):
                with self.subTest(image=image_name, scale=scale):
                    resized = cv2.resize(
                        image,
                        (round(image.shape[1] * scale), round(image.shape[0] * scale)),
                        interpolation=cv2.INTER_LINEAR,
                    )
                    cards = self.locator.locate(resized)
                    self.assertEqual("onnx", self.locator.last_backend)
                    self.assertEqual(expected["card_indices"], [card.index for card in cards])
                    self.assertEqual(
                        len(expected["avatars"]),
                        sum(len(card.avatars) for card in cards),
                    )
                    self.assertEqual(
                        sum(item[2] for item in expected["avatars"]),
                        sum(avatar.eligible for card in cards for avatar in card.avatars),
                    )

    def test_annotation_contains_all_manual_corrections(self):
        expected_gray = {
            "new_ui_1.png": {"2:1": "Megu"},
            "new_ui_2.png": {"1:0": "Noa (Pajamas)"},
            "new_ui_3.png": {
                "1:2": "Saki",
                "3:1": "Reijo",
                "7:1": "Marina (Qipao)",
            },
            "new_ui_4.png": {"2:0": "Chiaki", "6:2": "Maki (Camp)"},
            "new_ui_5.png": {
                "4:0": "Tsukuyo",
                "5:0": "Reijo",
                "5:2": "Shigure (Hot Spring)",
            },
        }
        for image_name, expected in self.annotation["images"].items():
            actual_gray = {
                f"{card_index}:{slot}": expected["identity_labels"][f"{card_index}:{slot}"]
                for card_index, slot, eligible in expected["avatars"]
                if not eligible
            }
            self.assertEqual(expected_gray[image_name], actual_gray)
        self.assertNotIn(
            "Moe",
            {
                name
                for image in self.annotation["images"].values()
                for name in image["identity_labels"].values()
            },
        )

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

    def test_all_target_identities_have_correct_top1(self):
        recognizer = StudentRecognizer(StudentCatalog(STATIC_CONFIG["student_names"]))
        for image_name, expected in self.annotation["images"].items():
            image = cv2.imread(str(FIXTURE_DIR / image_name))
            locations = [
                (card.index, slot, avatar)
                for card in self.locator.locate(image)
                for slot, avatar in enumerate(card.avatars)
            ]
            predictions = recognizer.identify(
                [avatar.crop for _, _, avatar in locations],
                "CN",
            )
            for (card_index, slot, _), prediction in zip(locations, predictions):
                with self.subTest(image=image_name, card=card_index, slot=slot):
                    self.assertEqual(
                        expected["identity_labels"][f"{card_index}:{slot}"],
                        prediction.name,
                    )

    def test_real_gray_and_prototype_only_targets_do_not_select(self):
        service = StudentRecognitionService(STATIC_CONFIG["student_names"])
        gray_cards = service.recognize_lesson(
            cv2.imread(str(FIXTURE_DIR / "new_ui_3.png")),
            "CN",
        )
        self.assertIsNone(
            service.select_priority_card(gray_cards, ["available"] * 9, ["Saki"])
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
        self.assertEqual(265, len(rows))
        self.assertEqual(265, len({row["Global_name"] for row in rows}))
        self.assertEqual(265, len(self.catalog.records))
        self.assertEqual(
            1,
            sum(row["Global_name"] == "Hoshino (Battle)" for row in rows),
        )
        self.assertEqual("hoshino_battle", self.catalog.resolve("Hoshino (Battle)").student_id)

    def test_catalog_has_aliases_only(self):
        self.assertTrue(
            all(
                set(row) == {"CN_name", "Global_name", "JP_name"}
                for row in STATIC_CONFIG["student_names"]
            )
        )
        self.assertFalse(
            any("?" in value for row in STATIC_CONFIG["student_names"] for value in row.values())
        )

    def test_alias_validation_has_no_server_availability_filter(self):
        canonical, unknown = self.catalog.validate_names(["柚子", "not-a-student"])
        self.assertEqual(["Yuzu"], canonical)
        self.assertEqual(["not-a-student"], unknown)

    def test_new_students_are_available(self):
        expected = {
            "Asuna (School)",
            "Karin (School)",
            "Marina (Qipao)",
            "Neru (School)",
            "Noa (Pajamas)",
            "Reijo",
            "Sakurako (Pop Idol)",
            "Maki (Camp)",
            "Rio",
            "Chiaki",
            "Aoba",
            "Tomoe (Qipao)",
            "Kisaki",
            "Yuuka (Pajamas)",
            "Shun (Swimsuit)",
            "Rio (Armed)",
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
            self.assertLessEqual(len(recognizer.supported_ids), 43)
            self.assertGreater(float(recognizer.metadata["margin_threshold"]), 0.0)
            self.assertEqual(
                {
                    "aoba",
                    "atsuko_swimsuit",
                    "chiaki",
                    "chise_swimsuit",
                    "hanako_swimsuit",
                    "haruna",
                    "hibiki",
                    "hinata",
                    "hinata_swimsuit",
                    "ichika",
                    "junko",
                    "karin_school",
                    "kayoko",
                    "maki_camp",
                    "marina_qipao",
                    "meru",
                    "midori_maid",
                    "mutsuki",
                    "neru_school",
                    "noa_pajamas",
                    "nonomi_swimsuit",
                    "pina",
                    "rio",
                    "sakurako_pop_idol",
                    "shigure_hot_spring",
                    "shun_small",
                    "sumire",
                    "tsukuyo",
                    "yoshimi_band",
                },
                recognizer.prototype_only_ids,
            )
            self.assertTrue(
                recognizer.supported_ids.isdisjoint(recognizer.prototype_only_ids)
            )
            self.assertGreater(len(recognizer.seed_ids), len(recognizer.supported_ids))
            self.assertEqual(81, recognizer.metadata["target_avatar_count"])
            self.assertEqual(72, recognizer.metadata["target_identity_count"])
            self.assertEqual(71, recognizer.metadata["eligible_avatar_count"])
            self.assertEqual(10, recognizer.metadata["plain_avatar_count"])
            self.assertEqual(43, recognizer.metadata["independent_validation_candidate_count"])
            self.assertEqual(29, recognizer.metadata["prototype_only_student_count"])
            self.assertEqual(5, len(recognizer.metadata["validation_groups"]))
            self.assertEqual(72, len(recognizer.metadata["student_support"]))
            self.assertEqual(
                72,
                recognizer.metadata["verified_student_count"]
                + recognizer.metadata["prototype_only_student_count"]
                + recognizer.metadata["verification_failed_student_count"],
            )
            self.assertEqual("unsupported", recognizer.support_status("moe"))

    def test_runtime_model_resources_are_under_25mb(self):
        model_dir = ROOT / "src" / "models" / "student_recognition"
        total = sum(path.stat().st_size for path in model_dir.iterdir() if path.is_file())
        self.assertLessEqual(total, 25 * 1024 * 1024)

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


class CommittedTrainingLibraryTest(unittest.TestCase):
    def test_historical_portraits_are_complete_and_deduplicated(self):
        manifest = json.loads(HISTORICAL_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(177, len(manifest))
        self.assertEqual(177, len({row["git_blob"] for row in manifest}))
        self.assertEqual(122, len({row["label"] for row in manifest}))
        self.assertEqual(2, sum(row["label"] == "Toki (Bunny)" for row in manifest))
        self.assertEqual(1, sum(row["label"] == "Aris (Maid)" for row in manifest))
        self.assertNotIn("Ar1s-maid", {row["label"] for row in manifest})
        self.assertEqual(177, len(load_historical_portraits()))

    def test_roster_montages_cover_the_complete_catalog_once(self):
        annotation = json.loads(ROSTER_ANNOTATIONS.read_text(encoding="utf-8"))
        selected = [
            row for row in annotation["entries"]
            if row["include_for_identity_training"]
        ]
        excluded = [
            row for row in annotation["entries"]
            if not row["include_for_identity_training"]
        ]
        self.assertEqual(9, len(annotation["files"]))
        self.assertEqual(267, len(annotation["entries"]))
        self.assertEqual(265, len(selected))
        self.assertEqual(
            {row["Global_name"] for row in STATIC_CONFIG["student_names"]},
            {row["config_name"] for row in selected},
        )
        aliases = {
            row["Global_name"]: (row["CN_name"], row["JP_name"])
            for row in STATIC_CONFIG["student_names"]
        }
        self.assertTrue(
            all(
                (row["source_names"]["cn"], row["source_names"]["jp"])
                == aliases[row["config_name"]]
                for row in annotation["entries"]
            )
        )
        self.assertEqual(
            {
                (3, 1, 8, "second_form_hoshino_armed"),
                (3, 7, 6, "second_form_shun_swimsuit"),
            },
            {
                (
                    row["image_index"],
                    row["row"],
                    row["column"],
                    row["exclude_reason"],
                )
                for row in excluded
            },
        )
        portraits = load_roster_montage_portraits()
        self.assertEqual(265, len(portraits))
        self.assertTrue(all(image.shape == (30, 33, 3) for _, _, image in portraits))


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

    def test_mixed_card_only_allows_eligible_target(self):
        card = self.make_card(3, "Gray", eligible=False)
        eligible_avatar = self.make_card(3, "Pink", eligible=True).avatars[0]
        card.avatars.append(eligible_avatar)
        statuses = ["no activity"] * 9
        statuses[3] = "available"
        self.assertIsNone(
            StudentRecognitionService.select_priority_card([card], statuses, ["Gray"])
        )
        self.assertEqual(
            3,
            StudentRecognitionService.select_priority_card(
                [card],
                statuses,
                ["Pink"],
            ).index,
        )


if __name__ == "__main__":
    unittest.main()
