"""Regression tests for the Global tactical challenge shop catalog and config migration.

Run from the repository root with::

    python -m unittest develop_tools.test.test_global_tactical_challenge_shop
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from core.config.config_set import ConfigSet
from core.config.default_config import DEFAULT_CONFIG, STATIC_DEFAULT_CONFIG
from core.config.generated_static_config import StaticConfig
from gui.components.expand.arenaShopPriority import Layout
from gui.fragments.switch import SwitchFragment


class GlobalTacticalChallengeShopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.static_config = StaticConfig(**json.loads(STATIC_DEFAULT_CONFIG))
        self.static_patch = patch.object(ConfigSet, "static_config", self.static_config)
        self.static_patch.start()
        self.addCleanup(self.static_patch.stop)

    def write_config(self, goods, server="国际服"):
        config = json.loads(DEFAULT_CONFIG)
        config["server"] = server
        config["TacticalChallengeShopList"] = goods
        config["TacticalChallengeShopRefreshTime"] = "3"
        self.config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        return config

    def load_config(self):
        return ConfigSet(self.temp_dir.name)

    def test_global_catalog_contains_seven_students_in_game_order(self):
        goods = self.static_config.tactical_challenge_shop_price_list["Global"]
        self.assertEqual(goods[:3], [["30AP", 15], ["60AP", 30], ["美游神明文字x5", 50]])
        self.assertEqual(len(goods), 17)
        self.assertEqual(
            [name for name, _ in goods[3:9]],
            ["宫子神明文字x5", "静子神明文字x5", "真白神明文字x5",
             "纱绫神明文字x5", "风香神明文字x5", "歌原神明文字x5"],
        )

    def test_each_legacy_selection_keeps_its_item(self):
        # Old positions: six students, two AP items, eight supplies.
        new_positions = [3, 4, 5, 6, 7, 8, 0, 1, 9, 10, 11, 12, 13, 14, 15, 16]
        for old_index, new_index in enumerate(new_positions):
            with self.subTest(old_index=old_index):
                goods = [0] * 16
                goods[old_index] = 1
                self.write_config(goods)
                actual = self.load_config().config.TacticalChallengeShopList
                expected = [0] * 17
                expected[new_index] = 1
                self.assertEqual(actual, expected)

    def test_global_server_variants_migrate(self):
        for server in ("国际服", "国际服青少年", "韩国ONE", "Steam国际服"):
            with self.subTest(server=server):
                self.write_config([0] * 6 + [1, 1] + [0] * 8, server)
                actual = self.load_config().config.TacticalChallengeShopList
                self.assertEqual(actual, [1, 1] + [0] * 15)

    def test_migration_is_saved_and_only_changes_shop_selection(self):
        original = self.write_config([0] * 6 + [1, 1] + [0] * 8)
        self.load_config()
        saved = json.loads(self.config_path.read_text(encoding="utf-8"))
        original["TacticalChallengeShopList"] = [1, 1] + [0] * 15
        self.assertEqual(saved, original)
        with patch.object(ConfigSet, "save") as save:
            reloaded = self.load_config()
            self.assertEqual(reloaded.config.TacticalChallengeShopList, original["TacticalChallengeShopList"])
            save.assert_not_called()

    def test_current_miyu_selection_is_not_migrated_again(self):
        goods = [0, 0, 1] + [0] * 14
        self.write_config(goods)
        with patch.object(ConfigSet, "save") as save:
            self.assertEqual(self.load_config().config.TacticalChallengeShopList, goods)
            save.assert_not_called()

    def test_cn_and_jp_configs_are_unchanged(self):
        for server in ("官服", "B服", "日服", "日服PC端"):
            with self.subTest(server=server):
                goods = [1] * 16
                self.write_config(goods, server)
                with patch.object(ConfigSet, "save") as save:
                    self.assertEqual(self.load_config().config.TacticalChallengeShopList, goods)
                    save.assert_not_called()

    def test_new_global_config_keeps_all_items_unselected(self):
        self.write_config(json.loads(DEFAULT_CONFIG)["TacticalChallengeShopList"])
        config = self.load_config()
        SwitchFragment._tactical_challenge_shop_config_update(SimpleNamespace(config=config))
        self.assertEqual(config.config.TacticalChallengeShopList, [0] * 17)

    def test_shop_panel_uses_migrated_selection(self):
        self.write_config([0] * 6 + [1, 1] + [0] * 8)
        config = self.load_config()
        SwitchFragment._tactical_challenge_shop_config_update(SimpleNamespace(config=config))
        panel = Layout(config=config)
        try:
            self.assertEqual(panel.goods_count, 17)
            self.assertEqual(panel.price_list[2], ["美游神明文字x5", 50])
            self.assertEqual(panel.goods, [1, 1] + [0] * 15)
        finally:
            panel.close()
            panel.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
