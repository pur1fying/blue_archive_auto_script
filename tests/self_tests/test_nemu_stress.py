"""Check stress diagnostics without loading the emulator SDK."""
import asyncio
import threading
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.stress.nemu_capture import Metrics
from tests.support.nemu_trace import LiveNemuTrace


class CaptureDiagnosticsTests(unittest.TestCase):
    def test_records_native_completion_after_async_timeout(self):
        metrics = Metrics()
        entered = threading.Event()
        release = threading.Event()
        threads = []

        def nemu_capture_display(*args):
            entered.set()
            release.wait(2)
            return 0

        def original(func, *args, **kwargs):
            thread = threading.Thread(target=func, args=args)
            threads.append(thread)
            thread.start()
            self.assertTrue(entered.wait(1))
            raise asyncio.TimeoutError()

        try:
            with self.assertRaises(asyncio.TimeoutError):
                metrics.trace(original, .15)(nemu_capture_display, 1, 0, 10)
            self.assertEqual(metrics.snapshot(1)["active_native_calls"], 1)
        finally:
            release.set()
            for thread in threads:
                thread.join(2)
        result = metrics.snapshot(1)
        self.assertEqual(result["active_native_calls"], 0)
        self.assertEqual(result["native_calls_completed_after_timeout"], 1)
        self.assertEqual(sum(result["ipc_errors"].values()), 1)
        self.assertEqual(result["error_examples"][0]["stage"], "nemu_capture_display:pixels")

    def test_resolution_timeout_override_and_return_value(self):
        metrics = Metrics()
        observed = []

        def nemu_capture_display(*args):
            return 0

        def original(func, *args, **kwargs):
            observed.append(kwargs["timeout"])
            return func(*args)

        result = metrics.trace(original, .5)(nemu_capture_display, 1, 0, 0)
        snapshot = metrics.snapshot(1)
        self.assertEqual(result, 0)
        self.assertEqual(observed, [.5])
        self.assertEqual(snapshot["ipc_errors"], {})
        self.assertEqual(snapshot["native_latency"]["nemu_capture_display:resolution"]["count"], 1)

    def test_live_trace_preserves_retries_none_and_timeout_arguments(self):
        import numpy as np
        from core.device.screenshot.nemu import NemuScreenshot
        attempts, timeouts, records = [], [], []
        failure = [True]

        def nemu_capture_display(*args):
            attempts.append(1)
            if failure[0]:
                raise asyncio.TimeoutError()
            return 0

        def original_ipc(func, *args, **kwargs):
            timeouts.append(kwargs.copy())
            return func(*args)

        client = SimpleNamespace(ev_run_sync=original_ipc)
        frame = np.full((8, 8, 3), 127, dtype=np.uint8)

        def native_screenshot():
            client.ev_run_sync(nemu_capture_display, 1, 0, 256, timeout=.27)
            return frame

        client.screenshot = native_screenshot
        provider = NemuScreenshot.__new__(NemuScreenshot)
        provider.nemu_client = client
        provider.logger = SimpleNamespace(warning=lambda message: None)
        original_capture = provider.screenshot
        baas = SimpleNamespace(screenshot=SimpleNamespace(screenshot_instance=provider),
                               control=SimpleNamespace(control_instance=SimpleNamespace(nemu_client=client)))
        case = {"case_id": "test-case", "task_id": "group"}
        with tempfile.TemporaryDirectory() as directory:
            recorder = SimpleNamespace(directory=Path(directory), lock=threading.RLock(),
                                       capture=lambda *args, **kwargs: records.append(args))
            trace = LiveNemuTrace(baas, recorder, case).install()
            try:
                self.assertIsNone(provider.screenshot())
                self.assertEqual(len(attempts), 3)
                failure[0] = False
                self.assertIs(provider.screenshot(), frame)
                self.assertTrue(trace.shared_control_client)
                self.assertEqual(trace.metrics.empty, 1)
                self.assertEqual(trace.metrics.frames, 2)
                self.assertEqual(timeouts, [{"timeout": .27}] * 4)
            finally:
                trace.close()
            self.assertEqual(provider.screenshot, original_capture)
            self.assertIs(client.ev_run_sync, original_ipc)


if __name__ == "__main__":
    unittest.main()
