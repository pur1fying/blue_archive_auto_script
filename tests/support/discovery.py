import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.request import urlopen
import importlib.util
import sys


@dataclass
class Target:
    config_id: str
    kind: str = "unknown"
    identity: str = ""
    resources: list = field(default_factory=list)
    ready: bool = False
    reason: str = ""
    detail: dict = field(default_factory=dict)

    def data(self):
        return asdict(self)


def environment_problems(root, configs):
    required = ["fastapi", "cv2", "numpy", "adbutils", "uiautomator2", "psutil", "pygit2", "rich", "nacl", "cryptography"]
    if sys.version_info < (3, 11):
        required.append("tomli")
    if any(c.get("server") in {"日服PC端", "Steam国际服"} for c in configs):
        required.extend(["mss", "pyautogui"])
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    problems = ["Missing service dependencies in this Python environment: " + ", ".join(missing)] if missing else []
    binary = root / "core/ocr/baas_ocr_client/bin" / ("BAAS_ocr_server.exe" if os.name == "nt" else "BAAS_ocr_server")
    if not binary.is_file():
        problems.append("OCR executable is missing: " + str(binary))
    return problems


def desktop_titles(root, config):
    static = json.loads((root / "config/static.json").read_text(encoding="utf-8"))
    server = "JP" if config["server"] == "日服PC端" else "Global"
    titles = static["PC_app_process_name"][server]
    return [titles] if isinstance(titles, str) else titles


def discover(root, config_id, config):
    target = Target(config_id)
    try:
        server = config.get("server", "")
        if server in {"日服PC端", "Steam国际服"}:
            target.kind = "desktop"
            target.resources = ["desktop"]
            if os.name != "nt":
                raise ValueError("Desktop clients require Windows")
            import pyautogui
            titles = desktop_titles(root, config)
            windows = {w._hWnd: w for title in titles for w in pyautogui.getWindowsWithTitle(title) if w.title == title}
            if len(windows) != 1:
                raise ValueError(f"Found {len(windows)} matching windows; keep exactly one target client open: {titles}")
            hwnd, window = next(iter(windows.items()))
            target.identity = f"window:{hwnd}"
            target.detail = {"title": window.title, "hwnd": hwnd}
        else:
            target.kind = "android"
            from adbutils import adb
            devices = adb.device_list()
            serial = str(config.get("adbPort", "auto"))
            host = str(config.get("adbIP", "127.0.0.1"))
            if serial == "auto":
                if len(devices) != 1:
                    raise ValueError("ADB auto-selection is ambiguous; specify a device in the original config")
                serial = devices[0].serial
            elif serial.isdigit():
                serial = f"{host}:{serial}"
            device = next((d for d in devices if d.serial == serial), None)
            if device is None:
                raise ValueError(f"Device is not connected: {serial}; open the client and connect ADB first")
            # Duplicate properties conservatively serialize devices rather than
            # allowing two profiles to control the same device through aliases.
            hardware = device.getprop("ro.serialno") or device.getprop("ro.boot.serialno")
            target.identity = f"android:{hardware}" if hardware else "android:unresolved"
            if "nemu" in {config.get("control_method"), config.get("screenshot_method")}:
                from core.device.nemu_client import NemuClient
                if not serial.startswith(("127.0.0.1:", "localhost:")):
                    raise ValueError("Nemu IPC requires a local emulator; check the device address")
                instance_id = NemuClient.serial_to_id(serial)
                if instance_id is not None:
                    target.identity = f"nemu:local:{instance_id}"
            target.resources = [target.identity]
            target.detail = {"serial": serial, "hardware_serial": hardware or "unknown"}
            packages = json.loads((root / "config/static.json").read_text(encoding="utf-8"))["package_name"]
            expected = packages.get(server)
            if not expected:
                raise ValueError("Select a supported game server explicitly in the config")
            current = device.app_current()
            actual = current.get("package") if isinstance(current, dict) else getattr(current, "package", None)
            if actual != expected:
                raise ValueError(f"Game is not open on the device: expected {expected}, current {actual}")
        target.ready = True
    except Exception as exc:
        target.reason = str(exc)
    return target


def external_conflicts(root):
    """Fail closed for active/unknown BAAS controllers, without stopping them."""
    import psutil
    problems, inspected = [], set()
    own_processes = {os.getpid()} | {p.pid for p in psutil.Process().parents()}
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        if process.pid in own_processes:
            continue
        try:
            args = process.info.get("cmdline") or []
            if "tests.runner.worker" in args:
                problems.append(f"Another test host ({process.pid}) has not exited")
                continue
            if not any("main.service.py" in a or "service.app:app" == a for a in args):
                if any(Path(a).name == "window.py" for a in args):
                    problems.append(f"Legacy GUI process {process.pid} is running; close it because task ownership cannot be verified")
                continue
            port = int(args[args.index("--port") + 1]) if "--port" in args else 8190
            if port in inspected:
                continue
            inspected.add(port)
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                    health = json.load(response)
                if any(s.get("running") for s in health.get("statuses", {}).values()):
                    problems.append(f"Backend on port {port} has active tasks; stop other BAAS automation first")
            except Exception:
                problems.append(f"Cannot verify task ownership for backend port {port}")
        except (psutil.Error, ValueError, IndexError):
            continue
    return problems
