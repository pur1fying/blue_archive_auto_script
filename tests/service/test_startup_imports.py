from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from service.runtime import ServiceRuntime


def test_service_ready_does_not_load_task_or_image_engines():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
from pathlib import Path
from service.runtime import ServiceRuntime
runtime = ServiceRuntime(Path.cwd())
runtime._ensure_main_sync()
assert runtime.get_main_log_queue() is not None
assert 'core.Baas_thread' not in sys.modules
assert 'module.cafe_reward' not in sys.modules
assert 'cv2' not in sys.modules
assert 'core.ocr.ocr' not in sys.modules
"""],
        cwd=root, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_concurrent_main_initialization_constructs_once(monkeypatch, tmp_path):
    import service.runtime as runtime_module

    constructed = []

    class Main:
        def __init__(self, **kwargs):
            time.sleep(0.01)
            constructed.append(self)

    monkeypatch.setattr(runtime_module, "apply_startup_injections", lambda: None)
    monkeypatch.setitem(sys.modules, "main", SimpleNamespace(Main=Main))
    runtime = ServiceRuntime(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _: runtime._ensure_main_sync(), range(8)))
    assert constructed == [runtime._main]
