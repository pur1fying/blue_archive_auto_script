from __future__ import annotations

from service.android_modes import ANDROID_LOCAL_METHOD
from core.device.uiautomator2_client import U2Client


def _with_uiautomator_retry(u2_client, operation):
    """Runs an Android-local UIAutomator operation with one reconnect attempt."""
    try:
        return operation()
    except Exception:
        connection = u2_client.get_connection()
        uiautomator = getattr(connection, "uiautomator", None)
        if uiautomator is not None:
            uiautomator.start()
        return operation()


class AndroidLocalControl:
    """Android-embedded control adapter backed by the local device agent."""

    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def click(self, x, y):
        """Taps the Android screen and retries once if UIAutomator detached."""
        return _with_uiautomator_retry(self.u2, lambda: self.u2.click(x, y))

    def swipe(self, x1, y1, x2, y2, duration):
        """Swipes the Android screen and retries once if UIAutomator detached."""
        return _with_uiautomator_retry(self.u2, lambda: self.u2.swipe(x1, y1, x2, y2, duration))

    def long_click(self, x, y, duration):
        """Presses one Android screen point for the requested duration."""
        return _with_uiautomator_retry(self.u2, lambda: self.u2.swipe(x, y, x, y, duration))

    def scroll(self, x, y, clicks):
        """Converts wheel-style scroll clicks into Android swipe gestures."""
        direction = -1 if clicks > 0 else 1
        distance = 240 * abs(clicks)
        self.swipe(x, y, x, y + direction * distance, 0.2)


class AndroidLocalScreenshot:
    """Android-embedded screenshot adapter backed by the local device agent."""

    def __init__(self, conn):
        self.serial = conn.serial
        self.u2 = U2Client.get_instance(self.serial)

    def screenshot(self):
        """Captures the Android screen and retries once if UIAutomator detached."""
        return _with_uiautomator_retry(self.u2, lambda: self.u2.screenshot())
