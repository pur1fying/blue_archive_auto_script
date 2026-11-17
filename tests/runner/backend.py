import asyncio
import inspect
import os
import threading
from types import SimpleNamespace

from tests.runner.evidence import RecordingQueue


class ProductionBackend:
    """Use the real service lifecycle, including its current injection chain."""
    def __init__(self, root, recorder):
        self.root, self.recorder = root, recorder
        self.runtime = None
        self.pending = set()
        self.initial_children = set()
        self.ocr_observer = None
        self.stop_requested = threading.Event()

    def request_stop(self):
        """Called by the control reader without waiting for the asyncio loop."""
        self.stop_requested.set()
        if self.runtime is not None:
            for session in list(self.runtime._sessions.values()):
                session.stop_event.set()
                session.baas.flag_run = False

    async def start(self):
        import psutil
        self.initial_children = {p.pid for p in psutil.Process().children()}
        from service.runtime import ServiceRuntime
        self.runtime = ServiceRuntime(self.root, asyncio.get_running_loop())
        await self.runtime.ensure_ready()
        self.runtime._main.logger.log_collector = SimpleNamespace(put=self.recorder.system)
        await asyncio.to_thread(self.runtime.init_all_data, False)
        if not self.runtime.is_all_data_initialized:
            raise RuntimeError("Service initialization failed; prepare OCR, device dependencies and configs first")
        from service.injection import apply_service_injections
        apply_service_injections()
        from tests.support.ocr_evidence import OcrObserver
        self.ocr_observer = OcrObserver(self.runtime._main.ocr, self.recorder, self.root).install()
        from core import image, color
        from core.device.control.nemu import NemuControl
        result = {}
        for name, fn in [("image.compare_image", image.compare_image),
                         ("color.match_rgb_feature", color.match_rgb_feature), ("NemuControl.swipe", NemuControl.swipe)]:
            result[name] = {"file": inspect.getsourcefile(fn), "wrapped": hasattr(fn, "__wrapped__")}
        return result

    def remember(self, task):
        self.pending.add(task)
        task.add_done_callback(self.pending.discard)
        # Consume background failures after a timed-out cooperative initialization.
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
        return task

    async def close(self):
        if self.runtime is None:
            return
        for session in self.runtime._sessions.values():
            session.baas.flag_run = False
        if self.ocr_observer is not None and all(session.thread is None or not session.thread.is_alive()
                                                 for session in self.runtime._sessions.values()):
            self.ocr_observer.close()
        # OCR startup creates a new child on an unused port. It is not an OCR
        # instance belonging to another service; close only this owned Popen.
        main = self.runtime._main
        client = getattr(getattr(main, "ocr", None), "client", None)
        process = getattr(client, "server_process", None)
        if process is not None and process.poll() is None:
            stop = asyncio.create_task(asyncio.to_thread(client.stop_server))
            done, _ = await asyncio.wait({stop}, timeout=3)
            if stop in done:
                try:
                    await stop
                except Exception:
                    if process.poll() is None:
                        process.terminate()
            elif process.poll() is None:
                process.terminate()
                stop.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
        # A constructor failure can lose its Popen before Main.ocr is assigned.
        # Inspect only new direct children of this test host at the exact OCR path.
        import os
        import psutil
        expected = os.path.normcase(str((self.root / "core/ocr/baas_ocr_client/bin" /
                                        ("BAAS_ocr_server.exe" if os.name == "nt" else "BAAS_ocr_server")).resolve()))
        for child in psutil.Process().children():
            try:
                if child.pid not in self.initial_children and os.path.normcase(child.exe()) == expected:
                    child.terminate()
            except psutil.Error:
                pass

    async def run_case(self, job, case, batch_cancel):
        runtime = self.runtime
        loop = asyncio.get_running_loop()
        deadline = loop.time() + job.timeout_seconds
        cancel_wait = asyncio.create_task(batch_cancel.wait())
        obtaining = asyncio.create_task(runtime.get_session(job.config_id))
        done, _ = await asyncio.wait({obtaining, cancel_wait}, timeout=job.timeout_seconds, return_when=asyncio.FIRST_COMPLETED)
        if cancel_wait in done or obtaining not in done:
            obtaining.cancel()
            cancel_wait.cancel()
            return {"status": "cancelled" if batch_cancel.is_set() else "timeout",
                    "reason": "Cancelled or timed out while waiting for the service session", "quiescent": True}
        try:
            session = await obtaining
        except BaseException:
            cancel_wait.cancel()
            raise
        baas = session.baas
        baas.logger.log_collector = RecordingQueue(self.recorder, job.config_id, baas)
        if self.ocr_observer is not None:
            self.ocr_observer.register(job.config_id, baas)
        status_queue = await runtime.subscribe_status()
        case_cancel = threading.Event()
        if self.stop_requested.is_set():
            case_cancel.set()
        nemu_trace = None
        blocked_reason = None
        original_init = baas.init_all_data
        original_send = baas.send

        def initialize():
            nonlocal nemu_trace, blocked_reason
            if self.stop_requested.is_set():
                case_cancel.set()
                return False
            initialized = original_init()
            if initialized is False:
                return False
            if case_cancel.is_set():
                return False
            expected = case.get("target", {}).get("detail", {})
            connection = getattr(baas, "connection", None)
            if "serial" in expected and getattr(connection, "serial", None) != expected["serial"]:
                blocked_reason = "The device address changed after preflight; task was not executed"
                return False
            if "hwnd" in expected:
                window = getattr(connection, "app_process_window", None)
                if getattr(window, "_hwnd", None) != expected["hwnd"]:
                    blocked_reason = "The game window changed after preflight; task was not executed"
                    return False
            with self.recorder.lock:
                case["initialization_thread"] = {"id": threading.get_ident(), "name": threading.current_thread().name}
                case["runtime_target"] = {"server": getattr(baas, "server", None),
                    "identifier": getattr(baas, "identifier", None), "ratio": getattr(baas, "ratio", None),
                    "resolution": getattr(baas, "resolution", None),
                    "screenshot_method": getattr(getattr(baas, "screenshot", None), "method", None),
                    "control_method": getattr(getattr(baas, "control", None), "method", None)}
            self.recorder.capture(case["case_id"], "before / latest available frame", baas.latest_img_array, required=True)
            if os.getenv("BAAS_TEST_NEMU_TRACE") == "1" and getattr(getattr(baas, "screenshot", None), "method", None) == "nemu":
                from tests.support.nemu_trace import LiveNemuTrace
                nemu_trace = LiveNemuTrace(baas, self.recorder, case).install()
            return initialized

        def send(*args, **kwargs):
            if args and args[0] == "solve":
                with self.recorder.lock:
                    case["execution_thread"] = {"id": threading.get_ident(), "name": threading.current_thread().name}
            return original_send(*args, **kwargs)

        # Observe the production worker's initialization; do not initialize on
        # the asyncio/test host thread before dispatching the real task.
        baas.init_all_data = initialize
        baas.send = send

        async def dispatch():
            return await runtime.solve_task(job.config_id, case["task_id"], _plugin_cancel=case_cancel)

        started = self.remember(asyncio.create_task(dispatch()))
        status = "failed"
        reason = ""
        quiescent = True
        try:
            async def wait_or_cancel(awaitable):
                operation = asyncio.ensure_future(awaitable)
                done, _ = await asyncio.wait({operation, cancel_wait}, timeout=max(0, deadline - loop.time()), return_when=asyncio.FIRST_COMPLETED)
                if cancel_wait in done:
                    if operation is not started:
                        operation.cancel()
                    raise asyncio.CancelledError
                if operation not in done:
                    if operation is not started:
                        operation.cancel()
                    raise TimeoutError("Task exceeded its total timeout")
                return await operation

            response = await wait_or_cancel(started)
            if response.get("status") != "ok":
                status, reason = "blocked", str(response.get("status", "Start failed"))
            else:
                # The API acknowledgement only means that a thread was started.
                # Subscribe before starting so even immediate completion is observed.
                while True:
                    current = runtime.current_status().get(job.config_id, {})
                    thread = session.thread
                    if not current.get("running") and (thread is None or not thread.is_alive()):
                        if current.get("exit_code") == 1:
                            status, reason = "failed", "Production task returned failure or raised an exception"
                        elif not baas.flag_run:
                            status, reason = "cancelled", "Task was stopped; it cannot be counted as completed"
                        else:
                            status = "completed"
                        break
                    await wait_or_cancel(status_queue.get())
        except (TimeoutError, asyncio.CancelledError) as exc:
            status = "cancelled" if isinstance(exc, asyncio.CancelledError) else "timeout"
            reason = "Batch cancelled" if status == "cancelled" else "Task exceeded its total timeout"
            case_cancel.set()
            stop = self.remember(asyncio.create_task(runtime.stop_scheduler(job.config_id)))
            await asyncio.wait({stop}, timeout=10)
            quiescent = started.done() and (session.thread is None or not session.thread.is_alive())
            if not quiescent:
                reason += "; shutdown is incomplete and the device will remain blocked"
        except Exception as exc:
            case_cancel.set()
            status, reason = "failed", str(exc)
            stop = self.remember(asyncio.create_task(runtime.stop_scheduler(job.config_id)))
            await asyncio.wait({stop}, timeout=10)
            quiescent = started.done() and (session.thread is None or not session.thread.is_alive())
        finally:
            cancel_wait.cancel()
            runtime.unsubscribe_status(status_queue)
            if nemu_trace is not None and quiescent:
                nemu_trace.close()
            if quiescent:
                baas.init_all_data = original_init
                baas.send = original_send
            self.recorder.capture(case["case_id"], "after / latest available frame", baas.latest_img_array, required=True)
        if blocked_reason is not None:
            status, reason = "blocked", blocked_reason
        return {"status": status, "reason": reason, "quiescent": quiescent}
