"""Honor explicit swipe durations in service-mode Nemu control."""

from __future__ import annotations

import math
import time
from functools import wraps


def install_gesture_compat() -> None:
    from core.device.control.nemu import NemuControl, insert_swipe

    original = NemuControl.swipe
    if getattr(original, "_baas_gesture_compat", False):
        return

    @wraps(original)
    def swipe(context, x1, y1, x2, y2, duration):
        if duration is None:
            return original(context, x1, y1, x2, y2, duration)
        seconds = float(duration)
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Swipe duration must be finite and non-negative.")

        # Keep the existing curve and coordinates, already scaled by Baas_thread.
        points = list(insert_swipe(p0=(x1, y1), p3=(x2, y2)))
        target = (int(x2), int(y2))
        if not points:
            points.append((int(x1), int(y1)))
        if tuple(points[-1]) != target:
            points.append(target)

        started = time.monotonic()

        def wait_until(deadline):
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)

        try:
            for index, point in enumerate(points):
                wait_until(started + seconds * index / max(1, len(points) - 1))
                context.nemu_client.down(*point)
            wait_until(started + seconds)
        finally:
            context.nemu_client.up()
        time.sleep(0.050)

    swipe._baas_gesture_compat = True
    NemuControl.swipe = swipe
