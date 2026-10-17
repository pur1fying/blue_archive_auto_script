from pathlib import Path
import sys
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from core import position
from module.shop import shop_utils
from service.shop_compat import detect_cn_shop_items, install_shop_compat, track_cn_shop_swipe
from service.shop_compat import _catalog_at_top, reset_cn_shop_catalog


@pytest.fixture(autouse=True)
def preserve_shop_hooks(monkeypatch):
    for name in ("get_item_position", "swipe_get_y_diff", "buy"):
        monkeypatch.setattr(shop_utils, name, getattr(shop_utils, name))
    for name in ("module.shop.common_shop", "module.shop.tactical_challenge_shop"):
        module = sys.modules.get(name)
        if module is not None and hasattr(module, "buy"):
            monkeypatch.setattr(module, "buy", module.buy)


@pytest.fixture
def coins(monkeypatch):
    folder = Path(__file__).resolve().parents[2] / "src/images/CN/shop"
    values = {f"shop_{path.stem}": cv2.imread(str(path)) for path in folder.glob("coin-type*.png")}
    monkeypatch.setattr(position, "image_dic", {"CN": values})
    return values


def _shop(coins, ratio=1, columns=(0, 1, 2, 3), available=True, currency="creditpoints", include_coin=True):
    screenshot = np.full((720, 1280, 3), 240, dtype=np.uint8)
    suffix = "bright" if available else "grey"
    template = coins[f"shop_coin-type-{currency}-{suffix}"]
    for y in (300, 550):
        for column in columns:
            x = shop_utils.SHOP_ITEM_ROW_X["CN"][column]
            screenshot[y:y + 50, x - 14:x + 110] = (250, 221, 119) if available else (174, 150, 78)
            if include_coin:
                height, width = template.shape[:2]
                left = x - 23
                screenshot[y - 2:y - 2 + height, left:left + width] = template
    screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
    return SimpleNamespace(latest_img_array=screenshot, ratio=ratio, identifier="CN", server="CN")


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("available", [True, False])
def test_shifted_currency_glyph_preserves_four_columns_and_state(coins, ratio, available):
    items, rows = detect_cn_shop_items(_shop(coins, ratio=ratio, available=available))
    assert [count for _, count in rows] == [4, 4]
    assert [item[0][0] for item in items] == [0, 1, 2, 3] * 2
    assert all(item[1] is available and item[2] == "creditpoints" for item in items)


def test_blue_buttons_without_currency_are_not_items_and_missing_columns_keep_indices(coins):
    assert detect_cn_shop_items(_shop(coins, include_coin=False)) == ([], [])
    items, rows = detect_cn_shop_items(_shop(coins, columns=(0, 2)))
    assert [count for _, count in rows] == [2, 2]
    assert [item[0][0] for item in items] == [0, 2, 0, 2]


def test_detected_grid_selects_only_configured_purchase_indices(coins, monkeypatch):
    context = _shop(coins)
    context.logger = SimpleNamespace(info=lambda message: None, warning=lambda message: None)
    selected = []
    configured = np.array([True, False, False, True, False, True, False, False])
    monkeypatch.setattr(shop_utils, "get_item_position", detect_cn_shop_items)
    monkeypatch.setattr(shop_utils, "ensure_choose", lambda context, items: selected.extend(items))
    monkeypatch.setattr(shop_utils, "swipe_get_y_diff", lambda *args: pytest.fail("All required items are visible"))
    shop_utils.buy(context, configured)
    assert [(item[0][0], item[0][1] > 400) for item in selected] == [(0, False), (3, False), (1, True)]
    assert configured.tolist() == [True, False, False, True, False, True, False, False]


def _swipe_context(difference, failures=0):
    before = np.random.default_rng(82).integers(0, 256, (720, 1280, 3), dtype=np.uint8)
    after = np.full_like(before, 240)
    after[:720 - difference] = before[difference:]
    context = SimpleNamespace(latest_img_array=before, ratio=1, identifier="CN", is_android_device=True)
    context.swipes = []
    context.swipe = lambda *args, **kwargs: context.swipes.append((args, kwargs))
    context.update_screenshot_array = lambda: setattr(
        context, "latest_img_array", before if len(context.swipes) <= failures else after
    )
    return context


def test_swipe_tracking_uses_rich_visible_product_identity():
    assert track_cn_shop_swipe(_swipe_context(100), [(305, 4), (555, 4)]) == 100


def test_clipped_row_uses_next_visible_identity_without_negative_slice_or_opencv_assertion():
    assert track_cn_shop_swipe(_swipe_context(100), [(167, 4)]) == 100


def test_swipe_tracking_does_not_report_success_without_motion():
    with pytest.raises(RuntimeError, match="did not scroll"):
        track_cn_shop_swipe(_swipe_context(0), [(417, 4)])


