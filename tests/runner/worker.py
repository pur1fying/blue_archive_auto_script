"""Private test host. Does not open a production HTTP port or start a scheduler."""
import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import threading
import tempfile
from pathlib import Path

from tests.runner.backend import ProductionBackend
from tests.runner.evidence import Recorder, now
from tests.runner.executor import Executor, cases_for
from tests.runner.model import load_plan, read_config
from tests.runner.report import write_report
from tests.support.discovery import discover, external_conflicts, environment_problems
from tests.support.privacy import redact, secrets_in
from tests.tasks.catalog import catalog
from tests.tasks.ocr_catalog import scan as scan_ocr, write_inventory

PREFIX = "BAAS_TEST_EVENT "


def read_git(root, *args, timeout=5):
    # Use a regular file rather than a pipe: a Git launcher child retaining the
    # pipe must not prevent the final report from being written on Windows.
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(["git", *args], cwd=root, stdout=output, stderr=subprocess.DEVNULL,
                                   env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        try:
            result = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            import psutil
            try:
                for child in psutil.Process(process.pid).children(recursive=True):
                    try:
                        child.kill()
                    except psutil.Error:
                        pass
            except psutil.Error:
                pass
            process.kill()
            process.wait(timeout=2)
            raise
        if result:
            raise subprocess.CalledProcessError(result, process.args)
        output.seek(0)
        return output.read()


def source_info(root):
    def git(*args):
        return read_git(root, *args)
    try:
        status = git("status", "--porcelain").decode("utf-8", "replace")
        return {"commit": git("rev-parse", "HEAD").decode().strip(), "dirty": bool(status),
                "working_changes": status.splitlines(),
                "diff_sha256": hashlib.sha256(git("diff", "HEAD", "--binary")).hexdigest(),
                "test_code_sha256": hashlib.sha256(b"".join(p.read_bytes() for p in sorted((root / "tests").rglob("*.py")))).hexdigest()}
    except (OSError, subprocess.SubprocessError):
        return {"commit": "unknown", "dirty": "unknown", "error": "Git metadata is unavailable"}


async def run(root, plan_path, directory):
    jobs = load_plan(json.loads(plan_path.read_text(encoding="utf-8-sig")), root, catalog(root))
    configs = {job.config_id: read_config(root, job.config_id) for job in jobs}
    secrets = secrets_in(configs)
    cases = cases_for(jobs)
    data = {"version": 1, "run_id": directory.name, "state": "running", "started_at": now(),
            "source": source_info(root), "configs_before": redact(configs, secrets), "cases": cases}
    ocr_inventory = scan_ocr(root)
    write_inventory(directory, ocr_inventory)
    data["ocr_inventory"] = "ocr-inventory.html"
    data["ocr_inventory_parse_errors"] = ocr_inventory["parse_errors"]
    recorder = Recorder(directory, cases, secrets)
    cancel = asyncio.Event()
    loop = asyncio.get_running_loop()
    backend = None

    def request_stop():
        if backend is not None:
            backend.request_stop()
        if not loop.is_closed():
            loop.call_soon_threadsafe(cancel.set)

    def listen():
        for line in sys.stdin:
            try:
                if json.loads(line).get("type") == "cancel":
                    request_stop()
            except (ValueError, AttributeError):
                continue
        request_stop()

    threading.Thread(target=listen, name="test-control", daemon=True).start()

    def emit(event):
        print(PREFIX + json.dumps(redact(event, secrets), ensure_ascii=False), flush=True)
        data["cases"] = recorder.snapshot()
        write_report(directory, data)

    try:
        emit({"type": "batch_started", "run_id": directory.name})
        emit({"type": "phase", "message": "Checking service dependencies and external task ownership."})
        conflicts = environment_problems(root, configs.values())
        conflicts.extend(await asyncio.wait_for(asyncio.to_thread(external_conflicts, root), timeout=30))
        targets = {}
        for job in jobs:
            emit({"type": "phase", "message": f"Discovering client for config {job.config_id}."})
            target = await asyncio.wait_for(asyncio.to_thread(discover, root, job.config_id, configs[job.config_id]), timeout=30)
            if conflicts:
                target.ready, target.reason = False, "; ".join(conflicts)
            targets[job.config_id] = target
        data["targets"] = {k: v.data() for k, v in targets.items()}
        backend = ProductionBackend(root, recorder)
        if any(t.ready for t in targets.values()) and not cancel.is_set():
            emit({"type": "phase", "message": "Initializing the production service runtime and OCR."})
            data["startup_log"] = "startup.jsonl"
            startup = asyncio.create_task(backend.start())
            startup_cancel = asyncio.create_task(cancel.wait())
            done, _ = await asyncio.wait({startup, startup_cancel}, timeout=180, return_when=asyncio.FIRST_COMPLETED)
            startup_cancel.cancel()
            if cancel.is_set():
                raise asyncio.CancelledError("Test cancelled during initialization")
            if startup not in done:
                raise TimeoutError("Service initialization exceeded 180 seconds")
            data["runtime_functions"] = await startup
        executor = Executor(jobs, targets, backend, recorder, cancel, emit,
                            lambda config_id: read_config(root, config_id))
        emit({"type": "phase", "message": "Starting selected task queues."})
        await executor.run()
        data["state"] = "cancelled" if cancel.is_set() else "finished"
    except BaseException as exc:
        cancel.set()
        data["state"] = "cancelled" if isinstance(exc, asyncio.CancelledError) else "failed"
        data["error"] = redact(str(exc) or type(exc).__name__, secrets)
        for case in cases:
            if case["status"] in {"not_run", "running"}:
                case.update(status="blocked", reason=data["error"])
    finally:
        if backend is not None:
            try:
                await backend.close()
            except Exception as exc:
                data["cleanup_error"] = redact(str(exc), secrets)
        await asyncio.to_thread(recorder.close)
        data["ended_at"] = now()
        data["startup_evidence_dropped"] = recorder.system_dropped
        data["source_end"] = source_info(root)
        data["source_changed"] = (None if data["source_end"].get("error") or data["source"].get("error")
                                  else data["source_end"] != data["source"])
        data["cases"] = recorder.snapshot()
        write_inventory(directory, ocr_inventory, data["cases"])
        write_report(directory, data)
        emit({"type": "batch_finished", "state": data["state"], "report": str(directory / "report.html")})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.chdir(args.root)
    os.environ["BAAS_SERVICE_OCR_UPDATE_CHECK"] = "0"
    # The bundled Windows Python can deadlock on the first NumPy extension
    # import from an executor thread. Load native libraries before any threads.
    print(PREFIX + json.dumps({"type": "phase", "message": "Loading native libraries on the main thread."}), flush=True)
    import numpy  # noqa: F401
    import cv2  # noqa: F401
    if os.getenv("BAAS_TEST_DIAGNOSTICS") == "1":
        import faulthandler
        with (args.output / "thread-stacks.log").open("w", encoding="utf-8") as stream:
            faulthandler.dump_traceback_later(30, repeat=True, file=stream)
            try:
                asyncio.run(run(args.root, args.plan, args.output))
            finally:
                faulthandler.cancel_dump_traceback_later()
        return
    asyncio.run(run(args.root, args.plan, args.output))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Core logging may install Rich's local-variable exception dump. Test
        # crashes should print a normal traceback, never entire config/frame data.
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
