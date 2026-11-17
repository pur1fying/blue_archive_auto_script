import asyncio
import json
import tempfile
import threading
import unittest
import io
import ast
import re
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.runner.backend import ProductionBackend
from tests.runner.evidence import Recorder
from tests.runner.executor import Executor, cases_for
from tests.runner.model import Job, load_plan, plan_data, SERVER_LABELS
from tests.runner.report import write_report, review, LEGACY_REVIEW
from tests.runner.resources import Resources, ResourceBlocked
from tests.support.discovery import Target
from tests.support.privacy import redact, secrets_in
from tests.support.locking import batch_lock
from tests.tasks.catalog import catalog, no_work_reason, settings_for

ROOT = Path(__file__).resolve().parents[2]


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config/cn").mkdir(parents=True)
        (self.root / "config/cn/config.json").write_text("{}")

    def test_plan_roundtrip_and_order(self):
        jobs = [Job("cn", ("lesson", "cafe_reward", "lesson"), 42)]
        self.assertEqual(load_plan(plan_data(jobs), self.root, {"lesson": "", "cafe_reward": ""}), jobs)

    def test_batch_lock_is_exclusive_and_released(self):
        path = self.root / "runner.lock"
        with batch_lock(path):
            with self.assertRaises(RuntimeError):
                with batch_lock(path):
                    self.fail("second batch acquired the lock")
        with batch_lock(path):
            pass

    def test_own_venv_launcher_is_not_an_external_test_host(self):
        from tests.support.discovery import external_conflicts
        own_launcher = SimpleNamespace(pid=1111, info={"cmdline": ["python.exe", "-m", "tests.runner.worker"]})
        other = SimpleNamespace(pid=2222, info={"cmdline": ["python.exe", "-m", "tests.runner.worker"]})
        with patch("psutil.Process", return_value=SimpleNamespace(parents=lambda: [own_launcher])), \
             patch("psutil.process_iter", return_value=[own_launcher, other]):
            self.assertEqual(external_conflicts(self.root), ["Another test host (2222) has not exited"])

    def test_git_metadata_timeout_terminates_only_owned_process(self):
        from tests.runner.worker import read_git
        process = SimpleNamespace(pid=1234, args=["git", "status"],
                                  wait=unittest.mock.Mock(side_effect=[subprocess.TimeoutExpired(["git"], 1), 0]),
                                  kill=unittest.mock.Mock())
        with patch("tests.runner.worker.subprocess.Popen", return_value=process), \
             patch("psutil.Process", return_value=SimpleNamespace(children=lambda recursive: [])):
            with self.assertRaises(subprocess.TimeoutExpired):
                read_git(self.root, "status", timeout=1)
        process.kill.assert_called_once()

    def test_bad_plans_do_not_run(self):
        for entry in [{"config_id": "../cn", "tasks": ["lesson"]},
                      {"config_id": "cn", "tasks": []},
                      {"config_id": "cn", "tasks": ["unknown"]},
                      {"config_id": "cn", "tasks": ["lesson"], "timeout_seconds": -1},
                      {"config_id": "cn", "tasks": ["lesson"], "timeout_seconds": float("nan")}]:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                load_plan({"version": 1, "jobs": [entry]}, self.root, {"lesson": ""})
        with self.assertRaises(ValueError):
            load_plan({"version": 1, "jobs": [{"config_id": "cn", "tasks": ["lesson"]}] * 2}, self.root, {"lesson": ""})

    def test_catalog_matches_real_tasks(self):
        tasks = catalog(ROOT)
        self.assertIn("lesson", tasks)
        self.assertIn("cafe_reward", tasks)
        self.assertIn("refresh_uiautomator2", tasks)

    def test_framework_messages_are_english(self):
        # These Chinese values are existing config keys and legacy report data,
        # not framework-authored output messages.
        allowed = set(SERVER_LABELS) | set(LEGACY_REVIEW)
        for directory in ["runner", "support", "tasks"]:
            for path in (ROOT / "tests" / directory).glob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.search(r"[\u4e00-\u9fff]", node.value):
                        self.assertIn(node.value, allowed, f"Non-English message at {path}:{node.lineno}")
        self.assertTrue(all(label.isascii() for label in catalog(ROOT).values()))

    def test_legacy_review_values_are_preserved_in_english(self):
        cases = cases_for([Job("cn", ("lesson", "cafe_reward", "mail"))])
        for case, legacy in zip(cases, ["待复核", "通过", "不通过"]):
            case["review"] = legacy
        write_report(self.root, {"state": "finished", "cases": cases})
        data = json.loads((self.root / "result.json").read_text(encoding="utf-8"))
        self.assertEqual([c["review"] for c in data["cases"]], ["pending", "passed", "failed"])

    def test_no_tickets_is_not_success_or_program_error(self):
        self.assertIsNotNone(no_work_reason("lesson", ["No Lesson Tickets"]))
        self.assertIsNone(no_work_reason("lesson", ["Complete one lesson.", "No Tickets."]))
        self.assertIsNone(no_work_reason("cafe_reward", ["No interaction found"]))
        self.assertIsNotNone(no_work_reason("scrimmage", ["INADEQUATE AP", "Scrimmage task status : [False, False, False]"]))
        self.assertIsNone(no_work_reason("scrimmage", ["INADEQUATE AP", "Scrimmage task status : [True, False, False]"]))
        self.assertIsNotNone(no_work_reason("joint_firing_drill", ["No drill open."]))
        self.assertIsNotNone(no_work_reason("explore_activity_story", ["Current activity is not supported"]))

    def test_action_summary_includes_legacy_shop_fields(self):
        values = {"CommonShopList": [1, 0], "CommonShopRefreshTime": 2,
                  "purchase_lesson_ticket_times": 0, "push_telegram_token": "secret"}
        selected = settings_for(ROOT, ["common_shop"], values)
        self.assertEqual(selected["CommonShopRefreshTime"], 2)
        self.assertEqual(selected["CommonShopList"], [1, 0])
        self.assertNotIn("push_telegram_token", selected)

    def test_selected_plan_has_requested_clients_and_task_order(self):
        path = ROOT / "tests/fixtures/selected-client-plan.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual([j["config_id"] for j in data["jobs"]], ["cn", "global", "jppc"])
        for entry in data["jobs"]:
            self.assertEqual(len(entry["tasks"]), 15)
            self.assertEqual(entry["tasks"][0], "group")
            self.assertEqual(entry["tasks"][-1], "joint_firing_drill")
            self.assertEqual(entry["tasks"][9:11], ["collect_reward", "normal_task"])

    def test_evidence_keeps_the_original_frame(self):
        import numpy as np
        import cv2
        cases = cases_for([Job("cn", ("lesson",))])
        recorder = Recorder(self.root, cases, ["sensitive-token"])
        frame = np.full((8, 8, 3), 23, dtype=np.uint8)
        recorder.capture(cases[0]["case_id"], "Stage ended sensitive-token", frame)
        recorder.system({"message": "OCR failure sensitive-token", "level": 3})
        frame[:] = 200
        recorder.close()
        saved = cv2.imread(str(self.root / cases[0]["evidence"][0]["image"]))
        self.assertEqual(int(saved[0, 0, 0]), 23)
        self.assertNotIn("sensitive-token", (self.root / cases[0]["log"]).read_text(encoding="utf-8"))
        self.assertNotIn("sensitive-token", (self.root / "startup.jsonl").read_text(encoding="utf-8"))
        recorder.system({"message": "late initialization log"})
        self.assertEqual(recorder.system_dropped, 1)
        self.assertTrue(recorder.queue.empty())

    def test_secrets_and_html_are_not_exposed(self):
        config = {"push_telegram_token": "sensitive-token", "name": "cn", "nested": {"password": "password123"}}
        text = redact("token=sensitive-token password=password123", secrets_in(config))
        self.assertNotIn("sensitive-token", text)
        self.assertNotIn("password123", text)
        case = cases_for([Job("cn", ("lesson",))])[0]
        case["reason"] = '<script>alert("x")</script>'
        write_report(self.root, {"run_id": "test", "cases": [case]})
        content = (self.root / "report.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", content)
        self.assertIn("pending", content)

    def test_webhooks_and_custom_push_payloads_are_redacted(self):
        config = {"push_feishu": "https://feishu.example/hook/credential",
                  "push_serverchan": "SCT-credential", "push_json": '{"url":"https://private.example/push","headers":{"Authorization":"Bearer private-token"}}'}
        text = "SCT-credential Bearer private-token https://private.example/push"
        redacted = redact(text, secrets_in(config))
        self.assertNotIn("credential", redacted)
        self.assertNotIn("private-token", redacted)
        self.assertNotIn("private.example", redacted)
        self.assertEqual(set(redact(config).values()), {"[REDACTED]"})

    def test_review_does_not_pass_cancelled_case(self):
        case = cases_for([Job("cn", ("lesson",))])[0]
        case["status"] = "cancelled"
        write_report(self.root, {"state": "finished", "cases": [case]})
        with patch("builtins.input", side_effect=AssertionError("must not prompt for pass")):
            review(self.root)
        result = json.loads((self.root / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["cases"][0]["review"], "pending")


class SchedulingTests(unittest.IsolatedAsyncioTestCase):
    async def test_desktop_serializes_and_device_runs_in_parallel(self):
        pool = Resources()
        desktop_entered, release, android_entered = asyncio.Event(), asyncio.Event(), asyncio.Event()
        second_entered = asyncio.Event()

        async def desktop_one():
            locks = await pool.acquire(["desktop"])
            desktop_entered.set()
            await release.wait()
            pool.release(locks)

        async def desktop_two():
            await desktop_entered.wait()
            locks = await pool.acquire(["desktop"])
            second_entered.set()
            pool.release(locks)

        async def android():
            await desktop_entered.wait()
            locks = await pool.acquire(["android:1"])
            android_entered.set()
            pool.release(locks)

        tasks = [asyncio.create_task(fn()) for fn in [desktop_one, desktop_two, android]]
        await asyncio.wait_for(android_entered.wait(), 1)
        self.assertFalse(second_entered.is_set())
        release.set()
        await asyncio.gather(*tasks)
        self.assertTrue(second_entered.is_set())

    async def test_poisoned_resource_cannot_be_reused(self):
        pool = Resources()
        locks = await pool.acquire(["desktop"])
        pool.poison(["desktop"], "still stopping")
        pool.release(locks)
        with self.assertRaises(ResourceBlocked):
            await pool.acquire(["desktop"])
        other = await pool.acquire(["android:1"])
        pool.release(other)

    async def test_failure_isolates_configuration_and_no_work_continues(self):
        jobs = [Job("bad", ("lesson", "cafe_reward")), Job("good", ("lesson", "cafe_reward"))]
        cases = cases_for(jobs)
        with tempfile.TemporaryDirectory() as path:
            recorder = Recorder(Path(path), cases)
            calls = []

            class Backend:
                async def run_case(self, job, case, cancel):
                    calls.append((job.config_id, case["task_id"]))
                    if job.config_id == "bad":
                        return {"status": "failed"}
                    if case["task_id"] == "lesson":
                        recorder.capture(case["case_id"], "No Lesson Tickets")
                    return {"status": "completed"}

            targets = {j.config_id: Target(j.config_id, "android", j.config_id, [j.config_id], True) for j in jobs}
            runner = Executor(jobs, targets, Backend(), recorder, asyncio.Event(), lambda event: None, lambda config_id: {})
            await runner.run()
            await asyncio.to_thread(recorder.close)
        self.assertEqual([c["status"] for c in cases], ["failed", "not_run", "unexecuted", "completed"])
        self.assertNotIn(("bad", "cafe_reward"), calls)
        self.assertTrue(all(c["review"] == "pending" for c in cases))

    async def test_cancellation_before_start_runs_nothing(self):
        jobs = [Job("cn", ("lesson",))]
        with tempfile.TemporaryDirectory() as path:
            cases = cases_for(jobs)
            recorder = Recorder(Path(path), cases)
            cancel = asyncio.Event()
            cancel.set()
            runner = Executor(jobs, {"cn": Target("cn", ready=True)}, None, recorder, cancel, lambda event: None, lambda _: {})
            await runner.run()
            await asyncio.to_thread(recorder.close)
            self.assertEqual(cases[0]["status"], "not_run")


class BackendTests(unittest.IsolatedAsyncioTestCase):
    async def test_emergency_stop_sets_flags_without_waiting_for_event_loop(self):
        backend = ProductionBackend(ROOT, None)
        sessions = [SimpleNamespace(stop_event=threading.Event(), baas=SimpleNamespace(flag_run=True)) for _ in range(2)]
        backend.runtime = SimpleNamespace(_sessions={str(i): s for i, s in enumerate(sessions)})
        backend.request_stop()
        self.assertTrue(backend.stop_requested.is_set())
        self.assertTrue(all(s.stop_event.is_set() and not s.baas.flag_run for s in sessions))

    def fake(self):
        queue = asyncio.Queue()
        self.ack = asyncio.Event()
        self.done = asyncio.Event()
        self.stopped = False
        state = {"running": False}
        baas = SimpleNamespace(logger=SimpleNamespace(), latest_img_array=None, flag_run=True, scheduler=object(),
                               init_all_data=lambda: True, send=lambda *args: True)
        session = SimpleNamespace(baas=baas, thread=None)
        outer = self

        class Runtime:
            async def get_session(self, config): return session
            async def subscribe_status(self): return queue
            def unsubscribe_status(self, q): pass
            def current_status(self): return {"cn": state.copy()}

            async def solve_task(self, config, task, _plugin_cancel):
                if baas.init_all_data() is False:
                    state.update(running=False, exit_code=1)
                    return {"status": "ok", "result": 0}
                baas.send("solve", task)
                state.update(running=True, exit_code=None)
                session.thread = SimpleNamespace(is_alive=lambda: not outer.done.is_set())
                outer.ack.set()
                return {"status": "ok", "result": 0}

            async def stop_scheduler(self, config):
                outer.stopped = True
                outer.done.set()
                baas.flag_run = False
                state["running"] = False
                session.thread = None
                queue.put_nowait(state.copy())
                return {"status": "stopped"}

        def finish():
            self.done.set()
            state["running"] = False
            session.thread = None
            queue.put_nowait(state.copy())
        return Runtime(), finish

    async def test_start_ack_is_not_completion(self):
        runtime, finish = self.fake()
        with tempfile.TemporaryDirectory() as path:
            cases = cases_for([Job("cn", ("lesson",))])
            recorder = Recorder(Path(path), cases)
            backend = ProductionBackend(Path(path), recorder)
            backend.runtime = runtime
            task = asyncio.create_task(backend.run_case(Job("cn", ("lesson",)), cases[0], asyncio.Event()))
            await self.ack.wait()
            self.assertFalse(task.done())
            finish()
            result = await task
            await asyncio.to_thread(recorder.close)
        self.assertEqual(result["status"], "completed")

    async def test_changed_target_is_blocked_before_task_dispatch(self):
        runtime, _ = self.fake()
        session = await runtime.get_session("cn")
        session.baas.scheduler = None
        initialization = []
        def initialize():
            initialization.append("cn")
            session.baas.scheduler = object()
            session.baas.connection = SimpleNamespace(serial="different-device")
            return True
        session.baas.init_all_data = initialize
        with tempfile.TemporaryDirectory() as path:
            cases = cases_for([Job("cn", ("lesson",))])
            cases[0]["target"] = {"detail": {"serial": "expected-device"}}
            recorder = Recorder(Path(path), cases)
            backend = ProductionBackend(Path(path), recorder)
            backend.runtime = runtime
            result = await backend.run_case(Job("cn", ("lesson",)), cases[0], asyncio.Event())
            await asyncio.to_thread(recorder.close)
        self.assertEqual(initialization, ["cn"])
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(self.ack.is_set())

    async def test_timeout_requests_stop(self):
        runtime, _ = self.fake()
        with tempfile.TemporaryDirectory() as path:
            cases = cases_for([Job("cn", ("lesson",))])
            recorder = Recorder(Path(path), cases)
            backend = ProductionBackend(Path(path), recorder)
            backend.runtime = runtime
            result = await backend.run_case(Job("cn", ("lesson",), 0.01), cases[0], asyncio.Event())
            await asyncio.to_thread(recorder.close)
        self.assertTrue(self.stopped)
        self.assertEqual(result["status"], "timeout")
        self.assertTrue(result["quiescent"])

    async def test_cancel_is_not_reported_as_success(self):
        runtime, _ = self.fake()
        with tempfile.TemporaryDirectory() as path:
            cases = cases_for([Job("cn", ("lesson",))])
            recorder = Recorder(Path(path), cases)
            backend = ProductionBackend(Path(path), recorder)
            backend.runtime = runtime
            cancel = asyncio.Event()
            result_task = asyncio.create_task(backend.run_case(Job("cn", ("lesson",)), cases[0], cancel))
            await self.ack.wait()
            cancel.set()
            result = await result_task
            await asyncio.to_thread(recorder.close)
        self.assertEqual(result["status"], "cancelled")
        self.assertTrue(self.stopped)


class HostTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_clients_generate_report_without_starting_service(self):
        from tests.runner.worker import run
        gate = threading.Event()

        class Input:
            def __iter__(self):
                gate.wait()
                return iter(())

        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            (root / "config/cn").mkdir(parents=True)
            (root / "config/cn/config.json").write_text('{"server":"CN"}')
            plan = root / "plan.json"
            plan.write_text(json.dumps({"version": 1, "jobs": [{"config_id": "cn", "tasks": ["lesson", "cafe_reward"]}]}))
            output = root / "report"
            output.mkdir()
            with patch("tests.runner.worker.catalog", return_value={"lesson": "Lessons", "cafe_reward": "Cafe"}), \
                 patch("tests.runner.worker.environment_problems", return_value=[]), \
                 patch("tests.runner.worker.external_conflicts", return_value=[]), \
                 patch("tests.runner.worker.discover", return_value=Target("cn", reason="not open")), \
                 patch("tests.runner.worker.ProductionBackend.start") as start, \
                 patch("sys.stdin", Input()), redirect_stdout(io.StringIO()):
                try:
                    await run(root, plan, output)
                finally:
                    gate.set()
            start.assert_not_called()
            result = json.loads((output / "result.json").read_text(encoding="utf-8"))
            self.assertEqual([c["status"] for c in result["cases"]], ["blocked", "not_run"])
            self.assertTrue((output / "report.html").exists())

    async def test_waiting_session_can_be_cancelled(self):
        with tempfile.TemporaryDirectory() as path:
            cases = cases_for([Job("cn", ("lesson",))])
            recorder = Recorder(Path(path), cases)
            entered = asyncio.Event()
            async def session(_):
                entered.set()
                await asyncio.Event().wait()
            backend = ProductionBackend(Path(path), recorder)
            backend.runtime = SimpleNamespace(get_session=session)
            cancel = asyncio.Event()
            result_task = asyncio.create_task(backend.run_case(Job("cn", ("lesson",)), cases[0], cancel))
            await entered.wait()
            cancel.set()
            result = await result_task
            await asyncio.to_thread(recorder.close)
        self.assertEqual(result["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
