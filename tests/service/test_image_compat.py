from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from core import color, image, position
from service.image_compat import (
    _match_gift_close_anchor, _match_local_template, _match_shop_tab_offset,
    install_popup_image_compat,
)


AREA = (563, 277, 613, 312)
GIFT = [
    [[69, 563], [1238, 572]],
    [[35, 55, 60, 80, 90, 110], [5, 25, 23, 43, 54, 74]],
]


@pytest.fixture(autouse=True)
def preserve_core_comparisons(monkeypatch):
    monkeypatch.setattr(image, "compare_image", image.compare_image)
    monkeypatch.setattr(color, "match_rgb_feature", color.match_rgb_feature)
    picture = sys.modules.get("core.picture")
    if picture is not None and hasattr(picture, "match_rgb_feature"):
        monkeypatch.setattr(picture, "match_rgb_feature", picture.match_rgb_feature)


def _template():
    template = np.full((35, 50, 3), 225, dtype=np.uint8)
    cv2.putText(template, "Full", (1, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 40, 40), 2)
    return template


def _context(template, shift=(-1, 3), ratio=1, *, brightness=0):
    screenshot = np.full((720, 1280, 3), 225, dtype=np.uint8)
    if shift is not None:
        x, y = AREA[0] + shift[0], AREA[1] + shift[1]
        screenshot[y:y + 35, x:x + 50] = np.clip(
            template.astype(np.int16) + brightness, 0, 255
        ).astype(np.uint8)
    screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
    return SimpleNamespace(latest_img_array=screenshot, ratio=ratio, identifier="CN")


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("shift", [(-1, 3), (-5, -4), (5, 5)])
def test_local_fallback_recognizes_small_layout_shift_at_screen_ratios(ratio, shift):
    template = _template()
    context = _context(template, shift=shift, ratio=ratio)
    assert _match_local_template(context, template, AREA, 0.8, 20, image.compare_image_rgb)


@pytest.mark.parametrize("shift", [None, (30, 0), (0, -30)])
def test_local_fallback_rejects_absent_or_distant_template(shift):
    template = _template()
    assert not _match_local_template(
        _context(template, shift), template, AREA, 0.8, 20, image.compare_image_rgb
    )


def test_local_fallback_preserves_score_and_rgb_thresholds():
    template = _template()
    context = _context(template)
    assert not _match_local_template(context, template, AREA, 1, 20, image.compare_image_rgb)
    changed_color = _context(template, brightness=-35)
    assert not _match_local_template(changed_color, template, AREA, 0.8, 20, image.compare_image_rgb)
    assert _match_local_template(changed_color, template, AREA, 0.8, 40, image.compare_image_rgb)
    altered = _template()
    cv2.rectangle(altered, (0, 0), (25, 34), (0, 0, 0), -1)
    assert not _match_local_template(_context(altered), template, AREA, 0.8, 255, image.compare_image_rgb)


