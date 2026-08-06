import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODELS_PATH = ROOT / "develop_tools" / "student_recognition" / "models.py"
TRAINING_PATH = ROOT / "develop_tools" / "student_recognition" / "train_student_models.py"
ATTRIBUTION_PATH = ROOT / "develop_tools" / "student_recognition" / "pretrained_classifier_attribution.json"
RUNNER_PATH = ROOT / "develop_tools" / "student_recognition" / "train_pretrained_classifier.py"
CANDIDATE_DIR = ROOT / "develop_tools" / "student_recognition" / "experiments" / "pretrained_classifier"
REPORT_PATH = ROOT / "develop_tools" / "student_recognition" / "pretrained_classifier_experiment_report.json"


class PretrainedStudentClassifierTest(unittest.TestCase):
    def test_experiment_uses_torchvision_imagenet_weights(self):
        source = MODELS_PATH.read_text(encoding="utf-8")
        self.assertIn("MobileNet_V3_Small_Weights.IMAGENET1K_V1", source)
        self.assertIn("mobilenet_v3_small", source)
        ast.parse(source)

    def test_runner_keeps_independent_data_out_of_training(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("lesson_independent_v1", source)
        self.assertNotIn("independent_test_annotations_v1", source)
        self.assertIn("PretrainedMobileNetV3StudentEncoder", source)
        self.assertIn("training._train_student_encoder =", source)
        self.assertIn("frozen_backbone_epochs", source)
        ast.parse(source)
        ast.parse(TRAINING_PATH.read_text(encoding="utf-8"))

    def test_mature_network_source_is_attributed(self):
        attribution = json.loads(ATTRIBUTION_PATH.read_text(encoding="utf-8"))
        self.assertEqual("BSD-3-Clause", attribution["license"])
        self.assertEqual("0.20.1+cu124", attribution["package_version"])
        self.assertFalse(attribution["runtime_dependency_added"])

    def test_exported_candidate_and_frozen_result_are_explicit(self):
        metadata = json.loads((CANDIDATE_DIR / "student_encoder.json").read_text(encoding="utf-8"))
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual("torchvision-MobileNetV3-Small-ImageNet1K-V1", metadata["architecture"])
        self.assertEqual(265, metadata["gallery_identity_count"])
        self.assertEqual(74, metadata["cross_validation_metrics"]["correct"])
        self.assertEqual(75, report["metrics"]["identity_correct"])
        self.assertEqual(64, report["metrics"]["eligible_click_passed"])
        self.assertFalse(report["promotion"]["passed"])
        self.assertFalse(report["promotion"]["checks"]["pink_click_target_met"])
        self.assertLessEqual(report["performance"]["p95_ms"], 500.0)


if __name__ == "__main__":
    unittest.main()
