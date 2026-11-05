"""Service-only compatibility for the current CN shop layout."""

from __future__ import annotations

from functools import wraps


def _trace(context, stage, **details):
    import os

    directory = os.getenv("BAAS_SHOP_TRACE_DIR")
    if not directory:
        return
    import json
    from pathlib import Path
    import time
    import cv2

    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{time.time_ns()}-{stage}.png"
    cv2.imwrite(str(path), context.latest_img_array)
    with (destination / "tracking.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"stage": stage, "image": str(path), **details}) + "\n")


def _catalog_at_top(context):
    from core import color, image

    return bool(image.compare_image(context, "shop_menu")) and all(
        color.rgb_in_range(context, 1236, y, 53, 93, 64, 104, 71, 111)
        for y in (145, 155, 165)
    )


def reset_cn_shop_catalog(context, shop_type="common_shop"):
    from core import image
    from service.shop_tracking import estimate_cn_shop_translation

    context.update_screenshot_array()
    for attempt in range(9):
        if _catalog_at_top(context):
            return
        if not image.compare_image(context, "shop_menu"):
            raise RuntimeError("Cannot reset shop catalog: the shop page is not visible.")
        if attempt == 8:
            break
        _, rows = detect_cn_shop_items(context, shop_type)
        candidates = [y for y, _ in rows if y >= 292]
        if not candidates:
            raise RuntimeError("Cannot reset shop catalog without a visible product identity.")
        start = max(220, min(390, candidates[0] - 80))
        before = context.latest_img_array.copy()
        _trace(context, "reset-before", attempt=attempt)
        context.swipe(1000, start, 1000, start + 180, duration=1.0, post_sleep_time=0.6)
        context.update_screenshot_array()
        details = []
        movement = estimate_cn_shop_translation(before, context.latest_img_array, rows,
                                                 context.ratio, diagnostics=details,
                                                 movement_bounds=(-220, 1))
        at_top = _catalog_at_top(context)
        _trace(context, "reset-after", attempt=attempt, at_top=at_top,
               identity_movement=movement, matches=details)
        if not at_top and (movement is None or movement >= -1):
            raise RuntimeError("Cannot verify movement toward the top of the shop catalog.")
    raise RuntimeError("Cannot verify the top of the shop catalog; item selection was not started.")


def detect_cn_shop_items(context, shop_type="common_shop"):
    from core import color, image
    from module.shop.shop_utils import SHOP_ITEM_ROW_X

    currencies = {"common_shop": ("creditpoints", "pyroxene"),
                  "tactical_challenge_shop": ("tactical-coin",)}[shop_type]
    states, rows = [], []
    for column, x in enumerate(SHOP_ITEM_ROW_X["CN"]):
        y = 127
        while y <= 560:
            purchasable = None
            for available, limits in ((True, (99, 139, 211, 231, 245, 255)),
                                      (False, (68, 88, 140, 160, 164, 184))):
                if any(color.rgb_in_range(context, x + dx, y, *limits) for dx in range(-6, 7)):
                    purchasable = available
                    break
            if purchasable is None:
                y += 1
                continue
            suffix = "bright" if purchasable else "grey"
            # The currency glyph has moved up to nine pixels left of the old ROI.
            area = (x - 24, y - 25, x + 60, y + 60)
            currency = next((value for value in currencies if image.search_in_area(
                context, f"shop_coin-type-{value}-{suffix}", area=area, threshold=0.8
            )), None)
            if currency is None:
                y += 1
                continue
            for index, (row_y, count) in enumerate(rows):
                if abs(y - row_y) <= 5:
                    rows[index] = (row_y, count + 1)
                    break
            else:
                row_y = y
                rows.append((row_y, 1))
            states.append(((column, row_y), purchasable, currency))
            y += 70
    return sorted(states, key=lambda item: (item[0][1], item[0][0])), sorted(rows)


def track_cn_shop_swipe(context, item_lines_y):
    from service.shop_tracking import estimate_cn_shop_translation

    if not item_lines_y:
        raise RuntimeError("Cannot track shop scrolling without a detected item row.")
    before = context.latest_img_array.copy()
    start = max(260, min(500, item_lines_y[-1][0] - 80))
    for attempt in range(2):
        _trace(context, "scroll-before", attempt=attempt, rows=item_lines_y)
        context.swipe(1000, start, 1000, start - 100, duration=0.8, post_sleep_time=0.6)
        context.update_screenshot_array()
        details = []
        difference = estimate_cn_shop_translation(before, context.latest_img_array, item_lines_y,
                                                   context.ratio, diagnostics=details,
                                                   movement_bounds=(-1, 120))
        _trace(context, "scroll-after", attempt=attempt, difference=difference, matches=details)
        if difference is None:
            raise RuntimeError("Cannot uniquely verify shop item positions after scrolling; item selection stopped.")
        if difference >= 2:
            return difference
        if difference < -1:
            raise RuntimeError("Shop scrolled in the wrong direction; item selection was stopped.")
    raise RuntimeError("Shop did not scroll or its previous row was not found; stopping before item indices can drift.")


def install_shop_compat() -> None:
    import sys

    from module.shop import shop_utils

    original_items = shop_utils.get_item_position
    if getattr(original_items, "_baas_shop_compat", False):
        return
    original_swipe = shop_utils.swipe_get_y_diff
    original_buy = shop_utils.buy

    @wraps(original_items)
    def get_item_position(context, shop_type="common_shop"):
        if context.identifier == "CN":
            items, rows = detect_cn_shop_items(context, shop_type)
            # Existing selection logic also excludes pay rows <=252: their
            # product checkbox/image is clipped above the catalog viewport.
            rows = [(y, count) for y, count in rows if y > 252]
            items = [item for item in items if item[0][1] > 252]
            if not rows or any(count != 4 for _, count in rows):
                raise RuntimeError("Incomplete CN shop row; stopping before purchase indices can drift.")
            return items, rows
        return original_items(context, shop_type)

    @wraps(original_swipe)
    def swipe_get_y_diff(context, item_lines_y):
        if context.identifier == "CN":
            return track_cn_shop_swipe(context, item_lines_y)
        return original_swipe(context, item_lines_y)

    @wraps(original_buy)
    def buy(context, buy_list, shop_type="common_shop"):
        if context.identifier == "CN":
            reset_cn_shop_catalog(context, shop_type)
        return original_buy(context, buy_list, shop_type)

    get_item_position._baas_shop_compat = True
    shop_utils.get_item_position = get_item_position
    shop_utils.swipe_get_y_diff = swipe_get_y_diff
    shop_utils.buy = buy
    for module_name in ("module.shop.common_shop", "module.shop.tactical_challenge_shop"):
        module = sys.modules.get(module_name)
        if module is not None and getattr(module, "buy", None) is original_buy:
            module.buy = buy
