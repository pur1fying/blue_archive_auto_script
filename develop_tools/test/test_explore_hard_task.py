"""Interactive hard-stage route test.

Run from the repository root with an emulator already running:

    uv run --no-sync python -m unittest develop_tools.test.test_explore_hard_task

The stages come from ``explore_hard_task_list`` in the selected config and are
forced to run even when they have already been completed.
"""

import unittest

from core.config.config_set import ConfigSet
from main import Main
from module.explore_tasks.explore_task import explore_hard_task

TEST_CONFIG_DIR = "cn"


class TestExploreHardTask(unittest.TestCase):
    def setUp(self):
        self.main = Main(ocr_needed=["en-us"])
        self.baas_thread = self.main.get_thread(
            ConfigSet(config_dir=TEST_CONFIG_DIR),
            name="explore-hard-test",
        )
        self.assertTrue(
            self.baas_thread.init_all_data(),
            f"Failed to initialize BAAS test config: {TEST_CONFIG_DIR}",
        )

    def tearDown(self):
        self.baas_thread.flag_run = False
        if self.main.ocr is not None:
            self.main.ocr.client.stop_server()

    def test_explore_hard_task(self):
        self.assertTrue(
            explore_hard_task(
                self.baas_thread,
                force=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
