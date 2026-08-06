import json
import tempfile
import unittest
from pathlib import Path

import cv2

from core.student_recognition.lesson_locator import LessonLocator
from develop_tools.student_recognition.export_yolox_lesson_dataset import (
    CATEGORIES,
    EXPECTED_IMAGES,
    export_dataset,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "develop_tools" / "student_recognition" / "experiments" / "yolox_locator"
TRAINING_FIXTURE_DIR = ROOT / "develop_tools" / "test" / "fixtures" / "lesson"
TRAINING_ANNOTATION_PATH = ROOT / "develop_tools" / "student_recognition" / "lesson_locator_annotations.json"
REPORT_PATH = ROOT / "develop_tools" / "student_recognition" / "yolox_locator_experiment_report.json"


class YoloXLessonDatasetTest(unittest.TestCase):
    def test_export_contains_only_original_training_groups(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "dataset"
            manifest = export_dataset(output, augmentations_per_image=1)
            self.assertEqual(list(EXPECTED_IMAGES), manifest["source_images"])
            self.assertEqual(39, manifest["original_card_count"])
            self.assertEqual(81, manifest["original_avatar_count"])
            self.assertFalse(manifest["independent_comparison_data_included"])
            train = json.loads(
                (output / "annotations" / "instances_train2017.json").read_text(encoding="utf-8")
            )
            self.assertEqual(list(CATEGORIES), train["categories"])
            self.assertEqual(10, len(train["images"]))
            names = {image["file_name"] for image in train["images"]}
            self.assertTrue(set(EXPECTED_IMAGES).issubset(names))
            self.assertFalse(any(name.startswith("MuMu-") for name in names))

    def test_validation_fold_excludes_entire_original_group(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "dataset"
            held_out = "new_ui_3.png"
            manifest = export_dataset(
                output,
                validation_image=held_out,
                augmentations_per_image=2,
            )
            train = json.loads(
                (output / "annotations" / "instances_train2017.json").read_text(encoding="utf-8")
            )
            validation = json.loads(
                (output / "annotations" / "instances_val2017.json").read_text(encoding="utf-8")
            )
            train_names = {image["file_name"] for image in train["images"]}
            self.assertFalse(any(name.startswith("new_ui_3") for name in train_names))
            self.assertEqual([held_out], [image["file_name"] for image in validation["images"]])
            self.assertEqual(12, manifest["training_image_count"])

    def test_opencv_candidate_replays_all_training_boxes_and_statuses(self):
        annotation = json.loads(TRAINING_ANNOTATION_PATH.read_text(encoding="utf-8"))
        locator = LessonLocator(CANDIDATE_DIR)
        detected_cards = detected_avatars = detected_eligible = 0
        for image_name in EXPECTED_IMAGES:
            cards = locator.locate(cv2.imread(str(TRAINING_FIXTURE_DIR / image_name)))
            self.assertEqual("onnx", locator.last_backend)
            detected_cards += len(cards)
            detected_avatars += sum(len(card.avatars) for card in cards)
            detected_eligible += sum(
                avatar.eligible for card in cards for avatar in card.avatars
            )
        self.assertEqual(39, detected_cards)
        self.assertEqual(81, detected_avatars)
        self.assertEqual(71, detected_eligible)

    def test_frozen_comparison_report_passes_promotion_gate(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual("frozen_comparison_candidate", report["classification"])
        self.assertTrue(report["promotion"]["passed"])
        self.assertEqual(40, report["metrics"]["detected_card_count"])
        self.assertEqual(83, report["metrics"]["detected_avatar_count"])
        self.assertEqual(67, report["metrics"]["identity_correct"])
        self.assertEqual(82, report["metrics"]["eligibility_correct"])
        self.assertEqual(58, report["metrics"]["eligible_click_passed"])
        self.assertEqual(0, report["metrics"]["gray_target_clicked"])
        self.assertLessEqual(report["performance"]["p95_ms"], 500.0)


if __name__ == "__main__":
    unittest.main()
