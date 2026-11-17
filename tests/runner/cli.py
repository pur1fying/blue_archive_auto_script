import argparse
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path

from tests.runner.model import load_plan, plan_data, read_config, server_label
from tests.runner.report import LABELS, review, write_report
from tests.support.discovery import discover, external_conflicts, environment_problems
from tests.support.locking import batch_lock
from tests.support.privacy import redact, secrets_in
from tests.support.stop_control import GlobalCtrlC, TestStopControl, terminate_test_host
from tests.tasks.catalog import catalog, settings_for

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output/test_runs"
PREFIX = "BAAS_TEST_EVENT "


def config_ids(root):
    return sorted(p.parent.name for p in (root / "config").glob("*/config.json"))


def choose(tokens, options):
    selected = []
    for token in tokens.replace("，", ",").split(","):
        token = token.strip()
        if token in options:
            selected.append(token)
        elif token.isdigit() and 1 <= int(token) <= len(options):
            selected.append(options[int(token) - 1])
        else:
            raise ValueError(f"Invalid selection: {token!r}")
    return selected


def interactive(root, tasks):
    configs = config_ids(root)
    if not configs:
        raise ValueError("No configs found; create a BAAS config first")
    for number, config_id in enumerate(configs, 1):
        c = read_config(root, config_id)
        print(f"{number:2}. {config_id} | {c.get('name', config_id)} | {server_label(c.get('server'))} | {c.get('control_method')}")
    selected = choose(input("Select config numbers or IDs (comma-separated): "), configs)
    for number, (task, label) in enumerate(tasks.items(), 1):
        print(f"{number:2}. {task}: {label}")
    jobs = []
    for config_id in selected:
        value = input(f"{config_id} tasks (ordered comma-separated numbers/IDs; all selects every task): ").strip()
        task_ids = list(tasks) if value == "all" else choose(value, list(tasks))
        jobs.append({"config_id": config_id, "tasks": task_ids})
    return {"version": 1, "jobs": jobs}


def summarize(root, jobs):
    print("\nOriginal configs are used. Resources, claims and in-game purchases follow those configs. No real-money payments are performed.")
    for job in jobs:
        c = read_config(root, job.config_id)
        print(f"\n{job.config_id} [{server_label(c.get('server'))}]: {' -> '.join(job.tasks)}; timeout per task: {job.timeout_seconds:g} seconds")
        # Show exact configured actions rather than inventing a cost estimate.
        related = redact(settings_for(root, job.tasks, c), secrets_in(c))
        for key, value in related.items():
            rendered = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            if len(rendered) > 400:
                rendered = rendered[:400] + "... (full value is included in the report config snapshot)"
            print(f"  {key} = {rendered}")
    print("\nDesktop clients take turns using the foreground; independent emulators can run concurrently. Completed tasks still require functional review.")


def check(root, jobs):
    problems = environment_problems(root, [read_config(root, j.config_id) for j in jobs])
    try:
        problems.extend(external_conflicts(root))
    except ImportError as exc:
        problems.append(str(exc))
    ready = not problems
    for problem in problems:
        print("Blocked: " + problem)
    for job in jobs:
        target = discover(root, job.config_id, read_config(root, job.config_id))
        print(json.dumps(target.data(), ensure_ascii=False))
        ready = ready and target.ready
    return 0 if ready else 2


def launch(root, jobs):
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
    directory = OUTPUT / run_id
    directory.mkdir(parents=True)
    plan_path = directory / "plan.json"
    plan_path.write_text(json.dumps(plan_data(jobs), ensure_ascii=False, indent=2), encoding="utf-8")
    stop = TestStopControl(root, directory)
    with GlobalCtrlC(stop.request):
        previous_sigint = signal.signal(signal.SIGINT, lambda *_: stop.request())
        print("Ctrl+C stops this entire test batch" + (" from any application." if os.name == "nt" else " from this terminal."), flush=True)
        print("A second press forces shutdown; otherwise an unresponsive test host is terminated after 2 seconds.", flush=True)
        try:
            return _launch_host(root, jobs, directory, plan_path, stop)
        finally:
            stop.close()
            signal.signal(signal.SIGINT, previous_sigint)