@pytest.mark.parametrize("feature_name", [
    "main_page_full-notice", "cafe_button-goto-no1-cafe", "cafe_button-goto-no2-cafe",
    "lesson_purchase-lesson-ticket-menu",
    "lesson_all-locations",
    "cafe_confirm-invite",
    "normal_task_start-sweep-notice",
    "normal_task_hard-start-sweep-notice",
    "special_task_request-select",
    "create_start-crafting-notice",
    "shop_purchase-notice1",
])
def test_service_patch_keeps_original_first_and_limits_fallback_scope(monkeypatch, feature_name):
    template = _template()
    calls = []

    def original(context, name, threshold=0.8, rgb_diff=20):
        calls.append((name, threshold, rgb_diff))
        return name == "already_matched"

    monkeypatch.setattr(image, "compare_image", original)
    monkeypatch.setattr(position, "image_dic", {"CN": {feature_name: template}})
    monkeypatch.setattr(position, "get_area", lambda identifier, name: AREA)
    install_popup_image_compat()
    wrapped = image.compare_image
    install_popup_image_compat()
    assert image.compare_image is wrapped
    context = _context(template)
    assert image.compare_image(context, "already_matched")
    assert not image.compare_image(context, "other_feature")
    assert image.compare_image(context, feature_name)
    assert not image.compare_image(context, feature_name, threshold=1, rgb_diff=12)
    context.identifier = "JP"
    assert not image.compare_image(context, feature_name)
    assert calls[-2] == (feature_name, 1, 12)
    assert len(calls) == 5


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_crafting_confirmation_tolerates_only_local_title_shift(ratio):
    template_path = Path(__file__).resolve().parents[2] / "src/images/CN/create/start-crafting-notice.png"
    template = cv2.imread(str(template_path))
    height, width = template.shape[:2]
    area = (451, 296, 854, 328)
    for shift, expected in (((-1, 3), True), ((0, 20), False)):
        screenshot = np.full((720, 1280, 3), 245, dtype=np.uint8)
        x, y = area[0] + shift[0], area[1] + shift[1]
        screenshot[y:y + height, x:x + width] = template
        screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
        context = SimpleNamespace(latest_img_array=screenshot, ratio=ratio)
        assert _match_local_template(
            context, template, area, 0.8, 20, image.compare_image_rgb
        ) is expected


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("y", [147, 280, 420])
def test_purchase_question_tracks_quantity_dependent_dialog_height(monkeypatch, ratio, y):
    template = cv2.imread(str(Path(__file__).resolve().parents[2]
                            / "src/images/CN/shop/purchase-notice1.png"))
    screenshot = np.full((720, 1280, 3), 245, dtype=np.uint8)
    height, width = template.shape[:2]
    screenshot[y:y + height, 512:512 + width] = template
    screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
    context = SimpleNamespace(latest_img_array=screenshot, ratio=ratio, identifier="CN")
    monkeypatch.setattr(image, "compare_image", lambda *args, **kwargs: False)
    monkeypatch.setattr(position, "image_dic", {"CN": {"shop_purchase-notice1": template}})
    install_popup_image_compat()
    assert image.compare_image(context, "shop_purchase-notice1")
    assert not image.compare_image(context, "shop_purchase-notice1", threshold=1)
    context.identifier = "JP"
    assert not image.compare_image(context, "shop_purchase-notice1")


@pytest.mark.parametrize("x,y", [(200, 147), (512, 70), (512, 500)])
def test_purchase_question_rejects_text_outside_its_dialog_region(monkeypatch, x, y):
    template = cv2.imread(str(Path(__file__).resolve().parents[2]
                            / "src/images/CN/shop/purchase-notice1.png"))
    screenshot = np.full((720, 1280, 3), 245, dtype=np.uint8)
    height, width = template.shape[:2]
    screenshot[y:y + height, x:x + width] = template
    context = SimpleNamespace(latest_img_array=screenshot, ratio=1, identifier="CN")
    monkeypatch.setattr(image, "compare_image", lambda *args, **kwargs: False)
    monkeypatch.setattr(position, "image_dic", {"CN": {"shop_purchase-notice1": template}})
    install_popup_image_compat()
    assert not image.compare_image(context, "shop_purchase-notice1")


