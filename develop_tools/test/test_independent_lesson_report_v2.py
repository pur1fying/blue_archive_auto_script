import hashlib
import json
import unittest
from pathlib import Path

from develop_tools.student_recognition.evaluate_independent_test_v2 import (
    MODEL_FILES,
    evaluate,
    render_markdown,
)
from develop_tools.student_recognition.finalize_independent_v2_annotations import (
    GRAY_CORRECTIONS,
    IDENTITY_CORRECTIONS,
    generate as generate_annotations,
)


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "develop_tools" / "student_recognition"
ANNOTATION_PATH = DATA_DIR / "independent_test_annotations_v2.json"
PREANNOTATION_PATH = DATA_DIR / "independent_test_preannotations_v2.json"
REPORT_PATH = DATA_DIR / "independent_test_report_v2.json"
MARKDOWN_PATH = DATA_DIR / "independent_test_report_v2.md"
TRAINING_ANNOTATION_PATH = DATA_DIR / "lesson_locator_annotations.json"
TRAINING_SCRIPT_PATH = DATA_DIR / "train_student_models.py"
MODEL_DIR = ROOT / "src" / "models" / "student_recognition"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IndependentLessonReportV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.annotation = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.truth = {
            (image["file"], row["location"]): row
            for image in cls.annotation["images"]
            for row in image["instances"]
        }
        cls.rows = cls.report["instances"]

    def test_ground_truth_is_complete_and_user_confirmed(self):
        self.assertEqual(
            "sealed_posttraining_independent_test", self.annotation["status"]
        )
        self.assertEqual(11, len(self.annotation["images"]))
        self.assertEqual(
            86,
            sum(len(image["card_bboxes"]) for image in self.annotation["images"]),
        )
        self.assertEqual(182, len(self.truth))
        self.assertEqual(
            7,
            sum(
                len(image["selected_card_indices"])
                for image in self.annotation["images"]
            ),
        )
        self.assertEqual(
            sha256(PREANNOTATION_PATH),
            self.annotation["source_preannotation"]["sha256"],
        )
        self.assertFalse(self.annotation["data_policy"]["included_in_training"])
        self.assertFalse(self.annotation["data_policy"]["included_in_gallery"])
        self.assertFalse(
            self.annotation["data_policy"]["used_for_model_or_threshold_selection"]
        )

    def test_all_manual_corrections_are_materialized(self):
        for key, expected_name in IDENTITY_CORRECTIONS.items():
            self.assertEqual(expected_name, self.truth[key]["name"], key)
        for key in GRAY_CORRECTIONS:
            self.assertFalse(self.truth[key]["eligible"], key)
        corrected = self.annotation["manual_corrections"][
            "confirmed_position_correction"
        ]
        self.assertEqual("7-3", corrected["submitted_display_location"])
        self.assertEqual("7-2", corrected["confirmed_display_location"])
        self.assertEqual(
            "Sena (Casual)",
            self.truth[("MuMu-20260806-231311-941.png", "6:1")]["name"],
        )
        self.assertNotIn(
            ("MuMu-20260806-231311-941.png", "6:2"), self.truth
        )

    def test_fixed_formal_metrics(self):
        self.assertTrue(self.report["completed"])
        counts = self.report["counts"]
        expected = {
            "images": 11,
            "cards": 86,
            "avatars": 182,
            "selected_cards": 7,
            "available_avatars": 164,
            "selected_avatars": 18,
            "available_pink": 137,
            "available_gray": 27,
            "selected_pink": 17,
            "selected_gray": 1,
            "identity_correct": 178,
            "available_identity_correct": 164,
            "selected_identity_correct": 14,
            "eligibility_correct": 175,
            "available_eligibility_correct": 157,
            "selected_eligibility_correct": 18,
            "available_gray_false_positive": 7,
            "available_pink_false_negative": 0,
            "available_pink_click_passed": 137,
            "available_pink_click_failed": 0,
            "available_gray_blocked": 20,
            "available_gray_click_risks": 7,
            "selected_source_blocked": 18,
            "selected_source_clicks": 0,
            "wrong_card_clicks": 0,
            "identity_error_wrong_clicks": 0,
        }
        self.assertEqual(expected, counts)
        self.assertAlmostEqual(178 / 182, self.report["metrics"]["identity"]["all"]["accuracy"])
        self.assertAlmostEqual(175 / 182, self.report["metrics"]["eligibility"]["all"]["accuracy"])

    def test_identity_errors_are_selected_and_cannot_click(self):
        failures = self.report["identity_failures"]
        self.assertEqual(4, len(failures))
        self.assertEqual(
            {
                (filename, location, expected_name)
                for (filename, location), expected_name in IDENTITY_CORRECTIONS.items()
            },
            {
                (row["image"], row["location"], row["expected_name"])
                for row in failures
            },
        )
        for row in failures:
            self.assertEqual("selected", row["card_state"])
            self.assertFalse(row["simulated_source_card_clicked"])
            self.assertFalse(row["identity_error_wrong_click"])
        self.assertFalse(self.report["identity_error_wrong_clicks"])

    def test_available_pink_path_is_perfect(self):
        rows = [
            row
            for row in self.rows
            if row["card_state"] == "available" and row["expected_eligible"]
        ]
        self.assertEqual(137, len(rows))
        for row in rows:
            self.assertTrue(row["identity_correct"], row["display_location"])
            self.assertTrue(row["predicted_eligible"], row["display_location"])
            self.assertTrue(
                row["simulated_source_card_clicked"], row["display_location"]
            )
            self.assertFalse(row["wrong_card_click"])
        self.assertFalse(self.report["available_pink_click_failures"])
        self.assertFalse(self.report["wrong_card_clicks"])

    def test_seven_gray_false_positives_are_explicit(self):
        expected = GRAY_CORRECTIONS
        risks = self.report["available_gray_click_risks"]
        self.assertEqual(7, len(risks))
        self.assertEqual(
            expected,
            {(row["image"], row["location"]) for row in risks},
        )
        self.assertEqual(risks, self.report["available_eligibility_failures"])
        for row in risks:
            self.assertFalse(row["expected_eligible"])
            self.assertTrue(row["predicted_eligible"])
            self.assertTrue(row["simulated_source_card_clicked"])

    def test_all_selected_sources_are_blocked(self):
        selected = [row for row in self.rows if row["card_state"] == "selected"]
        self.assertEqual(18, len(selected))
        for row in selected:
            self.assertTrue(row["selected_source_blocked"])
            self.assertFalse(row["simulated_source_card_clicked"])
        self.assertFalse(self.report["selected_source_clicks"])

    def test_artifacts_are_read_only_and_regenerable(self):
        hashes = self.report["artifact_hashes"]
        self.assertEqual(
            hashes["production_models_before"], hashes["production_models_after"]
        )
        self.assertEqual(
            hashes["protected_files_before"], hashes["protected_files_after"]
        )
        for filename in MODEL_FILES:
            self.assertEqual(
                hashes["production_models_before"][filename]["sha256"],
                sha256(MODEL_DIR / filename),
            )
        self.assertEqual(self.annotation, generate_annotations())
        regenerated = evaluate()
        self.assertEqual(self.report, regenerated)
        self.assertEqual(
            MARKDOWN_PATH.read_text(encoding="utf-8"), render_markdown(regenerated)
        )

    def test_v2_remains_outside_training(self):
        training = json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            [f"new_ui_{index}.png" for index in range(1, 6)],
            sorted(training["images"]),
        )
        self.assertEqual(
            81,
            sum(len(image["avatars"]) for image in training["images"].values()),
        )
        training_source = TRAINING_SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("lesson_independent_v2", training_source)
        self.assertNotIn("independent_test_annotations_v2", training_source)

    def test_markdown_exposes_failures_and_all_instances(self):
        markdown = MARKDOWN_PATH.read_text(encoding="utf-8")
        self.assertIn("普通状态身份：164/164", markdown)
        self.assertIn("普通彩框正确卡片：137/137", markdown)
        self.assertIn("普通灰框正确阻止：20/27", markdown)
        self.assertIn("Sumire (Part-Timer)", markdown)
        self.assertIn("Ui (Swimsuit)", markdown)
        self.assertIn("Sena (Casual)", markdown)
        full_instance_table = markdown.split("## 全部头像", 1)[1]
        self.assertEqual(182, full_instance_table.count("| MuMu-20260806-"))


if __name__ == "__main__":
    unittest.main()
