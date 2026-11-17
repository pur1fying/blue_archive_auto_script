"""Bounded MuMu capture stress test. Never injects touch or keyboard input."""
import argparse
import asyncio
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import hashlib
import html
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]


def atomic_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def distribution(values):
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    def percentile(p):
        return round(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))], 3)
    return {"count": len(values), "mean_ms": round(sum(values) / len(values), 3),
            "p50_ms": percentile(.5), "p95_ms": percentile(.95), "p99_ms": percentile(.99),
            "max_ms": round(ordered[-1], 3)}


class Metrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame_ms = []
        self.ipc_ms = {}
        self.native_ms = {}
        self.errors = Counter()
        self.error_examples = []
        self.frames = 0
        self.empty = 0
        self.invalid = 0
        self.recovered = 0
        self.active = 0
        self.max_active = 0
        self.late = 0
        self.peak_rss_mb = 0
        self.blank = 0
        self.shapes = Counter()

    def trace(self, original, timeout=None):
        def invoke(func, *args, **kwargs):
            stage = func.__name__
            if stage == "nemu_capture_display":
                stage += ":resolution" if args[2] == 0 else ":pixels"
            state = {"timed_out": False}

            @wraps(func)
            def native(*native_args, **native_kwargs):
                started = time.perf_counter()
                with self.lock:
                    self.active += 1
                    self.max_active = max(self.max_active, self.active)
                try:
                    return func(*native_args, **native_kwargs)
                finally:
                    elapsed = (time.perf_counter() - started) * 1000
                    with self.lock:
                        self.active -= 1
                        self.native_ms.setdefault(stage, []).append(elapsed)
                        if state["timed_out"]:
                            self.late += 1

            if timeout is not None:
                kwargs["timeout"] = timeout
            started = time.perf_counter()
            try:
                result = original(native, *args, **kwargs)
                if stage != "nemu_connect" and result != 0:
                    with self.lock:
                        self.errors[f"{stage}:return={result}"] += 1
                return result
            except Exception as exc:
                elapsed = (time.perf_counter() - started) * 1000
                with self.lock:
                    state["timed_out"] = isinstance(exc, (TimeoutError, asyncio.TimeoutError))
                    key = f"{stage}:{type(exc).__module__}.{type(exc).__name__}"
                    self.errors[key] += 1
                    if len(self.error_examples) < 20:
                        self.error_examples.append({"stage": stage, "type": key, "repr": repr(exc),
                            "elapsed_ms": round(elapsed, 3), "active_native_calls": self.active,
                            "traceback": traceback.format_exc()})
                raise
            finally:
                with self.lock:
                    self.ipc_ms.setdefault(stage, []).append((time.perf_counter() - started) * 1000)
        return invoke

    def snapshot(self, elapsed):
        with self.lock:
            return {"frames": self.frames, "empty_frames": self.empty, "invalid_frames": self.invalid,
                    "recovered_frames": self.recovered, "near_blank_frames": self.blank,
                    "fps": round(self.frames / max(elapsed, .001), 2),
                    "capture_latency": distribution(self.frame_ms),
                    "ipc_latency": {k: distribution(v) for k, v in self.ipc_ms.items()},
                    "native_latency": {k: distribution(v) for k, v in self.native_ms.items()},
                    "ipc_errors": dict(self.errors), "error_examples": list(self.error_examples),
                    "active_native_calls": self.active, "max_active_native_calls": self.max_active,
                    "native_calls_completed_after_timeout": self.late,
                    "peak_rss_mb": round(self.peak_rss_mb, 1), "shapes": dict(self.shapes)}


