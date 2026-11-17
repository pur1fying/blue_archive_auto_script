"""Test-scoped global Ctrl+C and a bounded shutdown of the owned test host."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import threading
import time


class GlobalCtrlC:
    HOTKEY_ID = 0xBAA
    WM_HOTKEY = 0x0312

    def __init__(self, callback):
        self.callback = callback
        self.ready = threading.Event()
        self.thread = None
        self.thread_id = None
        self.error = None
        self.closing = threading.Event()

    def __enter__(self):
        if os.name != 'nt':
            return self
        self.thread = threading.Thread(target=self._listen, name='test-ctrl-c', daemon=True)
        self.thread.start()
        if not self.ready.wait(3):
            self.close()
            raise RuntimeError('Global Ctrl+C listener did not become ready; tests were not started')
        if self.error is not None:
            raise RuntimeError('Cannot register global Ctrl+C; tests were not started: ' + str(self.error))
        return self

    def _listen(self):
        registered = False
        try:
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            self.thread_id = kernel32.GetCurrentThreadId()
            user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
            user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
            user32.GetMessageW.restype = ctypes.c_int
            user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
            message = wintypes.MSG()
            user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
            # MOD_CONTROL | MOD_NOREPEAT. Active only while this test batch runs.
            if not user32.RegisterHotKey(None, self.HOTKEY_ID, 0x0002 | 0x4000, ord('C')):
                raise ctypes.WinError(ctypes.get_last_error())
            registered = True
            self.ready.set()
            while True:
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result < 0:
                    raise ctypes.WinError(ctypes.get_last_error())
                if result == 0:
                    break
                if message.message == self.WM_HOTKEY and message.wParam == self.HOTKEY_ID:
                    self.callback()
        except BaseException as exc:
            self.error = exc
        finally:
            self.ready.set()
            if registered:
                user32.UnregisterHotKey(None, self.HOTKEY_ID)
                if not self.closing.is_set():
                    self.callback()  # Never continue a test after losing its stop listener.

    def close(self):
        self.closing.set()
        if self.thread is not None and self.thread.is_alive() and self.thread_id is not None:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)  # WM_QUIT
            self.thread.join(timeout=3)

    def __exit__(self, *args):
        self.close()


def release_mouse_buttons():
    if os.name == 'nt':
        # A forcibly terminated drag may not reach its normal mouse-up call.
        ctypes.windll.user32.mouse_event(0x0004 | 0x0010 | 0x0040, 0, 0, 0, 0)


def terminate_test_host(process, root, directory):
    """Terminate only this Popen, its matching Python worker and owned OCR."""
    import psutil
    try:
        parent = psutil.Process(process.pid)
        descendants = parent.children(recursive=True)
    except psutil.Error:
        descendants = []
    workers, ocr = [], []
    expected_output = os.path.normcase(str(Path(directory).resolve()))
    expected_ocr = os.path.normcase(str((Path(root) / 'core/ocr/baas_ocr_client/bin/BAAS_ocr_server.exe').resolve()))
    for child in descendants:
        try:
            args = child.cmdline()
            if {'tests.runner.worker', 'tests.stress.nemu_capture'} & set(args) and '--output' in args:
                output = os.path.normcase(str(Path(args[args.index('--output') + 1]).resolve()))
                if output == expected_output:
                    workers.append(child)
        except (psutil.Error, ValueError, IndexError):
            continue
    worker_ids = {process.pid} | {child.pid for child in workers}
    for child in descendants:
        try:
            if child.ppid() in worker_ids and os.path.normcase(child.exe()) == expected_ocr:
                ocr.append(child)
        except psutil.Error:
            pass
    for child in workers:
        try:
            child.kill()
        except psutil.Error:
            pass
    if process.poll() is None:
        process.kill()
    for child in ocr:
        try:
            child.kill()
        except psutil.Error:
            pass


class TestStopControl:
    def __init__(self, root, directory, grace_seconds=2, release_input=release_mouse_buttons):
        self.root, self.directory = Path(root), Path(directory)
        self.grace_seconds = grace_seconds
        self.release_input = release_input
        self.condition = threading.Condition()
        self.requested = False
        self.force = False
        self.finished = False
        self.forced = False
        self.requested_at = None
        self.process = None
        self.thread = None

    def request(self):
        with self.condition:
            if self.finished:
                return
            if self.requested:
                self.force = True
            else:
                self.requested = True
                self.requested_at = time.monotonic()
            self.condition.notify_all()

    def attach(self, process):
        self.process = process
        self.thread = threading.Thread(target=self._watch, name='test-stop-watchdog', daemon=True)
        self.thread.start()

    def _watch(self):
        with self.condition:
            self.condition.wait_for(lambda: self.requested or self.finished)
            if self.finished:
                return
        try:
            self.process.stdin.write('{"type":"cancel"}\n')
            self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass
        with self.condition:
            self.condition.wait_for(lambda: self.force or self.finished,
                                    timeout=max(0, self.requested_at + self.grace_seconds - time.monotonic()))
            if self.finished:
                return
        if self.process.poll() is None:
            self.forced = True
            terminate_test_host(self.process, self.root, self.directory)
            self.release_input()

    def close(self):
        with self.condition:
            self.finished = True
            self.condition.notify_all()
        if self.thread is not None:
            self.thread.join(timeout=3)
