"""Service-only recognition of the smaller CN scrimmage result label."""

from __future__ import annotations

from functools import wraps
from math import isfinite

from service.image_compat import _match_local_template


_ACTIVE_ATTRIBUTE = "_baas_cn_scrimmage_sweep"
_RESULT_AREA = (601, 561, 682, 604)
_UNSET = object()


def _match_scrimmage_result(context, template, area, threshold, rgb_diff, compare_rgb):
    import cv2
    from core import color

    screenshot, ratio = context.latest_img_array, context.ratio
    if (screenshot is None or getattr(screenshot, "ndim", 0) != 3 or screenshot.shape[2] < 3
            or not isinstance(ratio, (int, float)) or isinstance(ratio, bool)
            or not isfinite(ratio) or ratio <= 0
            or area != _RESULT_AREA or template.shape[:2] != (43, 81)):
        return False
    height, width = screenshot.shape[:2]
    if abs(width - 1280 * ratio) > 1 or abs(height - 720 * ratio) > 1:
        return False
    # The completed-result dialog has a wide yellow header underline and a
    # cyan confirmation button below the rewards. A generic Confirm label on
    # another popup must not make this result feature match.
    anchors = [
        (550, 123, (245, 255, 225, 255, 60, 140)),
        (720, 123, (245, 255, 225, 255, 60, 140)),
        (1000, 95, (230, 255, 230, 255, 230, 255)),
        (550, 580, (70, 130, 180, 235, 230, 255)),
        (725, 580, (70, 130, 180, 235, 230, 255)),
    ]
    if not all(color.rgb_in_range(context, x, y, *bounds) for x, y, bounds in anchors):
        return False
    scaled = cv2.resize(template, (77, 41), interpolation=cv2.INTER_AREA)
    return _match_local_template(
        context, scaled, area, threshold, rgb_diff, compare_rgb, padding=3,
    )


def install_scrimmage_sweep_compat() -> None:
    """Keep the scaled-button fallback inside the CN scrimmage task only."""
    from core import image, position
    from core.Baas_thread import Baas_thread

    original_solve = Baas_thread.solve
    if getattr(original_solve, "_baas_scrimmage_sweep_compat", False):
        return
    original_compare = image.compare_image

    @wraps(original_solve)
    def solve(context, activity, *args, **kwargs):
        previous = getattr(context, _ACTIVE_ATTRIBUTE, _UNSET)
        setattr(context, _ACTIVE_ATTRIBUTE, context.identifier == "CN" and activity == "scrimmage")
        try:
            return original_solve(context, activity, *args, **kwargs)
        finally:
            if previous is _UNSET:
                delattr(context, _ACTIVE_ATTRIBUTE)
            else:
                setattr(context, _ACTIVE_ATTRIBUTE, previous)

    @wraps(original_compare)
    def compare_image(context, name, threshold=0.8, rgb_diff=20):
        matched = original_compare(context, name, threshold=threshold, rgb_diff=rgb_diff)
        if (matched or context.identifier != "CN" or not getattr(context, _ACTIVE_ATTRIBUTE, False)
                or name != "normal_task_sweep-complete"):
            return matched
        template = position.image_dic.get("CN", {}).get(name)
        if template is None:
            return False
        matched = _match_scrimmage_result(
            context, template, position.get_area("CN", name), threshold, rgb_diff,
            image.compare_image_rgb,
        )
        if matched:
            context.logger.info("Matched smaller CN scrimmage result label (0.95 scale).")
        return matched

    solve._baas_scrimmage_sweep_compat = True
    Baas_thread.solve = solve
    image.compare_image = compare_image
