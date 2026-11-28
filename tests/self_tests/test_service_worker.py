"""Exercise production service thread ownership without game input."""
import asyncio
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from service.runtime import ConfigSession, ServiceRuntime, _default_status


class ServiceWorkerTests(unittest.IsolatedAsyncioTestCase):
    def setup_runtime(self, gate=None, fail_init=False, handler=None):
        self.events = []
        self.workers = []
        self.entered = threading.Event()
        self.stopped = threading.Event()
        self.closed = threading.Event()
        self.exceptions = []
        self.hook = patch('threading.excepthook', side_effect=lambda args: self.exceptions.append(args.exc_value))
        self.hook.start()
        self.addCleanup(self.hook.stop)
        self.runtime = ServiceRuntime(Path.cwd(), asyncio.get_running_loop())
        outer = self

        class Provider:
            def __init__(self):
                self.handles = threading.local()
                self.handles.srcdc = object()
                self.owner = threading.current_thread()

            def grab(self):
                # Equivalent thread-local constraint to MSS on Windows.
                return self.handles.srcdc

            def close(self):
                outer.assertIs(threading.current_thread(), self.owner)
                self.grab()
                outer.events.append(('close', threading.current_thread()))
                outer.closed.set()

        class Baas:
            logger = SimpleNamespace()
            scheduler = object()  # Existing readiness must not bypass a new init.
            flag_run = True
            screenshot = None

            def init_all_data(self):
                thread = threading.current_thread()
                outer.workers.append(thread)
                outer.events.append(('init', thread))
                outer.entered.set()
                if gate is not None and not gate.wait(3):
                    raise TimeoutError('Test initialization gate was not released')
                self.flag_run = True
                self.scheduler = object()
                self.screenshot = SimpleNamespace(screenshot_instance=Provider())
                return not fail_init

            def send(self, command, task=None):
                if command == 'stop':
                    self.flag_run = False
                    outer.stopped.set()
                    return
                outer.events.append((command, threading.current_thread()))
                self.screenshot.screenshot_instance.grab()
                return handler(self) if handler else True

        self.baas = Baas()
        self.session = ConfigSession('jppc', None, self.baas, None, None, None)
        self.runtime._sessions['jppc'] = self.session
        self.runtime._statuses['jppc'] = _default_status('jppc')

    async def join_worker(self):
        self.assertTrue(await asyncio.to_thread(self.closed.wait, 3))
        await asyncio.to_thread(self.workers[-1].join, 3)
        self.assertFalse(self.workers[-1].is_alive())

    async def test_each_single_task_initializes_executes_and_closes_on_its_worker(self):
        self.setup_runtime()
        for task in ('group', 'mail'):
            self.closed.clear()
            response = await self.runtime.solve_task('jppc', task)
            self.assertEqual(response['status'], 'ok')
            await self.join_worker()
        self.assertEqual([e[0] for e in self.events], ['init', 'solve', 'close'] * 2)
        for start in (0, 3):
            self.assertTrue(all(e[1] is self.events[start][1] for e in self.events[start:start + 3]))
        self.assertIsNot(self.workers[0], self.workers[1])
        self.assertEqual(self.exceptions, [])

    async def test_scheduler_uses_one_worker_for_initialization_and_execution(self):
        self.setup_runtime()
        self.assertEqual((await self.runtime.start_scheduler('jppc'))['status'], 'started')
        await self.join_worker()
        self.assertEqual([e[0] for e in self.events], ['init', 'start', 'close'])
        self.assertTrue(all(e[1] is self.workers[0] for e in self.events))

    async def test_initialization_failure_closes_handles_without_dispatch(self):
        self.setup_runtime(fail_init=True)
        await self.runtime.solve_task('jppc', 'group')
        await self.join_worker()
        self.assertEqual([e[0] for e in self.events], ['init', 'close'])
        self.assertIsNone(self.baas.scheduler)
        self.assertEqual(self.runtime.current_status()['jppc']['exit_code'], 1)
        self.assertIsInstance(self.exceptions[0], RuntimeError)

    async def test_stop_during_init_survives_flag_reset_and_prevents_dispatch(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        self.setup_runtime(gate=gate)
        await self.runtime.solve_task('jppc', 'group')
        self.assertTrue(await asyncio.to_thread(self.entered.wait, 2))
        self.assertEqual((await self.runtime.solve_task('jppc', 'mail'))['status'], 'already-running')
        stopping = asyncio.create_task(self.runtime.stop_scheduler('jppc'))
        self.assertTrue(await asyncio.to_thread(self.stopped.wait, 2))
        gate.set()
        self.assertEqual((await stopping)['status'], 'stopped')
        await self.join_worker()
        self.assertEqual([e[0] for e in self.events], ['init', 'close'])
        self.assertFalse(self.baas.flag_run)

    async def test_scheduler_stop_during_initialization_prevents_start(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        self.setup_runtime(gate=gate)
        await self.runtime.start_scheduler('jppc')
        self.assertTrue(await asyncio.to_thread(self.entered.wait, 2))
        stopping = asyncio.create_task(self.runtime.stop_scheduler('jppc'))
        self.assertTrue(await asyncio.to_thread(self.stopped.wait, 2))
        gate.set()
        await stopping
        await self.join_worker()
        self.assertNotIn('start', [e[0] for e in self.events])

    async def test_plugin_handler_uses_the_same_initialized_worker(self):
        self.setup_runtime()
        seen = []
        def handler(baas):
            baas.screenshot.screenshot_instance.grab()
            seen.append(threading.current_thread())
            return {'verified': True}
        result = await self.runtime._run_plugin_owned_task('jppc', 'test', handler=handler)
        await self.join_worker()
        self.assertEqual(result, {'verified': True})
        self.assertIs(seen[0], self.workers[0])

    async def test_plugin_cancellation_during_initialization_does_not_execute(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        self.setup_runtime(gate=gate)
        invoked = []
        task = asyncio.create_task(self.runtime._run_plugin_owned_task('jppc', 'test', handler=lambda b: invoked.append(b)))
        self.assertTrue(await asyncio.to_thread(self.entered.wait, 2))
        task.cancel()
        self.assertTrue(await asyncio.to_thread(self.stopped.wait, 2))
        gate.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await self.join_worker()
        self.assertEqual(invoked, [])


if __name__ == '__main__':
    unittest.main()