def test_swipe_retries_once_inside_catalog_and_verifies_motion():
    context = _swipe_context(100, failures=1)
    assert track_cn_shop_swipe(context, [(417, 4)]) == 100
    assert len(context.swipes) == 2
    assert all(args == (1000, 337, 1000, 237) and kwargs["duration"] == 0.8
               for args, kwargs in context.swipes)


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_catalog_reset_verifies_top_before_item_selection(monkeypatch, ratio):
    from core import image
    from service import shop_compat

    monkeypatch.setattr(image, "compare_image", lambda context, name: True)
    monkeypatch.setattr(shop_compat, "detect_cn_shop_items", lambda *args: ([], [(305, 4)]))
    before = np.full((round(720 * ratio), round(1280 * ratio), 3), 240, dtype=np.uint8)
    after = before.copy()
    for y in (145, 155, 165):
        after[int(y * ratio), int(1236 * ratio)] = (91, 84, 73)
    context = SimpleNamespace(latest_img_array=before, ratio=ratio, swipes=[])
    context.swipe = lambda *args, **kwargs: context.swipes.append((args, kwargs))
    context.update_screenshot_array = lambda: setattr(context, "latest_img_array", after if context.swipes else before)
    assert not _catalog_at_top(context)
    reset_cn_shop_catalog(context)
    assert _catalog_at_top(context)
    assert context.swipes[0][0] == (1000, 225, 1000, 405)


def test_catalog_top_probes_cannot_accept_popup_and_reset_is_bounded(monkeypatch):
    from core import image
    from service import shop_compat, shop_tracking

    context = SimpleNamespace(latest_img_array=np.full((720, 1280, 3), (91, 84, 73), dtype=np.uint8),
                              ratio=1, swipes=[])
    context.swipe = lambda *args, **kwargs: context.swipes.append(args)
    context.update_screenshot_array = lambda: None
    monkeypatch.setattr(image, "compare_image", lambda context, name: False)
    assert not _catalog_at_top(context)
    with pytest.raises(RuntimeError, match="shop page is not visible"):
        reset_cn_shop_catalog(context)
    assert not context.swipes
    context.latest_img_array[:] = 240
    monkeypatch.setattr(image, "compare_image", lambda context, name: True)
    monkeypatch.setattr(shop_compat, "detect_cn_shop_items", lambda *args: ([], [(305, 4)]))
    monkeypatch.setattr(shop_tracking, "estimate_cn_shop_translation", lambda *args, **kwargs: -100)
    with pytest.raises(RuntimeError, match="Cannot verify the top"):
        reset_cn_shop_catalog(context)
    assert len(context.swipes) == 8


def test_uncertain_movement_is_not_retried_with_old_identity():
    context = _swipe_context(700)
    with pytest.raises(RuntimeError, match="Cannot uniquely verify shop"):
        track_cn_shop_swipe(context, [(555, 4)])
    assert len(context.swipes) == 1


def test_incomplete_row_stops_before_later_purchase_indices_shift(coins):
    context = _shop(coins, columns=(0, 2))
    install_shop_compat()
    with pytest.raises(RuntimeError, match="Incomplete CN shop row"):
        shop_utils.get_item_position(context)


def test_clipped_checked_row_cannot_shift_later_configured_purchase_indices(monkeypatch):
    from service import shop_compat

    pages = iter([
        ([((column, y), True, "creditpoints") for y in (305, 555) for column in range(4)],
         [(305, 4), (555, 4)]),
        ([((column, 129), True, "creditpoints") for column in range(3)]
         + [((column, 371), True, "creditpoints") for column in range(4)], [(129, 3), (371, 4)]),
    ])
    monkeypatch.setattr(shop_compat, "detect_cn_shop_items", lambda *args: next(pages))
    monkeypatch.setattr(shop_compat, "reset_cn_shop_catalog", lambda *args: None)
    monkeypatch.setattr(shop_compat, "track_cn_shop_swipe", lambda *args: 434)
    selected = []
    monkeypatch.setattr(shop_utils, "ensure_choose", lambda context, items: selected.extend(items))
    install_shop_compat()
    context = SimpleNamespace(identifier="CN", logger=SimpleNamespace(info=lambda message: None,
                                                                     warning=lambda message: None))
    configured = np.array([False] * 8 + [True, False, False, True])
    shop_utils.buy(context, configured)
    assert [item[0] for item in selected] == [(0, 371), (3, 371)]


def test_patch_is_cn_only_and_does_not_change_purchase_configuration(monkeypatch):
    original_items = lambda context, shop_type="common_shop": ("legacy", shop_type)
    original_swipe = lambda context, rows: 17
    original_buy = lambda context, values, shop_type="common_shop": values
    monkeypatch.setattr(shop_utils, "get_item_position", original_items)
    monkeypatch.setattr(shop_utils, "swipe_get_y_diff", original_swipe)
    monkeypatch.setattr(shop_utils, "buy", original_buy)
    common = SimpleNamespace(buy=original_buy)
    custom = lambda *args: None
    tactical = SimpleNamespace(buy=custom)
    monkeypatch.setitem(sys.modules, "module.shop.common_shop", common)
    monkeypatch.setitem(sys.modules, "module.shop.tactical_challenge_shop", tactical)
    install_shop_compat()
    wrapped = shop_utils.get_item_position
    install_shop_compat()
    assert shop_utils.get_item_position is wrapped
    assert common.buy is shop_utils.buy
    assert tactical.buy is custom
    context = SimpleNamespace(identifier="JP", config=SimpleNamespace(CommonShopList=[True, False]))
    assert shop_utils.get_item_position(context) == ("legacy", "common_shop")
    assert shop_utils.swipe_get_y_diff(context, []) == 17
    assert shop_utils.buy(context, context.config.CommonShopList) == [True, False]
    assert context.config.CommonShopList == [True, False]
