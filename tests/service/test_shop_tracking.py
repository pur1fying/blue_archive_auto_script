from __future__ import annotations

import cv2
import numpy as np
import pytest

from service.shop_tracking import estimate_cn_shop_translation


def _frames(offset=120, columns=(0, 1, 2, 3), brightness=0):
    before = np.full((720, 1280, 3), 225, dtype=np.uint8)
    after = np.full_like(before, 225)
    random = np.random.default_rng(41)
    for column in range(4):
        left = 640 + column * 150
        product = random.integers(20, 230, (145, 120, 3), dtype=np.uint8)
        before[390:535, left:left + 120] = product
        if column in columns:
            target = np.clip(product.astype(np.int16) + brightness, 0, 255).astype(np.uint8)
            after[390 - offset:535 - offset, left:left + 120] = target
    return before, after


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_product_identity_translation_requires_distinct_columns_at_screen_ratios(ratio):
    before, after = _frames(columns=(0, 2))
    if ratio != 1:
        size = (round(1280 * ratio), round(720 * ratio))
        before, after = cv2.resize(before, size), cv2.resize(after, size)
    assert estimate_cn_shop_translation(before, after, [(555, 4)], ratio) == pytest.approx(120)


def test_one_matching_column_does_not_establish_catalog_position():
    assert estimate_cn_shop_translation(*_frames(columns=(2,)), [(555, 4)]) is None


def test_missing_products_and_generic_blank_cards_are_rejected():
    before, after = _frames(columns=())
    assert estimate_cn_shop_translation(before, after, [(555, 4)]) is None
    assert estimate_cn_shop_translation(after, after, [(555, 4)]) is None


def test_original_rgb_limit_is_preserved_despite_high_correlation():
    before, after = _frames(brightness=-35)
    assert estimate_cn_shop_translation(before, after, [(555, 4)]) is None


def test_duplicate_product_rows_are_ambiguous():
    before, after = _frames(offset=220)
    for column in range(4):
        left = 640 + column * 150
        after[400:545, left:left + 120] = before[390:535, left:left + 120]
    assert estimate_cn_shop_translation(before, after, [(555, 4)]) is None


def test_two_disagreeing_column_groups_are_rejected():
    before, after = _frames()
    for column in (2, 3):
        left = 640 + column * 150
        after[270:415, left:left + 120] = 225
        after[370:515, left:left + 120] = before[390:535, left:left + 120]
    assert estimate_cn_shop_translation(before, after, [(555, 4)]) is None


@pytest.mark.parametrize("offset", [0, -50])
def test_stationary_or_reverse_movement_keeps_its_sign(offset):
    assert estimate_cn_shop_translation(*_frames(offset), [(555, 4)]) == offset


def test_known_short_gesture_excludes_other_repeated_row_before_peak_selection():
    before, after = _frames(offset=65)
    for column in range(4):
        left = 640 + column * 150
        after[150:295, left:left + 120] = before[390:535, left:left + 120]
    assert estimate_cn_shop_translation(before, after, [(555, 4)]) is None
    assert estimate_cn_shop_translation(
        before, after, [(555, 4)], movement_bounds=(-1, 120)
    ) == 65


@pytest.mark.parametrize("offset", [-50, 180])
def test_movement_outside_verified_gesture_bounds_cannot_advance_indices(offset):
    assert estimate_cn_shop_translation(
        *_frames(offset), [(555, 4)], movement_bounds=(-1, 120)
    ) is None


def test_next_row_image_tracks_motion_before_its_price_enters_detector_scan():
    before, after = _frames(offset=65)
    # The upper pay row is305; the next row's image is visible at390..535.
    # Its price555 need not have been returned by the currency detector yet.
    assert estimate_cn_shop_translation(
        before, after, [(305, 4)], movement_bounds=(-1, 120)
    ) == 65
