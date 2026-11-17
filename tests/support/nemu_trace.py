"""Observe the task's own Nemu calls without adding input, captures or delays."""
import json
import time

from tests.runner.evidence import now
from tests.stress.nemu_capture import Metrics, atomic_json


class LiveNemuTrace:
    def __init__(self, baas, recorder, case):
        self.baas, self.recorder, self.case = baas, recorder, case
        self.provider = baas.screenshot.screenshot_instance
        self.client = self.provider.nemu_client
        self.metrics = Metrics()
        self.started = time.perf_counter()
        self.last_flush = self.started
        self.last_touch = None
        self.touch_count = 0
        self.frame_id = 0
        self.after_touch_frames = 0
        self.after_touch_empty = 0
        self.problem_contexts = []
        self.last_evidence = 0
        self.last_good = None
        self.original_ipc = self.client.ev_run_sync
        self.original_capture = self.provider.screenshot
        self.directory = recorder.directory / case["case_id"]
        self.directory.mkdir(exist_ok=True)
        self.path = self.directory / "nemu-trace.json"
        self.shared_control_client = getattr(getattr(baas.control, "control_instance", None), "nemu_client", None) is self.client

    def context(self):
        touch = self.last_touch
        return {"time": now(), "frame_id": self.frame_id, "last_touch": touch,
                "milliseconds_since_touch": None if touch is None else round((time.perf_counter() - touch["monotonic"]) * 1000, 3)}

    def install(self):
        traced = self.metrics.trace(self.original_ipc)

        def ipc(func, *args, **kwargs):
            if func.__name__.startswith("nemu_input_event_touch_"):
                self.last_touch = {"event": func.__name__, "time": now(), "monotonic": time.perf_counter(),
                                   "position": list(args[2:])}
                if func.__name__.endswith("_down"):
                    self.touch_count += 1
                self.recorder.capture(self.case["case_id"], "Nemu input: " + json.dumps(self.last_touch))
            try:
                return traced(func, *args, **kwargs)
            except Exception as exc:
                event = {**self.context(), "event": "ipc_exception", "function": func.__name__,
                         "type": type(exc).__module__ + "." + type(exc).__name__, "repr": repr(exc)}
                self.problem_contexts.append(event)
                self.recorder.capture(self.case["case_id"], "Nemu IPC exception: " + json.dumps(event),
                                      self.last_good, required=True)
                raise

        def capture():
            import numpy as np
            self.frame_id += 1
            before = sum(self.metrics.errors.values())
            started = time.perf_counter()
            context = self.context()
            frame = self.original_capture()
            duration = (time.perf_counter() - started) * 1000
            valid = frame is not None and getattr(frame, "ndim", 0) == 3 and frame.shape[2] == 3 and frame.size > 0 and frame.dtype == np.uint8
            recovered = valid and sum(self.metrics.errors.values()) > before
            recent = context["milliseconds_since_touch"] is not None and context["milliseconds_since_touch"] <= 1000
            with self.metrics.lock:
                self.metrics.frames += 1
                self.metrics.frame_ms.append(duration)
                self.metrics.empty += int(frame is None)
                self.metrics.invalid += int(frame is not None and not valid)
                self.metrics.recovered += int(recovered)
                if valid:
                    self.metrics.shapes[str(tuple(frame.shape))] += 1
                    self.metrics.blank += int(frame[::32, ::32].max() < 4)
            self.after_touch_frames += int(recent)
            self.after_touch_empty += int(recent and frame is None)
            if not valid or recovered:
                event = {**context, "event": "capture_result", "empty": frame is None,
                         "valid": bool(valid), "recovered": bool(recovered), "capture_ms": round(duration, 3)}
                self.problem_contexts.append(event)
                self.recorder.capture(self.case["case_id"], "Nemu capture result: " + json.dumps(event),
                                      frame if valid else self.last_good, required=True)
            if valid:
                self.last_good = frame
                if recent and time.perf_counter() - self.last_evidence >= 3:
                    self.recorder.capture(self.case["case_id"], "Nemu frame after input: " + json.dumps(context), frame)
                    self.last_evidence = time.perf_counter()
            if not valid or recovered or time.perf_counter() - self.last_flush >= 5:
                self.flush("running")
            return frame

        self.client.ev_run_sync = ipc
        self.provider.screenshot = capture
        with self.recorder.lock:
            self.case["nemu_trace"] = str(self.path.relative_to(self.recorder.directory)).replace("\\", "/")
        self.flush("running")
        return self

    def flush(self, state):
        self.last_flush = time.perf_counter()
        data = {"state": state, "task_id": self.case["task_id"], "case_id": self.case["case_id"],
                "elapsed_seconds": round(self.last_flush - self.started, 3),
                "timeout_policy": "Unchanged production arguments and defaults",
                "shared_control_client": self.shared_control_client, "touch_down_calls": self.touch_count,
                "frames_within_one_second_of_touch": self.after_touch_frames,
                "empty_frames_within_one_second_of_touch": self.after_touch_empty,
                "problem_contexts": self.problem_contexts,
                **self.metrics.snapshot(self.last_flush - self.started)}
        atomic_json(self.path, data)
        with self.recorder.lock:
            self.case["nemu_summary"] = {k: data[k] for k in ("frames", "empty_frames", "recovered_frames", "ipc_errors", "touch_down_calls")}

    def close(self):
        self.provider.screenshot = self.original_capture
        self.client.ev_run_sync = self.original_ipc
        self.flush("finished")
