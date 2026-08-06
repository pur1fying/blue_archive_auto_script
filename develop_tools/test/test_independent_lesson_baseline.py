import hashlib
import json
import unittest
from pathlib import Path

from core.config.default_config import STATIC_DEFAULT_CONFIG
from core.student_recognition.catalog import StudentCatalog
from develop_tools.student_recognition.evaluate_independent_test import evaluate


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson_independent_v1"
TRAINING_FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
ANNOTATION_PATH = ROOT / "develop_tools" / "student_recognition" / "independent_test_annotations_v1.json"
TRAINING_ANNOTATION_PATH = ROOT / "develop_tools" / "student_recognition" / "lesson_locator_annotations.json"
REPORT_PATH = ROOT / "develop_tools" / "student_recognition" / "independent_test_report_v1.json"
EXPERIMENT_BASELINE_PATH = ROOT / "develop_tools" / "student_recognition" / "experiment_baseline_v1.json"
TRAINING_SCRIPT_PATH = ROOT / "develop_tools" / "student_recognition" / "train_student_models.py"
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
YOLOX_REPORT_PATH = ROOT / "develop_tools" / "student_recognition" / "yolox_locator_experiment_report.json"
COMBINED_REPORT_PATH = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "combined_top1_alpha_balanced_report.json"
)
PROMOTED_MODEL_FILES = {
    "src/models/student_recognition/lesson_locator.onnx",
    "src/models/student_recognition/lesson_locator.json",
    "src/models/student_recognition/student_encoder.onnx",
    "src/models/student_recognition/student_encoder.json",
    "src/models/student_recognition/gallery.npz",
    "develop_tools/student_recognition/train_student_models.py",
    "develop_tools/student_recognition/validation_report.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IndependentLessonBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.instances = [
            instance
            for image in cls.annotation["images"]
            for instance in image["instances"]
        ]

    def test_sealed_fixtures_and_ground_truth_are_complete(self):
        self.assertEqual("sealed_pretraining_independent_baseline", self.annotation["status"])
        self.assertEqual(5, len(self.annotation["images"]))
        self.assertEqual(40, sum(len(image["card_bboxes"]) for image in self.annotation["images"]))
        self.assertEqual(83, len(self.instances))
        self.assertEqual(70, sum(instance["eligible"] for instance in self.instances))
        self.assertEqual(13, sum(not instance["eligible"] for instance in self.instances))
        self.assertEqual(
            sorted(image["file"] for image in self.annotation["images"]),
            sorted(path.name for path in FIXTURE_DIR.glob("*.png")),
        )
        catalog = StudentCatalog(json.loads(STATIC_DEFAULT_CONFIG)["student_names"])
        for image in self.annotation["images"]:
            self.assertEqual(image["sha256"], sha256(FIXTURE_DIR / image["file"]))
            self.assertEqual(
                len(image["instances"]),
                len({instance["location"] for instance in image["instances"]}),
            )
            for instance in image["instances"]:
                self.assertIsNotNone(catalog.resolve(instance["name"]), instance["name"])

    def test_manual_corrections_are_fully_materialized(self):
        ground_truth = {
            (image["file"], instance["location"]): (
                instance["name"],
                instance["eligible"],
            )
            for image in self.annotation["images"]
            for instance in image["instances"]
        }
        expected_corrections = {
            ("MuMu-20260731-235301-451.png", "0:1"): ("Shokuhou Misaki", True),
            ("MuMu-20260731-235301-451.png", "5:1"): ("Ako (Dress)", True),
            ("MuMu-20260731-235301-451.png", "6:0"): ("Kotori (Cheer Squad)", True),
            ("MuMu-20260731-235521-485.png", "0:0"): ("Mimori (Swimsuit)", False),
            ("MuMu-20260731-235521-485.png", "1:2"): ("Izuna (Swimsuit)", True),
            ("MuMu-20260731-235521-485.png", "4:0"): ("Kanna (Swimsuit)", False),
            ("MuMu-20260731-235521-485.png", "4:1"): ("Shokuhou Misaki", True),
            ("MuMu-20260731-235521-485.png", "5:0"): ("Aru", True),
            ("MuMu-20260731-235327-036.png", "0:1"): ("Kirino (Swimsuit)", True),
            ("MuMu-20260731-235327-036.png", "1:1"): ("Aru", True),
            ("MuMu-20260731-235327-036.png", "3:0"): ("Michiru", True),
            ("MuMu-20260731-235327-036.png", "6:0"): ("Mimori (Swimsuit)", False),
            ("MuMu-20260731-235327-036.png", "6:1"): ("Sena (Casual)", False),
            ("MuMu-20260731-235327-036.png", "7:1"): ("Marina", False),
            ("MuMu-20260801-074740-652.png", "1:0"): ("Koyuki", True),
            ("MuMu-20260801-074740-652.png", "2:1"): ("Saten Ruiko", True),
            ("MuMu-20260801-074740-652.png", "5:1"): ("Shokuhou Misaki", True),
            ("MuMu-20260801-074754-624.png", "6:1"): ("Kotori (Cheer Squad)", True),
        }
        for location, expected in expected_corrections.items():
            self.assertEqual(expected, ground_truth[location], location)

    def test_baseline_metrics_and_failures_are_explicit(self):
        self.assertTrue(self.report["completed"])
        metrics = self.report["metrics"]
        expected = {
            "image_count": 5,
            "card_count": 40,
            "detected_card_count": 40,
            "avatar_count": 83,
            "detected_avatar_count": 83,
            "eligible_count": 70,
            "plain_count": 13,
            "identity_correct": 66,
            "eligible_identity_correct": 57,
            "plain_identity_correct": 9,
            "eligibility_correct": 81,
            "eligible_false_positive": 2,
            "eligible_false_negative": 0,
            "eligible_click_passed": 57,
            "eligible_click_failed": 13,
            "gray_target_blocked": 12,
            "gray_target_clicked": 1,
        }
        for key, value in expected.items():
            self.assertEqual(value, metrics[key], key)
        self.assertAlmostEqual(66 / 83, metrics["identity_top1_accuracy"])
        self.assertAlmostEqual(81 / 83, metrics["eligibility_accuracy"])
        self.assertEqual(17, len(self.report["identity_failures"]))
        self.assertEqual(2, len(self.report["eligibility_failures"]))
        self.assertEqual(13, len(self.report["eligible_click_failures"]))
        self.assertEqual(1, len(self.report["gray_target_clicks"]))
        self.assertEqual(
            {
                ("MuMu-20260731-235521-485.png", "1-1", "Mimori (Swimsuit)"),
                ("MuMu-20260731-235521-485.png", "5-1", "Kanna (Swimsuit)"),
            },
            {
                (row["image"], row["display_location"], row["expected_name"])
                for row in self.report["eligibility_failures"]
            },
        )

    def test_independent_data_is_not_a_training_input(self):
        training_annotation = json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))
        training_images = sorted(training_annotation["images"])
        independent_images = sorted(image["file"] for image in self.annotation["images"])
        self.assertEqual(
            [f"new_ui_{index}.png" for index in range(1, 6)],
            training_images,
        )
        self.assertEqual(
            81,
            sum(len(image["avatars"]) for image in training_annotation["images"].values()),
        )
        self.assertTrue(set(training_images).isdisjoint(independent_images))
        self.assertNotEqual(FIXTURE_DIR, TRAINING_FIXTURE_DIR)
        training_source = TRAINING_SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("lesson_independent_v1", training_source)
        self.assertNotIn("independent_test_annotations_v1", training_source)
        self.assertFalse(self.report["data_policy"]["included_in_training"])

    def test_historical_report_remains_immutable_after_model_promotion(self):
        before = self.report["artifact_hashes"]["protected_files_before"]
        after = self.report["artifact_hashes"]["protected_files_after"]
        self.assertEqual(before, after)
        for relative_path, expected_hash in before.items():
            if relative_path in PROMOTED_MODEL_FILES:
                continue
            self.assertEqual(expected_hash, sha256(ROOT / relative_path), relative_path)

    def test_candidate_evaluator_uses_an_explicit_model_directory(self):
        candidate = evaluate(
            model_dir=MODEL_DIR,
            enforce_expected_baseline=False,
            candidate_name="baseline-as-candidate",
        )
        self.assertTrue(candidate["completed"])
        self.assertEqual("frozen_comparison_candidate", candidate["classification"])
        self.assertEqual("baseline-as-candidate", candidate["candidate_name"])
        self.assertIsNone(candidate["expected_baseline"])
        combined_report = json.loads(COMBINED_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(combined_report["independent_v1"]["metrics"], candidate["metrics"])
        self.assertEqual("valid_global_top1", candidate["environment"]["identity_click_policy"])

    def test_experiment_baseline_locks_data_and_model_hashes(self):
        baseline = json.loads(EXPERIMENT_BASELINE_PATH.read_text(encoding="utf-8"))
        self.assertEqual("050840e5450689d8d7c5739352ef49492839d9e4", baseline["baseline_commit"])
        self.assertFalse(
            baseline["data_policy"]["frozen_comparison_may_be_used_for_training"]
        )
        self.assertFalse(
            baseline["data_policy"]["frozen_comparison_may_be_used_for_threshold_selection"]
        )
        for relative_path, expected_hash in baseline["sha256"].items():
            if relative_path in PROMOTED_MODEL_FILES:
                self.assertEqual(
                    expected_hash,
                    self.report["artifact_hashes"]["protected_files_before"][relative_path],
                    relative_path,
                )
            else:
                self.assertEqual(expected_hash, sha256(ROOT / relative_path), relative_path)


if __name__ == "__main__":
    unittest.main()
