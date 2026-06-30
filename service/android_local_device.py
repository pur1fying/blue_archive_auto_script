from __future__ import annotations

from service.android_modes import ANDROID_LOCAL_METHOD
from core.device.uiautomator2_client import U2Client


class AndroidLocalControl:
    """Android-embedded control adapter backed by the local device agent."""

    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def click(self, x, y):
        self.u2.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.u2.swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        self.u2.swipe(x, y, x, y, duration)

    def scroll(self, x, y, clicks):
        direction = -1 if clicks > 0 else 1
        distance = 240 * abs(clicks)
        self.swipe(x, y, x, y + direction * distance, 0.2)


class AndroidLocalScreenshot:
    """Android-embedded screenshot adapter backed by the local device agent."""

    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def screenshot(self):
        return self.u2.screenshot()