def _crafting_button_context(monkeypatch, displayed, *, ratio=1, scale=0.825):
    folder = Path(__file__).resolve().parents[2] / "src/images/CN/create"
    names = ["start-phase-1-bright", "start-phase-1-grey", "select-node", "start-crafting", displayed]
    templates = {f"create_{name}": cv2.imread(str(folder / f"{name}.png")) for name in names}
    shown = templates[f"create_{displayed}"]
    height, width = shown.shape[:2]
    shown = cv2.resize(shown, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    screenshot = np.full((720, 1280, 3), 240, dtype=np.uint8)
    screenshot[640:640 + shown.shape[0], 1011:1011 + shown.shape[1]] = shown
    screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
    monkeypatch.setattr(image, "compare_image", lambda *args, **kwargs: False)
    monkeypatch.setattr(position, "image_dic", {"CN": templates})
    monkeypatch.setattr(position, "get_area", lambda *args: (1000, 630, 1240, 677))
    install_popup_image_compat()
    return SimpleNamespace(latest_img_array=screenshot, ratio=ratio, identifier="CN")


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("scale", [0.825, 0.85])
@pytest.mark.parametrize("state", ["bright", "grey"])
def test_smaller_crafting_button_retains_bright_grey_state(monkeypatch, ratio, scale, state):
    name = f"create_start-phase-1-{state}"
    context = _crafting_button_context(monkeypatch, f"start-phase-1-{state}", ratio=ratio, scale=scale)
    assert image.compare_image(context, name)
    other = "grey" if state == "bright" else "bright"
    assert not image.compare_image(context, f"create_start-phase-1-{other}")
    context.identifier = "JP"
    assert not image.compare_image(context, name)


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("scale", [0.825, 0.85])
@pytest.mark.parametrize("displayed", ["start-phase-2-bright", "start-phase-3-bright", "select-node"])
def test_scaled_phase_one_fallback_rejects_other_stage_digits_and_labels(monkeypatch, displayed, ratio, scale):
    context = _crafting_button_context(monkeypatch, displayed, ratio=ratio, scale=scale)
    assert not image.compare_image(context, "create_start-phase-1-bright")


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("scale", [0.825, 0.85])
@pytest.mark.parametrize("label", ["select-node", "start-crafting"])
def test_smaller_crafting_action_labels_remain_distinct(monkeypatch, ratio, scale, label):
    context = _crafting_button_context(monkeypatch, label, ratio=ratio, scale=scale)
    assert image.compare_image(context, f"create_{label}")
    other = "start-crafting" if label == "select-node" else "select-node"
    assert not image.compare_image(context, f"create_{other}")
    assert not image.compare_image(context, "create_start-phase-1-bright")
    context.identifier = "JP"
    assert not image.compare_image(context, f"create_{label}")


@pytest.mark.parametrize("direction", [1, 2])
@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_shifted_cafe_switch_retains_direction_and_color_checks(direction, ratio):
    image_dir = Path(__file__).resolve().parents[2] / "src/images/CN/cafe"
    template = cv2.imread(str(image_dir / f"button-goto-no{direction}-cafe.png"))
    other = cv2.imread(str(image_dir / f"button-goto-no{3 - direction}-cafe.png"))
    screenshot = np.full((720, 1280, 3), 250, dtype=np.uint8)
    height, width = template.shape[:2]
    screenshot[92:92 + height, 150:150 + width] = template
    screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
    context = SimpleNamespace(latest_img_array=screenshot, ratio=ratio)
    area = (151, 91, 163, 115)
    assert _match_local_template(context, template, area, 0.8, 20, image.compare_image_rgb)
    assert not _match_local_template(context, other, area, 0.8, 20, image.compare_image_rgb)


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_lesson_menu_eight_pixel_shift_needs_only_its_ten_pixel_window(ratio):
    template_path = Path(__file__).resolve().parents[2] / "src/images/CN/lesson/purchase-lesson-ticket-menu.png"
    template = cv2.imread(str(template_path))
    height, width = template.shape[:2]
    area = (561, 147, 720, 186)
    for shift, expected in ((8, True), (20, False)):
        screenshot = np.full((720, 1280, 3), 250, dtype=np.uint8)
        screenshot[147 + shift:147 + shift + height, 561:561 + width] = template
        screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
        context = SimpleNamespace(latest_img_array=screenshot, ratio=ratio)
        assert _match_local_template(
            context, template, area, 0.8, 20, image.compare_image_rgb, padding=10
        ) is expected
        assert not _match_local_template(context, template, area, 0.8, 20, image.compare_image_rgb)


def test_zero_lesson_purchase_setting_only_reads_tickets(monkeypatch):
    from module import lesson

    calls = []
    context = SimpleNamespace(
        config=SimpleNamespace(lesson_times=[0], purchase_lesson_ticket_times=0),
        static_config=SimpleNamespace(lesson_region_name={"CN": ["区域1"]}),
        identifier="CN", server="CN",
        update_screenshot_array=lambda: None, to_main_page=lambda: None,
        logger=SimpleNamespace(warning=lambda message: calls.append(message)),
    )
    monkeypatch.setattr(lesson, "to_lesson_location_select", lambda *args: None)
    monkeypatch.setattr(lesson, "get_lesson_tickets", lambda context: 0)
    monkeypatch.setattr(lesson, "purchase_lesson_ticket", lambda *args: pytest.fail("Purchase count is zero"))
    assert lesson.implement(context)
    assert context.lesson_tickets == 0
    assert calls == ["No Lesson Tickets"]


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_all_locations_title_sixteen_pixel_shift_keeps_other_lesson_headers_distinct(ratio):
    image_dir = Path(__file__).resolve().parents[2] / "src/images/CN/lesson"
    template = cv2.imread(str(image_dir / "all-locations.png"))
    area = (575, 100, 703, 135)
    height, width = template.shape[:2]
    for shift, expected in ((-16, True), (-30, False)):
        screenshot = np.full((720, 1280, 3), 250, dtype=np.uint8)
        screenshot[100 + shift:100 + shift + height, 575:575 + width] = template
        screenshot = cv2.resize(screenshot, (round(1280 * ratio), round(720 * ratio)))
        context = SimpleNamespace(latest_img_array=screenshot, ratio=ratio)
        assert _match_local_template(
            context, template, area, 0.8, 20, image.compare_image_rgb, padding=18
        ) is expected
        if expected:
            for other in ("lesson-information", "lesson-report", "purchase-lesson-ticket-menu"):
                other_template = cv2.imread(str(image_dir / f"{other}.png"))
                assert not _match_local_template(
                    context, other_template, area, 0.8, 20, image.compare_image_rgb, padding=18
                )


def _gift_context(ratio=1, title=True, close_shift=(0, -11), close_color=(15, 33, 64)):
    screenshot = np.full((round(720 * ratio), round(1280 * ratio), 3), 250, dtype=np.uint8)
    anchors = []
    if title:
        anchors.append((GIFT[0][0], (45, 70, 99)))
    if close_shift is not None:
        anchors.append(((1238 + close_shift[0], 572 + close_shift[1]), close_color))
    for point, rgb in anchors:
        screenshot[int(point[1] * ratio), int(point[0] * ratio)] = rgb[::-1]
    return SimpleNamespace(
        latest_img_array=screenshot, ratio=ratio, identifier="CN", rgb_feature={"gift": GIFT},
    )


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
@pytest.mark.parametrize("shift", [(0, -11), (-10, 8), (10, 10)])
def test_gift_fallback_keeps_title_and_allows_only_local_close_anchor(ratio, shift):
    context = _gift_context(ratio, close_shift=shift)
    assert not color.match_rgb_feature(context, "gift")
    assert _match_gift_close_anchor(context, color.rgb_in_range)


@pytest.mark.parametrize("kwargs", [
    {"title": False}, {"close_shift": None}, {"close_shift": (0, -20)},
    {"close_shift": (20, 0)}, {"close_color": (100, 100, 100)},
])
def test_gift_fallback_requires_both_anchors_with_original_color_limits(kwargs):
    assert not _match_gift_close_anchor(_gift_context(**kwargs), color.rgb_in_range)


def test_gift_patch_keeps_original_first_and_cn_gift_scope(monkeypatch):
    calls = []

    def original(context, name):
        calls.append(name)
        return name == "already_matched"

    monkeypatch.setattr(color, "match_rgb_feature", original)
    picture = SimpleNamespace(match_rgb_feature=original)
    monkeypatch.setitem(sys.modules, "core.picture", picture)
    install_popup_image_compat()
    wrapped = color.match_rgb_feature
    install_popup_image_compat()
    assert color.match_rgb_feature is wrapped
    assert picture.match_rgb_feature is wrapped
    context = _gift_context()
    assert color.match_rgb_feature(context, "already_matched")
    assert color.match_rgb_feature(context, "gift")
    assert not color.match_rgb_feature(context, "cafe")
    context.identifier = "JP"
    assert not color.match_rgb_feature(context, "gift")
    assert calls == ["already_matched", "gift", "cafe", "gift"]


SHOP_TAB_LIMITS = {
    "temp_shop_not_selected": [245, 255, 245, 255, 245, 255],
    "temp_shop_selected": [35, 55, 60, 80, 89, 109],
}


def _shop_tab_context(name="temp_shop_not_selected", *, ratio=1, shifts=(5,) * 4,
                      top=248, horizontal_shift=0):
    screenshot = np.zeros((round(720 * ratio), round(1280 * ratio), 3), dtype=np.uint8)
    points = [[1, top], [1, top + 35], [206, top], [206, top + 35]]
    limits = SHOP_TAB_LIMITS[name]
    rgb = [(limits[index] + limits[index + 1]) // 2 for index in (0, 2, 4)]
    for (x, y), shift in zip(points, shifts):
        row, col = int((y + shift) * ratio), int((x + horizontal_shift) * ratio)
        if 0 <= row < screenshot.shape[0] and 0 <= col < screenshot.shape[1]:
            screenshot[row, col] = rgb[::-1]
    return SimpleNamespace(
        latest_img_array=screenshot, ratio=ratio, identifier="CN",
        rgb_feature={name: [points, [limits.copy() for _ in points]]},
    )


@pytest.mark.parametrize("name", SHOP_TAB_LIMITS)
@pytest.mark.parametrize("ratio", [0.5, 0.75, 1, 1.5, 2])
@pytest.mark.parametrize("shift", [-6, -5, 5, 6])
def test_shop_tab_fallback_moves_all_four_anchors_with_the_same_small_offset(name, ratio, shift):
    context = _shop_tab_context(name, ratio=ratio, shifts=(shift,) * 4)
    assert not color.match_rgb_feature(context, name)
    assert _match_shop_tab_offset(context, name, color.rgb_in_range)


@pytest.mark.parametrize("name", SHOP_TAB_LIMITS)
@pytest.mark.parametrize("kwargs", [
    {"shifts": (7,) * 4}, {"shifts": (-7,) * 4},
    {"shifts": (-5, -2, 2, 5)}, {"shifts": (5, 5, 5)},
    {"horizontal_shift": 2}, {"top": 1, "shifts": (-6,) * 4},
    {"top": 684, "shifts": (6,) * 4},
])
def test_shop_tab_fallback_rejects_distant_scattered_incomplete_and_out_of_frame_anchors(name, kwargs):
    context = _shop_tab_context(name, **kwargs)
    assert not _match_shop_tab_offset(context, name, color.rgb_in_range)


@pytest.mark.parametrize("name", SHOP_TAB_LIMITS)
def test_shop_tab_fallback_preserves_selected_state_and_original_rgb_ranges(name):
    other = next(candidate for candidate in SHOP_TAB_LIMITS if candidate != name)
    context = _shop_tab_context(other)
    context.rgb_feature[name] = _shop_tab_context(name).rgb_feature[name]
    assert not _match_shop_tab_offset(context, name, color.rgb_in_range)
    context = _shop_tab_context(name)
    pixel = context.latest_img_array[253, 1]
    pixel[2] = SHOP_TAB_LIMITS[name][0] - 1
    assert not _match_shop_tab_offset(context, name, color.rgb_in_range)


@pytest.mark.parametrize("malformation", [
    "missing", "outer", "point_count", "limits_count", "rectangle_width",
    "rectangle_height", "point_order", "float_point", "wrong_limits", "float_limit",
    "negative_top", "bottom_outside", "non_point", "non_limits",
])
def test_shop_tab_fallback_ignores_malformed_temporary_features(malformation):
    name = "temp_shop_not_selected"
    context = _shop_tab_context(name)
    points, limits = context.rgb_feature[name]
    if malformation == "missing":
        context.rgb_feature.clear()
    elif malformation == "outer":
        context.rgb_feature[name] = None
    elif malformation == "point_count":
        points.pop()
    elif malformation == "limits_count":
        limits.pop()
    elif malformation == "rectangle_width":
        points[2][0] -= 1
    elif malformation == "rectangle_height":
        points[1][1] -= 1
    elif malformation == "point_order":
        points[1], points[2] = points[2], points[1]
    elif malformation == "float_point":
        points[0][0] = 1.0
    elif malformation == "wrong_limits":
        limits[0][0] -= 1
    elif malformation == "float_limit":
        limits[0][0] = 245.0
    elif malformation == "negative_top":
        context = _shop_tab_context(name, top=-1)
    elif malformation == "bottom_outside":
        context = _shop_tab_context(name, top=685)
    elif malformation == "non_point":
        points[0] = None
    elif malformation == "non_limits":
        limits[0] = None
    assert not _match_shop_tab_offset(context, name, color.rgb_in_range)


@pytest.mark.parametrize("ratio", [0, -1, float("nan"), float("inf"), False, None, "1"])
def test_shop_tab_fallback_rejects_invalid_screen_ratio(ratio):
    context = _shop_tab_context()
    context.ratio = ratio
    assert not _match_shop_tab_offset(context, "temp_shop_not_selected", color.rgb_in_range)


@pytest.mark.parametrize("screenshot", [None, np.zeros((720, 1280), dtype=np.uint8),
                                         np.zeros((720, 1280, 2), dtype=np.uint8),
                                         np.zeros((720, 720, 3), dtype=np.uint8)])
def test_shop_tab_fallback_rejects_missing_or_inconsistent_screen_dimensions(screenshot):
    context = _shop_tab_context()
    context.latest_img_array = screenshot
    assert not _match_shop_tab_offset(context, "temp_shop_not_selected", color.rgb_in_range)


def test_shop_tab_patch_keeps_original_first_and_limits_scope_to_cn_temporary_tabs(monkeypatch):
    calls = []

    def original(context, name):
        calls.append(name)
        return name == "already_matched"

    monkeypatch.setattr(color, "match_rgb_feature", original)
    install_popup_image_compat()
    context = _shop_tab_context()
    assert color.match_rgb_feature(context, "already_matched")
    assert color.match_rgb_feature(context, "temp_shop_not_selected")
    context.rgb_feature["another_feature"] = context.rgb_feature["temp_shop_not_selected"]
    assert not color.match_rgb_feature(context, "another_feature")
    for identifier in ("JP", "Global"):
        context.identifier = identifier
        assert not color.match_rgb_feature(context, "temp_shop_not_selected")
    assert calls == ["already_matched", "temp_shop_not_selected", "another_feature",
                     "temp_shop_not_selected", "temp_shop_not_selected"]


def test_shop_tab_patch_preserves_original_success_without_touching_fallback(monkeypatch):
    monkeypatch.setattr(color, "match_rgb_feature", lambda *args: True)
    monkeypatch.setattr(color, "rgb_in_range", lambda *args: pytest.fail("Original already matched"))
    install_popup_image_compat()
    assert color.match_rgb_feature(_shop_tab_context(), "temp_shop_not_selected")


def test_shop_tab_patch_does_not_swallow_original_cancellation(monkeypatch):
    class Cancelled(Exception):
        pass

    def original(*args):
        raise Cancelled()

    monkeypatch.setattr(color, "match_rgb_feature", original)
    install_popup_image_compat()
    with pytest.raises(Cancelled):
        color.match_rgb_feature(_shop_tab_context(), "temp_shop_not_selected")