def capture_worker(args):
    # Import native libraries before creating any threads on bundled Windows Python.
    import numpy as np
    import cv2
    import psutil
    from core.device.screenshot.nemu import NemuScreenshot
    from core.device.Screenshot import Screenshot
    config = json.loads((ROOT / "config" / args.config / "config.json").read_text(encoding="utf-8"))
    logger = logging.getLogger("nemu-stress")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(args.output / "sdk.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    # Preserve production SDK discovery, but do not persist any auto-detected path.
    conn = SimpleNamespace(config=SimpleNamespace(**config), logger=logger, serial=args.serial,
                           config_set=SimpleNamespace(set=lambda key, value: logger.info("Read-only config suggestion: %s=%s", key, value)))
    with ThreadPoolExecutor(max_workers=1) as initializer:
        provider = initializer.submit(NemuScreenshot, conn).result(timeout=10)
    client = provider.nemu_client
    metrics = Metrics()
    client.ev_run_sync = metrics.trace(client.ev_run_sync, args.timeout)
    original_capture = provider.screenshot
    first_image = []
    consecutive = [0]
    process = psutil.Process()

    def measured_capture():
        with metrics.lock:
            errors_before = sum(metrics.errors.values())
        started = time.perf_counter()
        frame = original_capture()  # Includes the production three-attempt retry policy.
        elapsed = (time.perf_counter() - started) * 1000
        valid = frame is not None and getattr(frame, "ndim", 0) == 3 and frame.shape[2] == 3 and frame.size > 0 and frame.dtype == np.uint8
        with metrics.lock:
            metrics.frames += 1
            metrics.frame_ms.append(elapsed)
            if frame is None:
                metrics.empty += 1
            elif not valid:
                metrics.invalid += 1
            if valid:
                metrics.shapes[str(tuple(frame.shape))] += 1
                metrics.recovered += int(sum(metrics.errors.values()) > errors_before)
                sample = frame[::32, ::32]
                metrics.blank += int(sample.max() < 4)
                if not first_image:
                    first_image.append(frame.copy())
            consecutive[0] = 0 if valid else consecutive[0] + 1
        return frame

    provider.screenshot = measured_capture
    screenshot = Screenshot.__new__(Screenshot)
    screenshot.screenshot_instance = provider
    screenshot.screenshot_interval = args.interval
    screenshot.last_screenshot_time = 0
    screenshot.Baas_instance = SimpleNamespace(is_android_device=True)
    # The baseline reuses production pacing. Burst phases add no delay.
    finished = threading.Event()
    started = time.perf_counter()
    state = {"phase": args.phase, "rpc_timeout_seconds": args.timeout,
             "screenshot_interval_seconds": args.interval, "requested_seconds": args.seconds,
             "pid": os.getpid(), "serial": args.serial, "state": "running"}

    def reader():
        last_report = started
        try:
            while time.perf_counter() - started < args.seconds:
                screenshot.screenshot()
                current = time.perf_counter()
                if current - last_report >= 5:
                    with metrics.lock:
                        metrics.peak_rss_mb = max(metrics.peak_rss_mb, process.memory_info().rss / 1024**2)
                    atomic_json(args.output / "result.json", {**state, "elapsed_seconds": round(current - started, 2), **metrics.snapshot(current - started)})
                    last_report = current
                if consecutive[0] >= 20:
                    state["stop_reason"] = "Twenty consecutive invalid or empty frames"
                    break
                if metrics.peak_rss_mb > 1024:
                    state["stop_reason"] = "Worker RSS exceeded 1024 MiB"
                    break
        except BaseException as exc:
            state["worker_error"] = {"type": type(exc).__name__, "repr": repr(exc), "traceback": traceback.format_exc()}
        finally:
            state["state"] = "finished"
            elapsed = time.perf_counter() - started
            atomic_json(args.output / "result.json", {**state, "elapsed_seconds": round(elapsed, 2), **metrics.snapshot(elapsed)})
            finished.set()

    thread = threading.Thread(target=reader, name="nemu-stress-reader", daemon=True)
    thread.start()
    finished.wait(args.seconds + 5)
    if not finished.is_set():
        state.update(state="stalled", stop_reason="Capture loop did not return before the watchdog deadline")
    if first_image:
        ok, encoded = cv2.imencode(".png", cv2.cvtColor(first_image[0], cv2.COLOR_RGB2BGR))
        if ok:
            (args.output / "first-frame.png").write_bytes(encoded.tobytes())
    try:
        if finished.is_set():
            client.disconnect()
    except BaseException as exc:
        state["disconnect_error"] = repr(exc)
    elapsed = time.perf_counter() - started
    atomic_json(args.output / "result.json", {**state, "elapsed_seconds": round(elapsed, 2), **metrics.snapshot(elapsed)})


def write_summary(output, results):
    atomic_json(output / "summary.json", results)
    rows = []
    for r in results:
        latency = r.get("capture_latency", {})
        problem = r.get("worker_error") or r.get("stop_reason") or r.get("disconnect_error") or ""
        if isinstance(problem, dict):
            problem = problem.get("repr", str(problem))
        values = [r.get("phase"), r.get("state"), r.get("frames", 0), r.get("fps", 0),
                  latency.get("p95_ms", "-"), latency.get("p99_ms", "-"), latency.get("max_ms", "-"),
                  sum(r.get("ipc_errors", {}).values()), r.get("empty_frames", 0), r.get("invalid_frames", 0),
                  r.get("recovered_frames", 0), r.get("max_active_native_calls", 0),
                  r.get("native_calls_completed_after_timeout", 0), r.get("forced_cleanup", False), problem]
        rows.append("<tr>" + "".join("<td>" + html.escape(str(v)) + "</td>" for v in values) + "</tr>")
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>MuMu capture stress test</title>
<style>body{font:16px system-ui;margin:32px;color:#243145}table{border-collapse:collapse}td,th{border:1px solid #ccd4de;padding:9px}th{background:#eef2f7}</style>
<h1>MuMu capture stress test</h1><p>Read-only screenshots. No game input. Capture latency excludes pacing, includes production retries. Parallel workers use independent SDK connections.</p>
<table><tr><th>Phase</th><th>State</th><th>Frames</th><th>FPS</th><th>P95 ms</th><th>P99 ms</th><th>Max ms</th><th>IPC errors</th><th>Empty frames</th><th>Invalid frames</th><th>Recovered frames</th><th>Max concurrent native calls</th><th>Native completions after timeout</th><th>Forced cleanup</th><th>Problem</th></tr>'''+''.join(rows)+'''</table>
<p>Finished means the worker exited its capture loop; inspect errors, empty/invalid frames and stop reasons separately. Recovered frames had an IPC error before a production retry returned a valid image.</p>
<p>Near-blank frames can be legitimate loading frames. A successful static-screen stress test does not certify every game transition.</p>
<p><a href="summary.json">Complete measurements and exception examples</a></p></html>'''
    (output / "report.html").write_text(page, encoding="utf-8")


def controller(args):
    from tests.runner.model import read_config
    from tests.support.discovery import discover, external_conflicts
    from tests.support.locking import batch_lock
    from tests.support.stop_control import GlobalCtrlC, TestStopControl, terminate_test_host
    config = read_config(ROOT, args.config)
    issues = external_conflicts(ROOT)
    target = discover(ROOT, args.config, config)
    if issues or not target.ready or target.kind != "android":
        raise RuntimeError("Preflight blocked: " + "; ".join(issues + [target.reason]))
    output = ROOT / "output/test_runs" / time.strftime("nemu-stress-%Y%m%d-%H%M%S")
    output.mkdir(parents=True)
    atomic_json(output / "environment.json", {"config": args.config, "target": target.data(),
        "python": sys.version, "sdk_source_sha256": hashlib.sha256((ROOT / "core/device/nemu_client.py").read_bytes()).hexdigest(),
        "note": "Timeout overrides apply to every IPC call in the test worker only. Production config is unchanged."})
    duration = [5, 5, 5, 5] if args.quick else [120, 90, 60, 90]
    groups = [[("baseline", .3, .15, duration[0])], [("burst", 0, .15, duration[1])],
              [("parallel-a", 0, .15, duration[2]), ("parallel-b", 0, .15, duration[2])],
              [("timeout-500ms", 0, .5, duration[3])]]
    results, active = [], []
    stopped = threading.Event()

    def request_stop():
        stopped.set()
        for entry in list(active):
            entry[-1].request()

    with batch_lock(ROOT / "output/test_runs/.batch.lock"), GlobalCtrlC(request_stop):
        print("Ctrl+C stops the screenshot stress test from any application on Windows.", flush=True)
        try:
            for group in groups:
                if stopped.is_set():
                    break
                active = []
                print("Starting " + ", ".join(p[0] for p in group), flush=True)
                for phase, interval, timeout, seconds in group:
                    directory = output / phase
                    directory.mkdir()
                    log = (directory / "process.log").open("w", encoding="utf-8")
                    command = [sys.executable, "-m", "tests.stress.nemu_capture", "--worker", "--config", args.config,
                               "--serial", target.detail["serial"], "--phase", phase, "--interval", str(interval),
                               "--timeout", str(timeout), "--seconds", str(seconds), "--output", str(directory)]
                    process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                                               text=True, encoding="utf-8",
                                               env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
                                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    control = TestStopControl(ROOT, directory)
                    control.attach(process)
                    active.append((process, log, directory, seconds, time.monotonic(), control))
                    if stopped.is_set():
                        control.request()
                for process, log, directory, seconds, start, control in active:
                    forced = False
                    try:
                        process.wait(timeout=max(1, seconds + 20 - (time.monotonic() - start)))
                    except subprocess.TimeoutExpired:
                        forced = True
                        terminate_test_host(process, ROOT, directory)
                        process.wait(timeout=5)
                    control.close()
                    process.stdin.close()
                    forced = forced or control.forced
                    log.close()
                    path = directory / "result.json"
                    result = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"phase": directory.name, "state": "failed", "worker_error": "No result was produced"}
                    result.update(forced_cleanup=forced, process_exit_code=process.returncode)
                    if result.get("state") == "running":
                        result["state"] = "stalled"
                    if stopped.is_set():
                        result.update(state="cancelled", stop_reason="Stopped by Ctrl+C")
                    atomic_json(path, result)
                    results.append(result)
                    write_summary(output, results)
                    print(json.dumps({k: result.get(k) for k in ["phase", "state", "frames", "fps", "empty_frames", "recovered_frames", "ipc_errors", "capture_latency", "forced_cleanup"]}), flush=True)
        finally:
            for process, log, directory, _, _, control in active:
                if process.poll() is None:
                    terminate_test_host(process, ROOT, directory)
                    process.wait(timeout=5)
                control.close()
                process.stdin.close()
                log.close()
    print("Report: " + str(output / "report.html"), flush=True)
    return 130 if stopped.is_set() else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="cn")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--serial", default="")
    parser.add_argument("--phase", default="")
    parser.add_argument("--interval", type=float, default=0)
    parser.add_argument("--timeout", type=float, default=.15)
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        capture_worker(args)
    else:
        return controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
