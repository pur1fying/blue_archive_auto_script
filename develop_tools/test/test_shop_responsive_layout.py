"""Regression tests for the PR2 shop / cafe configuration editors.

Run from the repository root with::

    python -m unittest develop_tools.test.test_shop_responsive_layout

The legacy suite targeted the old flow-layout shop editor (variable column
count, ShopRefreshBox, dialog-level ScrollArea). PR2 replaces that editor
with a fixed four-column GoodsCard grid inside a ShopPanel with internal
scrolling, so these assertions are rewritten against the new contract while
keeping the file name and run command unchanged.
"""

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QBoxLayout, QLabel, QWidget

from gui.components.expand import arenaShopPriority, shopPriority
from gui.components.expand.cafeInvite import Layout as CafeLayout
from gui.components.expand.shop_panel import estimate_common_shop_daily
from gui.components.shop_goods import (
    GRID_COLUMNS,
    GRID_H_SPACING,
    MIN_COL_W,
    SHOP_MAX_WIDTH,
    GoodsCard,
    ShopGoodCard,
    ShopGoodsGrid,
)
from gui.util.customized_ui import DialogSettingBox

_HORIZONTAL_CHROME = 48
_SCREEN_MARGIN = 64


class _Config:
    server_mode = "CN"

    def __init__(self, *, common_goods=None, arena_goods=None):
        common_goods = common_goods or []
        arena_goods = arena_goods or []
        self.static_config = SimpleNamespace(
            common_shop_price_list={self.server_mode: common_goods},
            tactical_challenge_shop_price_list={self.server_mode: arena_goods},
            student_names=[],
        )
        self.values = {
            "CommonShopList": [0] * len(common_goods),
            "CommonShopRefreshTime": 0,
            "TacticalChallengeShopList": [0] * len(arena_goods),
            "TacticalChallengeShopRefreshTime": 0,
        }

    def get(self, key=None, default=None, **kwargs):
        if key is None:
            key = kwargs.get("key")
        return self.values.get(key, default)

    def set(self, key=None, value=None, **kwargs):
        if key is None:
            key = kwargs.get("key")
        self.values[key] = value


class ShopAndCafeLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widgets = []

    def tearDown(self):
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

    # ------------------------------------------------------------------
    # shop_goods exports
    # ------------------------------------------------------------------

    def test_legacy_import_name_still_resolves(self):
        # ShopGoodCard is kept purely as an import-compatibility alias for
        # the new GoodsCard API; old positional signatures are gone.
        self.assertIs(ShopGoodCard, GoodsCard)

    def test_category_color_hook_returns_defaults(self):
        from gui.components.shop_goods import get_category_colors

        colors = get_category_colors()
        self.assertIn("default", colors)
        self.assertIsInstance(colors, dict)

    # ------------------------------------------------------------------
    # GoodsCard
    # ------------------------------------------------------------------

    def test_goods_card_click_toggles_selection_overlay(self):
        card = self._show(GoodsCard(2, "Item name", "125000"), 220, 120)
        events = []
        card.toggled.connect(lambda index, checked: events.append((index, checked)))

        self.assertFalse(card.is_checked())
        self.assertFalse(card._selection_frame.isVisible())

        QTest.mouseClick(card, Qt.LeftButton, pos=card.rect().center())
        self.app.processEvents()
        self.assertTrue(card.is_checked())
        self.assertTrue(card._selection_frame.isVisible())
        self.assertEqual([(2, True)], events)

        QTest.mouseClick(card, Qt.LeftButton, pos=card.rect().center())
        self.app.processEvents()
        self.assertFalse(card.is_checked())
        self.assertFalse(card._selection_frame.isVisible())
        self.assertEqual([(2, True), (2, False)], events)

    def test_long_names_wrap_without_fixed_height(self):
        long_name = "Random Intermediate Material 美游神明文字x5 상급 활동 보고서 x3"
        card = GoodsCard(0, long_name, "50")
        self.assertTrue(card.name_lbl.wordWrap())
        single_line = QFontMetrics(card.name_lbl.font()).height()
        self.assertGreater(card.name_lbl.heightForWidth(80), single_line)

    # ------------------------------------------------------------------
    # ShopGoodsGrid: always four columns
    # ------------------------------------------------------------------

    def test_grid_keeps_four_columns_at_any_width(self):
        grid = ShopGoodsGrid()
        grid.set_cards([GoodsCard(i, f"Item {i}", "50") for i in range(8)])
        self._show(grid, 800, 600)

        def column_count():
            return len({card.geometry().x() for card in grid.cards()})

        self.assertEqual(GRID_COLUMNS, column_count())

        grid.resize(500, 600)
        self.app.processEvents()
        self.assertEqual(GRID_COLUMNS, column_count())

        minimum = GRID_COLUMNS * MIN_COL_W + GRID_H_SPACING * (GRID_COLUMNS - 1)
        self.assertGreaterEqual(grid.minimumSizeHint().width(), minimum)

    # ------------------------------------------------------------------
    # ShopPanel refresh input must match the executor's limit
    # ------------------------------------------------------------------

    def test_refresh_commit_is_clamped_to_three(self):
        config = _Config(common_goods=[["Advanced Report", 25, "creditpoints"]])
        editor = self._show(shopPriority.Layout(config=config), 800)

        editor.refresh_input.setText("9")
        editor.refresh_input.editingFinished.emit()
        self.app.processEvents()
        self.assertEqual("3", editor.refresh_input.text())
        self.assertEqual(3, config.get("CommonShopRefreshTime"))

        arena_config = _Config(arena_goods=[["Mashiro's Eleph", 50]])
        arena_editor = self._show(arenaShopPriority.Layout(config=arena_config), 800)
        arena_editor.refresh_input.setText("7")
        arena_editor.refresh_input.editingFinished.emit()
        self.app.processEvents()
        self.assertEqual("3", arena_editor.refresh_input.text())
        self.assertEqual(3, arena_config.get("TacticalChallengeShopRefreshTime"))

    def test_estimate_matches_runtime_refresh_prices(self):
        dummy = SimpleNamespace(tr=lambda text: text)

        # No refresh, credit-only: plain total with the unit, no detail line.
        title, detail = estimate_common_shop_daily(
            dummy, [1], 0, [["Credit Item", 100, "creditpoints"]]
        )
        self.assertIn("100", title)
        self.assertIn("信用点", title)
        self.assertEqual("", detail)

        # Refreshing costs pyroxene even when only credit items are picked,
        # so the detail line must surface 40 + 60 + 80.
        title, detail = estimate_common_shop_daily(
            dummy, [1], 3, [["Credit Item", 100, "creditpoints"]]
        )
        self.assertIn("400", title)
        self.assertIn("180", detail)

        # Pyroxene goods: item total x rounds plus the same refresh costs,
        # never the removed 100 / 120 tiers.
        _, detail = estimate_common_shop_daily(
            dummy, [1], 3, [["Report", 50, "pyroxene"]]
        )
        self.assertIn("380", detail)

        # Requests beyond the runtime cap are clamped, not extrapolated.
        clamped = estimate_common_shop_daily(
            dummy, [1], 9, [["Report", 50, "pyroxene"]]
        )
        self.assertEqual(clamped, estimate_common_shop_daily(
            dummy, [1], 3, [["Report", 50, "pyroxene"]]
        ))

    def test_checking_goods_updates_estimate_label(self):
        config = _Config(common_goods=[["Credit Item", 100, "creditpoints"]])
        editor = self._show(shopPriority.Layout(config=config), 800)

        editor.cards[0].set_checked(True)
        editor.refresh_input.setText("3")
        editor.refresh_input.editingFinished.emit()
        self.app.processEvents()

        self.assertIn("400", editor.estimate_label.text())
        self.assertEqual([1], config.get("CommonShopList"))

    # ------------------------------------------------------------------
    # DialogSettingBox sizing
    # ------------------------------------------------------------------

    def _expected_content_width(self, dialog, parent, lower, upper):
        available = dialog._available_geometry(parent)
        limit = min(parent.width(), available.width()) - _HORIZONTAL_CHROME - _SCREEN_MARGIN
        return max(lower, min(upper, limit))

    def test_shop_dialog_width_follows_viewport_formula(self):
        config = _Config(arena_goods=[[f"Item {index}", 50] for index in range(8)])
        parent = self._show(QWidget(), 640, 600)
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

        minimum = GRID_COLUMNS * MIN_COL_W + GRID_H_SPACING * (GRID_COLUMNS - 1)
        expected = self._expected_content_width(dialog, parent, minimum, SHOP_MAX_WIDTH)
        self.assertEqual(expected + _HORIZONTAL_CHROME, dialog.widget.width())

    def test_cafe_dialog_reaches_narrow_vertical_mode(self):
        narrow_parent = self._show(QWidget(), 600, 700)
        narrow_cafe = CafeLayout(config=_Config())
        narrow_dialog = self._show(
            DialogSettingBox(
                narrow_parent,
                narrow_cafe.config,
                narrow_cafe,
                setting_name="cafeinvite",
            ),
            narrow_parent.width(),
            narrow_parent.height(),
        )

        expected = self._expected_content_width(narrow_dialog, narrow_parent, 480, 820)
        self.assertEqual(expected + _HORIZONTAL_CHROME, narrow_dialog.widget.width())
        # The content must be able to drop below the 640 px breakpoint so
        # the cafe layout can actually switch to its vertical arrangement.
        self.assertLess(expected, 640)
        self.assertEqual(QBoxLayout.TopToBottom, narrow_cafe.root_layout.direction())

        wide_parent = self._show(QWidget(), 1200, 800)
        wide_cafe = CafeLayout(config=_Config())
        wide_dialog = self._show(
            DialogSettingBox(
                wide_parent,
                wide_cafe.config,
                wide_cafe,
                setting_name="cafeinvite",
            ),
            wide_parent.width(),
            wide_parent.height(),
        )
        self.assertGreater(wide_dialog.widget.width(), narrow_dialog.widget.width())
        self.assertEqual(QBoxLayout.LeftToRight, wide_cafe.root_layout.direction())

    def test_cafe_titles_follow_palette(self):
        cafe = CafeLayout(config=_Config())
        self.widgets.append(cafe)

        left_title = next(
            label for label in cafe.findChildren(QLabel) if label.text() == "通用设置"
        )
        self.assertIn("palette(text)", left_title.styleSheet())
        self.assertNotIn("#1a1a1a", left_title.styleSheet())

        # card1 is active by default -> palette(text); card2 starts inactive
        # -> palette(placeholder-text). Both must stay palette-driven, never
        # a hard-coded dark hex that becomes unreadable on dark themes.
        self.assertIn("palette(text)", cafe.card1.title_lbl.styleSheet())
        self.assertNotIn("#1a1a1a", cafe.card1.title_lbl.styleSheet())
        self.assertIn("palette(placeholder-text)", cafe.card2.title_lbl.styleSheet())
        self.assertNotIn("#1a1a1a", cafe.card2.title_lbl.styleSheet())


if __name__ == "__main__":
    unittest.main()
