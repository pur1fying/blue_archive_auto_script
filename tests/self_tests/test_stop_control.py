import ctypes
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from tests.support.stop_control import GlobalCtrlC, TestStopControl, terminate_test_host


class StopControlTests(unittest.TestCase):
    def test_cli_persists_cancelled_report_when_the_worker_is_unresponsive(self):
        from tests.runner.cli import _launch_host
        from tests.runner.model import Job
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'config/cn').mkdir(parents=True)
            (root / 'config/cn/config.json').write_text('{"server":"CN"}')
            directory = root / 'run'
            directory.mkdir()
            stop = TestStopControl(root, directory, grace_seconds=.4, release_input=lambda: None)
            program = '''import json, pathlib, sys, threading
p = pathlib.Path(sys.argv[1])
data = {'run_id': p.name, 'state': 'running', 'cases': [{'case_id': 'case-001-001', 'config_id': 'cn', 'task_id': 'group', 'status': 'running'}]}
(p / 'result.json').write_text(json.dumps(data))
print('BAAS_TEST_EVENT ' + json.dumps({'type':'case','config_id':'cn','task_id':'group','status':'running'}), flush=True)
threading.Event().wait()
'''
            original_popen = subprocess.Popen
            def launch_dummy(*args, **kwargs):
                kwargs.pop('env', None)
                process = original_popen([sys._base_executable, '-u', '-c', program, str(directory)], **kwargs)
                stop.request()
                return process
            with patch('tests.runner.cli.subprocess.Popen', side_effect=launch_dummy), redirect_stdout(io.StringIO()):
                code = _launch_host(root, [Job('cn', ('group',))], directory, directory / 'plan.json', stop)
            report = json.loads((directory / 'result.json').read_text(encoding='utf-8'))
            self.assertEqual(code, 130)
            self.assertEqual(report['state'], 'cancelled')
            self.assertEqual(report['cases'][0]['status'], 'cancelled')
            self.assertTrue(report['stop_control']['forced_termination'])

    def start_child(self, program):
        process = subprocess.Popen([sys._base_executable, '-u', '-c', program], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        def close():
            if process.poll() is None:
                process.kill()
            process.wait(timeout=3)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        self.addCleanup(close)
        self.assertEqual(process.stdout.readline().strip(), 'READY')
        return process

    def test_one_press_requests_cooperative_shutdown(self):
        process = self.start_child("import sys; print('READY', flush=True); line=sys.stdin.readline(); print(line.strip(), flush=True)")
        releases = []
        stop = TestStopControl(Path.cwd(), Path.cwd(), grace_seconds=1, release_input=lambda: releases.append(True))
        self.addCleanup(stop.close)
        stop.attach(process)
        stop.request()
        process.wait(timeout=2)
        stop.close()
        self.assertIn('"type":"cancel"', process.stdout.read())
        self.assertFalse(stop.forced)
        self.assertEqual(releases, [])

    def test_one_press_terminates_an_unresponsive_host_without_second_press(self):
        process = self.start_child("import threading; print('READY', flush=True); threading.Event().wait()")
        released = threading.Event()
        stop = TestStopControl(Path.cwd(), Path.cwd(), grace_seconds=.1, release_input=released.set)
        self.addCleanup(stop.close)
        stop.attach(process)
        stop.request()
        process.wait(timeout=2)
        self.assertTrue(released.wait(1))
        self.assertTrue(stop.forced)

    def test_second_press_skips_grace_period(self):
        process = self.start_child("import threading; print('READY', flush=True); threading.Event().wait()")
        stop = TestStopControl(Path.cwd(), Path.cwd(), grace_seconds=30, release_input=lambda: None)
        self.addCleanup(stop.close)
        stop.attach(process)
        stop.request()
        stop.request()
        process.wait(timeout=2)
        self.assertTrue(stop.forced)

    def test_normal_completion_does_not_trigger_input_release(self):
        process = self.start_child("import sys; print('READY', flush=True); sys.stdin.readline()")
        stop = TestStopControl(Path.cwd(), Path.cwd(), release_input=lambda: self.fail('No input release expected'))
        stop.attach(process)
        stop.close()
        self.assertIsNone(process.poll())
        self.assertFalse(stop.requested)

    @unittest.skipUnless(os.name == 'nt', 'Windows global hotkey')
    def test_windows_hotkey_message_and_unregister_without_keyboard_input(self):
        triggered = threading.Event()
        with GlobalCtrlC(triggered.set) as hotkey:
            # Exercise the registered message loop without injecting a physical key.
            self.assertTrue(ctypes.windll.user32.PostThreadMessageW(hotkey.thread_id, hotkey.WM_HOTKEY, hotkey.HOTKEY_ID, 0))
            self.assertTrue(triggered.wait(2))
        self.assertFalse(hotkey.thread.is_alive())
        # Registration must be released so the next batch can use the same key.
        with GlobalCtrlC(lambda: None) as next_hotkey:
            self.assertIsNone(next_hotkey.error)

    def test_hotkey_registration_failure_blocks_launch(self):
        def unavailable(hotkey):
            hotkey.error = OSError('Key is already registered')
            hotkey.ready.set()
        with patch('tests.support.stop_control.os.name', 'nt'), patch.object(GlobalCtrlC, '_listen', unavailable):
            with self.assertRaisesRegex(RuntimeError, 'tests were not started'):
                with GlobalCtrlC(lambda: None):
                    self.fail('Must not enter the test launch scope')

    def test_forced_shutdown_excludes_game_and_unrelated_python_children(self):
        import psutil
        from unittest.mock import Mock
        root = Path.cwd()
        output = root / 'output/test_runs/owned'
        process = Mock(pid=100)
        process.poll.return_value = None
        owned = Mock(pid=101)
        owned.cmdline.return_value = ['python', '-m', 'tests.runner.worker', '--output', str(output)]
        owned.ppid.return_value = 100
        owned.exe.return_value = str(root / '.venv/Scripts/python.exe')
        unrelated = Mock(pid=102)
        unrelated.cmdline.return_value = ['python', 'another_script.py']
        unrelated.ppid.return_value = 100
        unrelated.exe.return_value = str(root / '.venv/Scripts/python.exe')
        game = Mock(pid=103)
        game.cmdline.return_value = ['BlueArchive.exe']
        game.ppid.return_value = 101
        game.exe.return_value = 'E:/game/BlueArchive.exe'
        parent = Mock()
        parent.children.return_value = [owned, unrelated, game]
        with patch.object(psutil, 'Process', return_value=parent):
            terminate_test_host(process, root, output)
        owned.kill.assert_called_once()
        process.kill.assert_called_once()
        unrelated.kill.assert_not_called()
        game.kill.assert_not_called()


if __name__ == '__main__':
    unittest.main()