def _launch_host(root, jobs, directory, plan_path, stop):
    run_id = directory.name
    if stop.requested:
        from tests.runner.executor import cases_for
        write_report(directory, {"run_id": run_id, "state": "cancelled", "cases": cases_for(jobs),
                                 "error": "Stopped before the test host started"})
        return 130
    secrets = secrets_in({j.config_id: read_config(root, j.config_id) for j in jobs})
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
    args = [sys.executable, "-m", "tests.runner.worker", "--root", str(root), "--plan", str(plan_path), "--output", str(directory)]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(args, cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=flags)
    stop.attach(process)
    lines = queue.Queue()

    def read():
        for line in process.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()
    cancelled, finished = False, False
    try:
        with (directory / "host.log").open("w", encoding="utf-8") as log:
            while True:
                try:
                    if stop.requested and not cancelled:
                        cancelled = True
                        print("Stop requested. Cancelling all test tasks and releasing input control.", flush=True)
                    line = lines.get(timeout=0.5)
                    if line is None:
                        break
                    line = redact(line, secrets)
                    log.write(line)
                    log.flush()
                    if line.startswith(PREFIX):
                        event = json.loads(line[len(PREFIX):])
                        if event["type"] == "case":
                            print(f"[{event['config_id']}] {event['task_id']}: {LABELS.get(event['status'], event['status'])} {event.get('reason', '')}", flush=True)
                        elif event["type"] == "phase":
                            print(event["message"], flush=True)
                        if event["type"] == "batch_finished":
                            finished = True
                            break
                    else:
                        print(line.rstrip())
                except queue.Empty:
                    if process.poll() is not None:
                        break
                except KeyboardInterrupt:
                    stop.request()
        try:
            process.wait(timeout=10 if finished else 2)
        except subprocess.TimeoutExpired:
            # Only our owned host is terminated, never a game, emulator or an
            # existing service/OCR process.
            terminate_test_host(process, root, directory)
            process.wait(timeout=5)
    finally:
        if process.poll() is None:
            terminate_test_host(process, root, directory)
            process.wait()
        stop.close()
        process.stdin.close()
        process.stdout.close()
    cancelled = cancelled or stop.requested
    result_path = directory / "result.json"
    if result_path.exists():
        data = json.loads(result_path.read_text(encoding="utf-8"))
    else:
        from tests.runner.executor import cases_for
        data = {"run_id": run_id, "cases": cases_for(jobs)}
    if not finished:
        data.update(state="interrupted" if cancelled else "failed", error="The test host did not finish; incomplete tasks cannot be treated as passed")
        for case in data["cases"]:
            if case["status"] == "running":
                case.update(status="cancelled" if cancelled else "failed", reason=data["error"])
            events = directory / case["case_id"] / "events.jsonl"
            if events.exists():
                entries = []
                for line in events.read_text(encoding="utf-8").splitlines():
                    try:
                        entries.append(json.loads(line))
                    except ValueError:
                        continue  # The final write may have been interrupted.
                case["log"] = f"{case['case_id']}/events.jsonl"
                case["evidence"] = [entry for entry in entries if entry.get("image")]
    data["stop_control"] = {"shortcut": "Ctrl+C", "global_on_windows": True,
                            "requested": cancelled, "forced_termination": stop.forced}
    if cancelled:
        data["state"] = "cancelled"
        data["error"] = "Stopped by Ctrl+C" + ("; the test host exceeded the shutdown deadline and was terminated" if stop.forced else "")
    write_report(directory, data)
    print(f"\nReport: {directory / 'report.html'}\nReview: python -m tests review {run_id}")
    if cancelled or data.get("state") in {"interrupted", "cancelled"}:
        return 130
    if data.get("state") == "failed" or any(c["status"] in {"failed", "timeout", "blocked"} for c in data["cases"]):
        return 1
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    parser = argparse.ArgumentParser(description="BAAS live task testing by config")
    parser.add_argument("command", nargs="?", choices=["review"])
    parser.add_argument("run_id", nargs="?")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--save-plan", type=Path)
    parser.add_argument("--list-configs", action="store_true")
    parser.add_argument("--list-tasks", action="store_true")
    parser.add_argument("--check", action="store_true", help="Check the environment without executing game tasks")
    parser.add_argument("--yes", action="store_true", help="Explicitly confirm real execution of the supplied --plan")
    args = parser.parse_args(argv)
    try:
        if args.command == "review":
            if not args.run_id:
                raise ValueError("review requires a run ID or report directory")
            path = Path(args.run_id)
            review(path if path.is_dir() else OUTPUT / args.run_id)
            return 0
        tasks = catalog(ROOT)
        if args.list_tasks:
            for task, label in tasks.items():
                print(f"{task}\t{label}")
            return 0
        if args.list_configs:
            for config_id in config_ids(ROOT):
                c = read_config(ROOT, config_id)
                print(f"{config_id}\t{c.get('name', config_id)}\t{server_label(c.get('server'))}")
            return 0
        if args.yes and not args.plan:
            raise ValueError("--yes requires an explicit --plan")
        data = json.loads(args.plan.read_text(encoding="utf-8-sig")) if args.plan else interactive(ROOT, tasks)
        jobs = load_plan(data, ROOT, tasks)
        if args.save_plan:
            args.save_plan.write_text(json.dumps(plan_data(jobs), ensure_ascii=False, indent=2), encoding="utf-8")
        summarize(ROOT, jobs)
        if args.check:
            return check(ROOT, jobs)
        if not args.yes and input("Type RUN to start real execution; anything else cancels: ").strip() != "RUN":
            print("Cancelled; no tasks were executed.")
            return 130
        with batch_lock(OUTPUT / ".batch.lock"):
            return launch(ROOT, jobs)
    except (ValueError, OSError, RuntimeError, ImportError, EOFError) as exc:
        print(f"Cannot start: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
