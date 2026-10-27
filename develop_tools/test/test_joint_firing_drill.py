import runpy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from core import image, position


ROOT = Path(__file__).resolve().parents[2]


class JointFiringDrillTest(unittest.TestCase):
    def test_cn_quick_battle_dialog_is_recognized(self):
        self.check_dialog("sweep-menu", "cn_drill_sweep_title.png", (560, 165, 715, 225))

    def test_cn_quick_battle_confirmation_is_recognized(self):
        self.check_dialog("start-sweep-notice", "cn_drill_sweep_notice.png", (560, 130, 720, 200))

    def check_dialog(self, feature, fixture, area):
        # Real 2560x1440 screenshot, cropped to the title only (1280x720 coordinates).
        title = cv2.imread(str(Path(__file__).with_name("fixtures") / fixture))
        self.assertIsNotNone(title)
        coordinates = runpy.run_path(str(ROOT / "src/images/CN/x_y_range/joint_firing_drill.py"))
        template = cv2.imread(str(ROOT / "src/images/CN/joint_firing_drill" / (feature + ".png")))

        name = "drill_" + feature
        with patch.dict(position.image_dic, {"CN": {name: template}}), patch.dict(
            position.image_x_y_range, {"CN": {"drill": coordinates["x_y_range"]}}
        ):
            for ratio in (1, 2):
                with self.subTest(ratio=ratio):
                    screenshot = np.zeros((720 * ratio, 1280 * ratio, 3), dtype=np.uint8)
                    screenshot[area[1] * ratio:area[3] * ratio, area[0] * ratio:area[2] * ratio] = cv2.resize(
                        title, ((area[2] - area[0]) * ratio, (area[3] - area[1]) * ratio),
                        interpolation=cv2.INTER_AREA,
                    )
                    thread = SimpleNamespace(identifier="CN", ratio=ratio, latest_img_array=screenshot)
                    self.assertTrue(image.compare_image(thread, name))


if __name__ == "__main__":
    unittest.main()
