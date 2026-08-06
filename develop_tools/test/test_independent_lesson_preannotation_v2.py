import hashlib
import json
import unittest
from pathlib import Path

from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.catalog import StudentCatalog
from develop_tools.student_recognition.preannotate_independent_v2 import (
    MODEL_FILES,
    generate,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson_independent_v2"
TRAINING_FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
TRAINING_ANNOTATION_PATH = (
    ROOT / "develop_tools" / "student_recognition" / "lesson_locator_annotations.json"
)
PREANNOTATION_PATH = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "independent_test_preannotations_v2.json"
)
MARKDOWN_PATH = PREANNOTATION_PATH.with_suffix(".md")
GROUND_TRUTH_PATH = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "independent_test_annotations_v2.json"
)
TRAINING_SCRIPT_PATH = (
    ROOT / "develop_tools" / "student_recognition" / "train_student_models.py"
)
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"

SCREENSHOTS = {
    "MuMu-20260806-231258-968.png": (7, 17, {6}, "e12131cad1ad3063e9b9ccb238a2649d1a82d4f0157b9e9d603b0bc0673e4a42"),
    "MuMu-20260806-231304-820.png": (7, 15, {5}, "81c7af909cfeff0ff84813ff147c3cc14fa5c926b8d3fb5a33c737bec257f731"),
    "MuMu-20260806-231311-941.png": (8, 18, {3}, "9e025ccb915c5c41721cd178cba8e7a464484d3253257b214b0e32230674c08c"),
    "MuMu-20260806-231317-557.png": (8, 16, {7}, "4460a28e14d08587e0759cd9bafed179e1720c139af3e207b50fb67a0662c175"),
    "MuMu-20260806-231322-679.png": (8, 17, {0}, "949be86f7876cb5806f443a9e1603c9582dd47b379a8a8e0aca7653ce3deea40"),
    "MuMu-20260806-231327-489.png": (8, 17, set(), "afa5f221db0c51bb2ef5e37a1982b3cda54a48af86d1d1491f5e507f30a153f1"),
    "MuMu-20260806-231332-087.png": (8, 17, {4}, "469b80a46af48d02a1c2dd36ed922653b0dd68663eba73754642392701c067c0"),
    "MuMu-20260806-231336-603.png": (8, 17, set(), "f5ce69bab8dac63ba0ee5142a9a989875417660f4da125a31783eb16dda34394"),
    "MuMu-20260806-231341-107.png": (8, 16, set(), "2b8f24759479991c514329298a1d31259a8f53e9ae73df005f995ea00228388f"),
    "MuMu-20260806-231345-085.png": (8, 16, set(), "f0531da5730f781a827f73add98ab28fa6c76ff444f39e61d1e9ac05911f5db6"),
    "MuMu-20260806-231349-471.png": (8, 16, {4}, "c05c394158379301a7a633e916373853c0b23ad2c6aaa5502d98086d75ec03c7"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IndependentLessonPreannotationV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(PREANNOTATION_PATH.read_text(encoding="utf-8"))
        cls.images = {image["file"]: image for image in cls.report["images"]}
        cls.instances = [
            row for image in cls.report["images"] for row in image["instances"]
        ]

    def test_review_state_and_fixed_counts(self):
        self.assertEqual("lesson_independent_v2", self.report["dataset_id"])
        self.assertEqual("pending_user_review", self.report["status"])
        self.assertEqual(
            "model_preannotation_not_ground_truth_or_accuracy",
            self.report["classification"],
        )
        self.assertEqual(
            {
                "images": 11,
                "nonempty_cards": 86,
                "avatars": 182,
                "selected_cards": 7,
                "selected_state_avatars": 18,
                "available_state_cards": 79,
                "available_state_avatars": 164,
                "predicted_pink_available": 144,
                "predicted_gray_available": 20,
                "predicted_pink_selected": 17,
                "predicted_gray_selected": 1,
            },
            self.report["counts"],
        )
        self.assertFalse(self.report["data_policy"]["formal_metrics_allowed_before_user_review"])
        self.assertFalse(self.report["data_policy"]["included_in_training"])
        self.assertFalse(self.report["data_policy"]["included_in_gallery"])
        self.assertFalse(self.report["data_policy"]["used_for_model_or_threshold_selection"])

    def test_original_files_and_selected_cards_are_exact(self):
        self.assertEqual(set(SCREENSHOTS), set(self.images))
        self.assertEqual(set(SCREENSHOTS), {path.name for path in FIXTURE_DIR.glob("*.png")})
        for filename, (card_count, avatar_count, selected_cards, expected_hash) in SCREENSHOTS.items():
            image = self.images[filename]
            self.assertEqual([1280, 720], [image["width"], image["height"]])
            self.assertEqual(expected_hash, image["sha256"])
            self.assertEqual(expected_hash, sha256(FIXTURE_DIR / filename))
            self.assertEqual(card_count, len(image["card_bboxes"]))
            self.assertEqual(avatar_count, len(image["instances"]))
            self.assertEqual(selected_cards, set(image["selected_card_indices"]))
            self.assertEqual(
                avatar_count,
                len({row["location"] for row in image["instances"]}),
            )

    def test_selected_state_is_inherited_and_never_clicked(self):
        for image in self.report["images"]:
            selected_cards = set(image["selected_card_indices"])
            for row in image["instances"]:
                expected_state = (
                    "selected" if row["card_index"] in selected_cards else "available"
                )
                self.assertEqual(expected_state, row["card_state"])
                if expected_state == "selected":
                    self.assertFalse(row["simulated_source_card_clicked"])
                    self.assertNotEqual(
                        row["card_index"], row["simulated_selected_card_index"]
                    )

    def test_predictions_are_reviewable_but_not_ground_truth(self):
        catalog = StudentCatalog(json.loads(STATIC_DEFAULT_CONFIG)["student_names"])
        forbidden_keys = {
            "name",
            "expected_name",
            "ground_truth",
            "identity_correct",
            "accuracy",
            "correct",
        }
        for row in self.instances:
            self.assertEqual("pending_user_review", row["review_status"])
            self.assertTrue(row["prediction_valid"])
            self.assertIsNotNone(catalog.resolve(row["predicted_name"]), row["predicted_name"])
            self.assertTrue(forbidden_keys.isdisjoint(row))
            self.assertEqual(4, len(row["bbox"]))
            self.assertGreaterEqual(row["score"], -1.0)
            self.assertLessEqual(row["score"], 1.0)
        self.assertTrue(GROUND_TRUTH_PATH.exists())
        ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            "sealed_posttraining_independent_test", ground_truth["status"]
        )
        self.assertEqual(
            sha256(PREANNOTATION_PATH),
            ground_truth["source_preannotation"]["sha256"],
        )

    def test_models_are_read_only_and_report_is_reproducible(self):
        self.assertEqual(
            self.report["production_model_hashes_before"],
            self.report["production_model_hashes_after"],
        )
        for filename in MODEL_FILES:
            expected = self.report["production_model_hashes_before"][filename]
            self.assertEqual(expected["sha256"], sha256(MODEL_DIR / filename))
            self.assertEqual(expected["bytes"], (MODEL_DIR / filename).stat().st_size)
        regenerated = generate()
        self.assertEqual(self.report, regenerated)
        self.assertEqual(MARKDOWN_PATH.read_text(encoding="utf-8"), render_markdown(regenerated))

    def test_training_data_remains_isolated(self):
        training = json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            [f"new_ui_{index}.png" for index in range(1, 6)],
            sorted(training["images"]),
        )
        self.assertEqual(
            81,
            sum(len(image["avatars"]) for image in training["images"].values()),
        )
        self.assertNotEqual(FIXTURE_DIR, TRAINING_FIXTURE_DIR)
        training_source = TRAINING_SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("lesson_independent_v2", training_source)
        self.assertNotIn("independent_test_preannotations_v2", training_source)

    def test_markdown_contains_full_review_format(self):
        markdown = MARKDOWN_PATH.read_text(encoding="utf-8")
        self.assertIn("pending_user_review", markdown)
        self.assertIn("不是人工真值", markdown)
        self.assertIn("[灰框]", markdown)
        self.assertIn("[已选择]", markdown)
        self.assertIn("[低分差]", markdown)
        self.assertIn("其余均正确", markdown)
        self.assertEqual(11, markdown.count("## MuMu-20260806-"))


if __name__ == "__main__":
    unittest.main()
