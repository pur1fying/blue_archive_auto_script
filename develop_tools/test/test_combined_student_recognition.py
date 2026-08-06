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
    / "yolox_mobilenetv3_wikiru270_top1"
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

    def test_frozen_comparison_is_reported_but_non_blocking(self):
        result = self.report["independent_v1"]
        metrics = result["metrics"]
        self.assertEqual(40, metrics["detected_card_count"])
        self.assertEqual(83, metrics["detected_avatar_count"])
        self.assertEqual(71, metrics["identity_correct"])
        self.assertEqual(82, metrics["eligibility_correct"])
        self.assertEqual(62, metrics["eligible_click_passed"])
        self.assertEqual(1, metrics["gray_target_clicked"])
        self.assertFalse(result["promotion"]["passed"])
        self.assertFalse(result["promotion"]["blocks_completion"])
        self.assertTrue(self.report["completed"])
        aru = next(
            row
            for row in result["instances"]
            if row["image"] == "MuMu-20260731-235521-485.png"
            and row["display_location"] == "6-1"
        )
        self.assertEqual("Hanako (Swimsuit)", aru["top1_name"])
        self.assertFalse(aru["expected_target_click_passed"])

    def test_all_270_students_have_exclusive_evidence_categories(self):
        capability = self.report["catalog_capability"]
        self.assertEqual(
            {"correct": 55, "error": 9, "uncertain": 206},
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
        self.assertEqual(270, len(set().union(*categories)))
        self.assertEqual(270, self.report["architecture"]["catalog_identity_count"])
        self.assertEqual(270, self.report["architecture"]["gallery_identity_count"])
        for name in (
            "Ibuki (Swimsuit)",
            "Iroha (Swimsuit)",
            "Satsuki (Swimsuit)",
            "Chiaki (Swimsuit)",
            "Makoto (Swimsuit)",
        ):
            row = next(item for item in capability["students"] if item["name"] == name)
            self.assertEqual("uncertain", row["category"])
            self.assertEqual("wikiru_only", row["support_status"])
        self.assertEqual(
            {
                "Aru",
                "Kanna (Swimsuit)",
                "Kotori (Cheer Squad)",
                "Marina",
                "Mimori (Swimsuit)",
                "Neru",
                "Nozomi",
                "Sena (Casual)",
                "Shokuhou Misaki",
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
        self.assertTrue(self.report["training_action"]["performed"])
        self.assertEqual(20260801, self.report["training_action"]["selected_seed"])

    def test_pre_wikiru_comparison_contains_all_instances(self):
        comparison = self.report["comparison_to_pre_wikiru270"]
        self.assertEqual(83, len(comparison["instances"]))
        self.assertEqual(11, len(comparison["changed_instances"]))
        self.assertEqual(-4, comparison["metrics"]["identity_correct"]["delta"])
        self.assertEqual(-3, comparison["metrics"]["eligible_click_passed"]["delta"])
        self.assertEqual(0, comparison["metrics"]["eligibility_correct"]["delta"])

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
