"""Track CN catalog movement using product identities rather than buy buttons."""

from __future__ import annotations

import math
from statistics import median


def estimate_cn_shop_translation(before, after, item_lines_y, ratio=1.0, diagnostics=None,
                                 movement_bounds=None):
    """Return content movement (up is positive), or None without a unique consensus."""
    import cv2

    from core.image import compare_image_rgb

    if before is None or after is None or not math.isfinite(ratio) or ratio <= 0:
        return None
    images = []
    for image in (before, after):
        if image.ndim != 3 or image.shape[2] != 3:
            return None
        if ratio != 1:
            height, width = image.shape[:2]
            image = cv2.resize(image, (round(width / ratio), round(height / ratio)),
                               interpolation=cv2.INTER_AREA)
        if image.shape[0] < 606 or image.shape[1] < 1218:
            return None
        images.append(image)
    before, after = images
    anchors = []
    # A next row's product image can be fully visible before its price reaches
    # the detector's y<=560 scan. Use it for motion only, never purchase indices.
    row_positions = {row_y for row_y, _ in item_lines_y}
    row_positions.update(row_y + 250 for row_y, _ in item_lines_y)
    for row_y in sorted(row_positions):
        top, bottom = round(row_y - 165), round(row_y - 20)
        if top < 127 or bottom > 606:
            continue
        for column in range(4):
            left = 640 + 150 * column
            template = before[top:bottom, left:left + 120]
            if template.std(axis=(0, 1)).max() < 5:
                continue
            search = after[127:606, left - 8:left + 128]
            scores = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
            if movement_bounds is not None:
                minimum, maximum = movement_bounds
                first = max(0, math.ceil(top - 127 - maximum))
                last = min(scores.shape[0], math.floor(top - 127 - minimum) + 1)
                if last <= first:
                    continue
                scores[:first] = -1
                scores[last:] = -1
            _, score, _, (x, y) = cv2.minMaxLoc(scores)
            detail = {"row": row_y, "column": column, "score": score,
                      "dx": x - 8, "dy": top - (127 + y)}
            if diagnostics is not None:
                diagnostics.append(detail)
            if not score > 0.9:
                continue
            # Similar copies of an item on two rows do not establish its index.
            other = scores.copy()
            other[max(0, y - 8):y + 9] = -1
            if cv2.minMaxLoc(other)[1] > 0.9 and score - cv2.minMaxLoc(other)[1] < 0.03:
                continue
            candidate = search[y:y + template.shape[0], x:x + template.shape[1]]
            detail["rgb_ok"] = bool(compare_image_rgb(template, candidate, rgb_diff=20))
            if detail["rgb_ok"]:
                anchors.append((top - (127 + y), column))
    groups = []
    for offset, _ in anchors:
        group = [(value, column) for value, column in anchors if abs(value - offset) <= 2]
        if len({column for _, column in group}) >= 2:
            groups.append(median(value for value, _ in group))
    if not groups or max(groups) - min(groups) > 2:
        return None
    return float(median(groups))
