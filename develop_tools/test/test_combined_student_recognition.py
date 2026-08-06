import ast
import json
import unittest
from pathlib import Path

from develop_tools.student_recognition.evaluate_combined_top1 import build_report


ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
CANDIDATE_DIR = (
    ROOT
    / "develop_tools"
    / "student_recognition"
    / "experiments"
    / "yolox_mobilenetv3_top1"
)
REPORT_PATH = ROOT / "develop_tools" / "student_recognition" / "combined_top1_report.json"
MARKDOWN_PATH = ROOT / "develop_tools" / "student_recognition" / "combined_top1_report.md"
EVALUATOR_PATH = ROOT / "develop_tools" / "student_recognition" / "evaluate_combined_top1.py"


class CombinedStudentRecognitionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_candidate_is_exactly_promoted(self):
        for name in (
            "lesson_locator.onnx",
            "lesson_locator.json",
            "student_encoder.onnx",
            "student_encoder.json",
            "gallery.npz",
        ):
            self.assertEqual(
                (CANDIDATE_DIR / name).read_bytes(),
                (MODEL_DIR / name).read_bytes(),
                name,
            )

    def test_top1_policy_has_no_similarity_gate(self):
        metadata = json.loads((MODEL_DIR / "student_encoder.json").read_text(encoding="utf-8"))
        self.assertNotIn("similarity_threshold", metadata)
        self.assertEqual("valid_global_top1", metadata["identity_click_policy"])
        recognizer_source = (
            ROOT / "core" / "student_recognition" / "recognizer.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("similarity_threshold", recognizer_source)
        ast.parse(recognizer_source)

    def test_training_replay_is_complete(self):
        metrics = self.report["training_replay"]["metrics"]
        self.assertEqual(39, metrics["detected_card_count"])
        self.assertEqual(81, metrics["detected_avatar_count"])
        self.assertEqual(81, metrics["identity_correct"])
        self.assertEqual(71, metrics["pink_click_passed"])
        self.assertEqual(10, metrics["gray_blocked"])
        self.assertEqual(65, metrics["click_passed_student_count"])
        self.assertEqual(9, metrics["gray_only_student_count"])

    def test_frozen_comparison_meets_predeclared_targets(self):
        result = self.report["independent_v1"]
        metrics = result["metrics"]
        self.assertEqual(40, metrics["detected_card_count"])
        self.assertEqual(83, metrics["detected_avatar_count"])
        self.assertEqual(75, metrics["identity_correct"])
        self.assertEqual(82, metrics["eligibility_correct"])
        self.assertEqual(65, metrics["eligible_click_passed"])
        self.assertEqual(1, metrics["gray_target_clicked"])
        self.assertTrue(result["promotion"]["passed"])
        aru = next(
            row
            for row in result["instances"]
            if row["image"] == "MuMu-20260731-235521-485.png"
            and row["display_location"] == "6-1"
        )
        self.assertEqual("Aru", aru["top1_name"])
        self.assertTrue(aru["expected_target_click_passed"])

    def test_all_265_students_have_exclusive_evidence_categories(self):
        capability = self.report["catalog_capability"]
        self.assertEqual(
            {"correct": 56, "error": 7, "uncertain": 202},
            capability["counts"],
        )
        categories = [
            set(capability["correct"]),
            set(capability["error"]),
            set(capability["uncertain"]),
        ]
        self.assertFalse(categories[0] & categories[1])
        self.assertFalse(categories[0] & categories[2])
        self.assertFalse(categories[1] & categories[2])
        self.assertEqual(265, len(set().union(*categories)))
        self.assertEqual(
            {
                "Kirino (Swimsuit)",
                "Kotori (Cheer Squad)",
                "Marina",
                "Michiru",
                "Mimori (Swimsuit)",
                "Neru",
                "Sena (Casual)",
            },
            set(capability["error"]),
        )

    def test_independent_data_remains_excluded(self):
        isolation = self.report["data_isolation"]
        self.assertFalse(isolation["independent_v1_in_training"])
        self.assertTrue(
            set(isolation["training_fixture_names"]).isdisjoint(
                isolation["independent_fixture_names"]
            )
        )
        training_source = (
            ROOT / "develop_tools" / "student_recognition" / "train_student_models.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("lesson_independent_v1", training_source)
        self.assertNotIn("independent_test_annotations_v1", training_source)
        self.assertFalse(self.report["training_action"]["performed"])

    def test_report_is_reproducible_and_human_readable(self):
        regenerated = build_report(MODEL_DIR, benchmark_runs=1)
        self.assertEqual(
            self.report["training_replay"]["metrics"],
            regenerated["training_replay"]["metrics"],
        )
        self.assertEqual(
            self.report["independent_v1"]["metrics"],
            regenerated["independent_v1"]["metrics"],
        )
        markdown = MARKDOWN_PATH.read_text(encoding="utf-8")
        self.assertIn("Kotori (Cheer Squad)", markdown)
        self.assertIn("YOLOX-Nano", markdown)
        self.assertIn("MobileNetV3", markdown)


if __name__ == "__main__":
    unittest.main()
