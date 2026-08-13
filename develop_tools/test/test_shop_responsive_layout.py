"""Regression tests for the responsive legacy-GUI shop editors.

Run from the repository root with::

    python -m unittest develop_tools.test.test_shop_responsive_layout
"""

import os
import importlib
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QStyle,
    QStyleOptionButton,
    QWidget,
)
from qfluentwidgets import ScrollArea

from gui.components.expand import arenaShopPriority, shopPriority
from gui.util.customized_ui import DialogSettingBox


class _Config:
    server_mode = "CN"

    def __init__(self, *, common_goods=None, arena_goods=None):
        common_goods = common_goods or []
        arena_goods = arena_goods or []
        self.static_config = SimpleNamespace(
            common_shop_price_list={self.server_mode: common_goods},
            tactical_challenge_shop_price_list={self.server_mode: arena_goods},
        )
        self.values = {
            "CommonShopList": [0] * len(common_goods),
            "CommonShopRefreshTime": 0,
            "TacticalChallengeShopList": [0] * len(arena_goods),
            "TacticalChallengeShopRefreshTime": 0,
        }

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class ShopResponsiveLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._shop_tr = shopPriority.bt.tr
        self._arena_tr = arenaShopPriority.bt.tr
        shopPriority.bt.tr = lambda _context, text: text
        arenaShopPriority.bt.tr = lambda _context, text: text
        self.widgets = []

    def tearDown(self):
        shopPriority.bt.tr = self._shop_tr
        arenaShopPriority.bt.tr = self._arena_tr
        for widget in reversed(self.widgets):
            widget.close()
            widget.deleteLater()
        self.app.processEvents()

    def _show(self, widget, width, height=900):
        self.widgets.append(widget)
        widget.resize(width, height)
        widget.show()
        self.app.processEvents()
        return widget

    @staticmethod
    def _column_count(editor):
        return len({box.parentWidget().geometry().x() for box in editor.boxes})

    def test_shared_shop_components_live_in_the_components_package(self):
        shop_goods = importlib.import_module("gui.components.shop_goods")

        self.assertTrue(hasattr(shop_goods, "ShopGoodsGrid"))
        self.assertTrue(hasattr(shop_goods, "ShopGoodCard"))

    def test_refresh_control_occupies_the_full_content_row(self):
        config = _Config(common_goods=[["Advanced Report", 25, "creditpoints"]])
        editor = self._show(shopPriority.Layout(config=config), 800)

        refresh_box = editor.findChild(QWidget, "shopRefreshBox")

        self.assertIsNotNone(refresh_box)
        self.assertGreaterEqual(refresh_box.width(), editor.contentsRect().width() - 40)

    def test_each_good_is_rendered_as_a_distinct_card(self):
        config = _Config(arena_goods=[["Mashiro's Eleph", 50]])
        editor = self._show(arenaShopPriority.Layout(config=config), 500)

        card = editor.boxes[0].parentWidget()

        self.assertIsInstance(card, QFrame)
        self.assertEqual(QFrame.StyledPanel, card.frameShape())
        self.assertEqual("shopGoodCard", card.objectName())
        check_box = editor.boxes[0]
        option = QStyleOptionButton()
        option.initFrom(check_box)
        indicator_rect = check_box.style().subElementRect(
            QStyle.SE_CheckBoxIndicator, option, check_box
        )
        indicator_right = check_box.geometry().left() + indicator_rect.right()
        self.assertLessEqual(card.rect().right() - indicator_right, 10)

    def test_clicking_a_good_card_toggles_its_checkbox_and_config(self):
        config = _Config(arena_goods=[["Mashiro's Eleph", 50]])
        editor = self._show(arenaShopPriority.Layout(config=config), 500)
        card = editor.boxes[0].parentWidget()

        QTest.mouseClick(card, Qt.LeftButton, pos=card.rect().center())
        self.app.processEvents()

        self.assertTrue(editor.boxes[0].isChecked())
        self.assertEqual([1], config.get("TacticalChallengeShopList"))

        QTest.mouseClick(editor.boxes[0], Qt.LeftButton)
        self.app.processEvents()
        self.assertFalse(editor.boxes[0].isChecked())

    def test_goods_reflow_and_long_translations_wrap_without_fixed_item_height(self):
        names = [
            "Random Intermediate Material",
            "Advanced Activity Report x3",
            "Mashiro's Eleph",
            "Shizuko's Eleph",
            "Miyako's Eleph",
            "美游神明文字x5",
            "상급 활동 보고서 x3",
            "中級素材（ランダム）",
        ]
        config = _Config(arena_goods=[[name, 50] for name in names])
        editor = self._show(arenaShopPriority.Layout(config=config), 800)

        self.assertEqual(3, self._column_count(editor))

        editor.resize(500, 1200)
        self.app.processEvents()
        self.assertEqual(2, self._column_count(editor))

        long_label = next(
            label for label in editor.findChildren(QLabel)
            if label.text() == "Random Intermediate Material"
        )
        self.assertTrue(long_label.wordWrap())
        self.assertGreater(long_label.height(), long_label.fontMetrics().height())

        last_item = editor.boxes[-1].parentWidget()
        goods_host = last_item.parentWidget()
        self.assertLessEqual(last_item.geometry().bottom(), goods_host.contentsRect().bottom())

    def test_shop_dialog_width_tracks_the_available_application_width(self):
        config = _Config(arena_goods=[[f"Item {index}", 50] for index in range(8)])

        narrow_parent = self._show(QWidget(), 640, 600)
        narrow_editor = arenaShopPriority.Layout(config=config)
        narrow_dialog = self._show(
            DialogSettingBox(
                narrow_parent,
                config,
                narrow_editor,
                setting_name="arenaShopPriority",
            ),
            narrow_parent.width(),
            narrow_parent.height(),
        )
        narrow_scroll = narrow_dialog.findChild(ScrollArea)

        wide_parent = self._show(QWidget(), 1200, 800)
        wide_editor = arenaShopPriority.Layout(config=config)
        wide_dialog = self._show(
            DialogSettingBox(
                wide_parent,
                config,
                wide_editor,
                setting_name="arenaShopPriority",
            ),
            wide_parent.width(),
            wide_parent.height(),
        )
        wide_scroll = wide_dialog.findChild(ScrollArea)

        self.assertLessEqual(narrow_scroll.width(), narrow_parent.width() - 48)
        self.assertGreater(wide_scroll.width(), narrow_scroll.width())

    def test_shop_dialog_height_does_not_overflow_a_short_application_window(self):
        config = _Config(arena_goods=[[f"Item {index}", 50] for index in range(8)])
        parent = self._show(QWidget(), 640, 300)
        dialog = self._show(
            DialogSettingBox(
                parent,
                config,
                arenaShopPriority.Layout(config=config),
                setting_name="arenaShopPriority",
            ),
            parent.width(),
            parent.height(),
        )
        scroll = dialog.findChild(ScrollArea)

        self.assertLessEqual(scroll.height(), parent.height() - 180)
        self.assertGreater(scroll.verticalScrollBar().maximum(), 0)


if __name__ == "__main__":
    unittest.main()
