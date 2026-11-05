"""Service-only OCR regions for the current CN asset bar."""

from __future__ import annotations

import time
from functools import wraps


CN_SECONDARY_CREDIT_REGION = (741, 10, 908, 40)
CN_HOME_CREDIT_REGION = (671, 20, 832, 52)
CN_HOME_AP_REGION = (484, 25, 609, 52)
CN_SECONDARY_AP_REGION = (530, 10, 662, 40)


def install_asset_compat() -> None:
    """Restore clipped CN asset digits without changing shared OCR state."""
    from core.Baas_thread import Baas_thread

    original = Baas_thread.get_creditpoints
    if getattr(original, "_baas_asset_compat", False):
        return
    original_ap = Baas_thread.get_ap

    @wraps(original)
    def get_creditpoints(context, is_main_page=False):
        if context.server != "CN":
            return original(context, is_main_page)
        region = CN_HOME_CREDIT_REGION if is_main_page else CN_SECONDARY_CREDIT_REGION
        text = context.ocr.get_region_res(
            context, region, "en-us", "Credit Points", "0123456789,", 0.2,
        )
        count = 0
        for char in text:
            if char.isdigit():
                count = count * 10 + int(char)
        context.config_set.set("creditpoints", {"count": count, "time": time.time()})
        return count

    @wraps(original_ap)
    def get_ap(context, is_main_page=False):
        if context.server != "CN":
            return original_ap(context, is_main_page)
        region = CN_HOME_AP_REGION if is_main_page else CN_SECONDARY_AP_REGION
        for attempt in range(3):
            text = context.ocr.get_region_res(context, region, "en-us", "AP", "0123456789/")
            # During a page transition the asset bar can yield a bare number.
            # It is not a valid count/max reading and must not replace the cache.
            if text.count("/") == 1:
                count_text, maximum_text = text.split("/")
                try:
                    count, maximum = int(count_text), int(maximum_text)
                    if 0 <= count <= 999 and 0 < maximum <= 999:
                        context.config_set.set("ap", {"count": count, "max": maximum, "time": time.time()})
                        return count
                except ValueError:
                    pass
            refresh = getattr(context, "update_screenshot_array", None)
            if attempt == 2 or not callable(refresh):
                break
            time.sleep(0.15)
            refresh()
        context.logger.warning("Failed to get AP.")
        return 999

    get_creditpoints._baas_asset_compat = True
    get_ap._baas_asset_compat = True
    Baas_thread.get_creditpoints = get_creditpoints
    Baas_thread.get_ap = get_ap
