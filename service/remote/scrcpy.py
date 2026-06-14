"""
This module is modified from leng-yue/py-scrcpy-client.
Reference URL: https://github.com/leng-yue/py-scrcpy-client
"""
import asyncio
import inspect
import shlex
import socket
import threading
from pathlib import Path
from time import sleep
from typing import Any, Callable, Optional

import websockets
from websockets import ClientConnection

try:
    from adbutils import AdbDevice, AdbError, AdbTimeout, ForwardItem
except ModuleNotFoundError:  # pragma: no cover - remote control dependency is optional at import time
    AdbDevice = Any  # type: ignore
    AdbError = RuntimeError  # type: ignore
    AdbTimeout = TimeoutError  # type: ignore
    ForwardItem = Any  # type: ignore


# ---------------------------------------------------------------------------
# ws-scrcpy server constants
# ---------------------------------------------------------------------------
EVENT_INIT = "init"
EVENT_DISCONNECT = "disconnect"
EVENT_STREAM = "stream"
LOCK_SCREEN_ORIENTATION_UNLOCKED = -1

SCRCPY_SERVER_PACKAGE = "com.genymobile.scrcpy.Server"
SCRCPY_SERVER_VERSION = "1.19-ws7"
SCRCPY_SERVER_TYPE = "web"
SCRCPY_LOG_LEVEL = "ERROR"
SCRCPY_SERVER_PORT = 8886
SCRCPY_LISTENS_ON_ALL_INTERFACES = "true"

SCRCPY_TEMP_PATH = "/data/local/tmp"
SCRCPY_SERVER_JAR_NAME = "scrcpy-server.jar"
SCRCPY_REMOTE_JAR = f"{SCRCPY_TEMP_PATH}/{SCRCPY_SERVER_JAR_NAME}"
SCRCPY_PID_FILE = f"{SCRCPY_TEMP_PATH}/ws_scrcpy.pid"


class ScrcpyClient:
    """
    ws-scrcpy web-mode client.

    This class no longer implements the classic scrcpy raw socket protocol.

    Old classic mode:
        ADB localabstract:scrcpy
        Python reads dummy byte, device name, resolution, and raw H264.

    Current web mode:
        ADB tcp:8886
        Python only proxies bytes between browser WebSocket and Android server.

    Expected chain:
        Browser WebSocket
            <-> FastAPI
            <-> adbutils create_connection(Network.TCP, 8886)
            <-> ws-scrcpy server on Android
    """

    device: AdbDevice

    def __init__(
        self,
        device: AdbDevice,
        max_width: int = 0,
        bitrate: int = 8000000,
        max_fps: int = 0,
        flip: bool = False,
        block_frame: bool = False,
        stay_awake: bool = False,
        lock_screen_orientation: int = LOCK_SCREEN_ORIENTATION_UNLOCKED,
        connection_timeout: int = 3000,
        encoder_name: Optional[str] = None,
        codec_name: Optional[str] = None,
    ):
        assert max_width >= 0, "max_width must be greater than or equal to 0"
        assert bitrate >= 0, "bitrate must be greater than or equal to 0"
        assert max_fps >= 0, "max_fps must be greater than or equal to 0"
        assert -1 <= lock_screen_orientation <= 3, (
            "lock_screen_orientation must be LOCK_SCREEN_ORIENTATION_*"
        )
        assert connection_timeout >= 0, "connection_timeout must be greater than or equal to 0"

        assert encoder_name in [
            None,
            "OMX.google.h264.encoder",
            "OMX.qcom.video.encoder.avc",
            "c2.qti.avc.encoder",
            "c2.android.avc.encoder",
        ]

        assert codec_name in [None, "h264", "h265", "av1"]

        self.device = device

        # Kept for API compatibility. In web mode these are not used by this
        # Python proxy directly; the Android server and frontend protocol handle
        # stream configuration.
        self.flip = flip
        self.max_width = max_width
        self.bitrate = bitrate
        self.max_fps = max_fps
        self.block_frame = block_frame
        self.stay_awake = stay_awake
        self.lock_screen_orientation = lock_screen_orientation
        self.connection_timeout = connection_timeout
        self.encoder_name = encoder_name
        self.codec_name = codec_name

        self.listeners: dict[str, list[Callable[..., Any]]] = {
            EVENT_INIT: [],
            EVENT_DISCONNECT: [],
        }

        self.alive = False
        self.__server_pid: Optional[int] = None

        # adbutils create_connection(Network.TCP, port) returns socket.socket.
        self.__remote_socket: Optional[ClientConnection] = None

        # Kept as a compatibility alias. Do not use old ControlSender against
        # this socket unless you are certain the message format matches the
        # ws-scrcpy web protocol.
        self.control_socket: Optional[ClientConnection] = None
        self.control_socket_lock = threading.Lock()

        # Middleware
        self.on_ws_to_adb: Optional[Callable[[bytes], Optional[bytes]]] = None
        self.on_adb_to_ws: Optional[Callable[[bytes], Optional[bytes]]] = None

    # -----------------------------------------------------------------------
    # adb shell helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def __to_text(output: Any) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="replace")
        return str(output)

    def __shell(self, command: str, timeout: Optional[float] = None) -> str:
        try:
            if timeout is None:
                return self.__to_text(self.device.shell(command))
            return self.__to_text(self.device.shell(command, timeout=timeout))
        except TypeError:
            # Older adbutils may not accept timeout.
            return self.__to_text(self.device.shell(command))

    # -----------------------------------------------------------------------
    # server startup / readiness
    # -----------------------------------------------------------------------

    @staticmethod
    def __build_server_command() -> str:
        args_string = (
            f"/ {SCRCPY_SERVER_PACKAGE} "
            f"{SCRCPY_SERVER_VERSION} "
            f"{SCRCPY_SERVER_TYPE} "
            f"{SCRCPY_LOG_LEVEL} "
            f"{SCRCPY_SERVER_PORT} "
            f"{SCRCPY_LISTENS_ON_ALL_INTERFACES} "
            "2>&1 > /dev/null"
        )

        return f"CLASSPATH={SCRCPY_REMOTE_JAR} nohup app_process {args_string}"

    @staticmethod
    def get_free_tcp_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
            return port

    def __read_server_pid_file(self) -> Optional[int]:
        output = self.__shell(
            f"test -f {shlex.quote(SCRCPY_PID_FILE)} && cat {shlex.quote(SCRCPY_PID_FILE)}",
            timeout=1,
        ).strip()

        if not output:
            return None

        try:
            pid = int(output)
        except ValueError:
            return None

        return pid if pid > 0 else None

    def __get_cmdline(self, pid: int) -> list[str]:
        output = self.__shell(f"cat /proc/{pid}/cmdline", timeout=1)
        return [part for part in output.split("\x00") if part]

    def __is_expected_server_pid(self, pid: int) -> bool:
        try:
            cmdline = self.__get_cmdline(pid)
        except Exception:
            return False

        if SCRCPY_SERVER_PACKAGE not in cmdline:
            return False

        package_index = cmdline.index(SCRCPY_SERVER_PACKAGE)

        expected_args = [
            SCRCPY_SERVER_PACKAGE,
            SCRCPY_SERVER_VERSION,
            SCRCPY_SERVER_TYPE,
            SCRCPY_LOG_LEVEL,
            str(SCRCPY_SERVER_PORT),
            SCRCPY_LISTENS_ON_ALL_INTERFACES,
        ]

        actual_args = cmdline[package_index: package_index + len(expected_args)]
        return actual_args == expected_args

    def __read_valid_server_pid_file(self) -> Optional[int]:
        pid = self.__read_server_pid_file()

        if pid is None:
            return None

        if self.__is_expected_server_pid(pid):
            return pid

        # Stale pid file or PID reused by another process.
        try:
            self.__shell(f"rm -f {shlex.quote(SCRCPY_PID_FILE)}", timeout=1)
        except Exception:
            pass

        return None

    def __find_expected_server_pids(self) -> list[int]:
        script = r"""
            for p in /proc/[0-9]*; do
              pid="${p##*/}"
              first="$(tr '\0' '\n' < "$p/cmdline" 2>/dev/null | head -n 1)"
              base="${first##*/}"

              if [ "$base" = "app_process" ] || [ "$base" = "app_process64" ] || [ "$base" = "app_process32" ]; then
                echo "$pid"
              fi
            done
        """.strip()

        try:
            output = self.__shell(script, timeout=3)
        except Exception:
            return []

        pids: list[int] = []

        for line in output.splitlines():
            line = line.strip()
            if not line.isdigit():
                continue

            pid = int(line)
            if self.__is_expected_server_pid(pid):
                pids.append(pid)

        return pids

    def __wait_server_ready(self) -> int:
        attempts = max(1, self.connection_timeout // 100)

        for _ in range(attempts):
            pid = self.__read_valid_server_pid_file()

            if pid is not None:
                self.__server_pid = pid
                return pid

            pids = self.__find_expected_server_pids()
            if pids:
                self.__server_pid = pids[0]
                return pids[0]

            sleep(0.1)

        raise ConnectionError(
            f"scrcpy-server did not become ready within {self.connection_timeout} ms"
        )

    async def __deploy_server(self) -> None:
        existing_pids = self.__find_expected_server_pids()
        if existing_pids:
            self.__server_pid = existing_pids[0]
            return

        server_file_path = Path(__file__).parent / SCRCPY_SERVER_JAR_NAME

        if not server_file_path.exists():
            raise FileNotFoundError(f"scrcpy-server.jar not found: {server_file_path}")

        self.device.sync.push(server_file_path, SCRCPY_REMOTE_JAR)

        # Remove stale ready marker before starting a new server.
        self.__shell(f"rm -f {shlex.quote(SCRCPY_PID_FILE)}", timeout=1)

        background_command = self.__build_server_command()

        async def start_server() -> str:
            try:
                return await asyncio.to_thread(
                    self.__shell,
                    background_command,
                    timeout=20.0,
                )
            except AdbTimeout:
                return "pending"

        async def wait_server_ready() -> int:
            return await asyncio.to_thread(self.__wait_server_ready)

        start_task = asyncio.create_task(start_server())
        ready_task = asyncio.create_task(wait_server_ready())

        done, pending = await asyncio.wait(
            [start_task, ready_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        for task in pending:
            try:
                await task
            except asyncio.CancelledError:
                pass

    # -----------------------------------------------------------------------
    # ADB TCP connection
    # -----------------------------------------------------------------------

    async def __init_server_connection(self) -> None:
        last_error: Optional[Exception] = None
        attempts = max(1, self.connection_timeout // 100)

        for _ in range(attempts):
            try:
                items_forward = self.device.forward_list()
                remote = f"tcp:{SCRCPY_SERVER_PORT}"

                def _filter_func(x: ForwardItem):
                    return (
                        x.remote == remote
                        and x.local.startswith("tcp:")
                    )

                forwarded_list = list(filter(_filter_func, items_forward))  # type: list[ForwardItem]

                if len(forwarded_list) > 0:
                    local = forwarded_list[0].local
                    local_port = int(local.split("tcp:")[1])
                else:
                    local_port = self.get_free_tcp_port()
                    local = f"tcp:{local_port}"
                    self.device.forward(local, remote)

                self.__remote_socket = await websockets.connect(
                    f"ws://127.0.0.1:{local_port}",
                    max_size=None,
                    ping_interval=None,
                    ping_timeout=None,
                )

                self.control_socket = self.__remote_socket
                return

            except AdbError as exc:
                last_error = exc
                sleep(0.1)

        raise ConnectionError(
            f"Failed to connect ws-scrcpy server at tcp:{SCRCPY_SERVER_PORT} "
            f"within {self.connection_timeout} ms. Last error: {last_error}"
        )

    # -----------------------------------------------------------------------
    # public lifecycle
    # -----------------------------------------------------------------------

    async def init(self):
        if self.alive:
            return self

        try:
            await self.__deploy_server()
            await self.__init_server_connection()
            self.alive = True
            await self.__send_to_listeners(EVENT_INIT)
            return self

        except Exception:
            await self.stop(kill_server=False)
            raise

    async def start(self, daemon_threaded: bool = False) -> None:
        raise RuntimeError(
            "start() is deprecated in ws-scrcpy web mode. "
            "Use await client.proxy_websocket(websocket) instead."
        )

    async def stop(self, kill_server: bool = True) -> None:
        self.alive = False

        if self.__remote_socket is not None:
            try:
                await self.__remote_socket.close()
            except Exception:
                pass
            self.__remote_socket = None

        self.control_socket = None

        if kill_server:
            try:
                pid = self.__read_valid_server_pid_file()
                if pid is not None:
                    self.__shell(f"kill {pid} >/dev/null 2>&1 || true", timeout=1)

                self.__shell(f"rm -f {shlex.quote(SCRCPY_PID_FILE)}", timeout=1)
            except Exception:
                pass

        self.__server_pid = None

    # -----------------------------------------------------------------------
    # websocket proxy
    # -----------------------------------------------------------------------

    def set_proxy_callbacks(
        self,
        ws_to_adb: Optional[Callable[[bytes], Optional[bytes]]] = None,
        adb_to_ws: Optional[Callable[[bytes], Optional[bytes]]] = None,
    ) -> None:
        self.on_ws_to_adb = ws_to_adb
        self.on_adb_to_ws = adb_to_ws

    async def __websocket_to_adb(self, websocket) -> None:
        if self.__remote_socket is None:
            raise ConnectionError("Remote ADB TCP socket is not initialized")

        while self.alive:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                payload = message["bytes"]
            elif message.get("text") is not None:
                payload = message["text"].encode("utf-8")
            else:
                continue

            if self.on_ws_to_adb is not None:
                result = self.on_ws_to_adb(payload)
                if inspect.isawaitable(result):
                    result = await result
                payload = result

            if payload is None:
                continue

            await self.__remote_socket.send(payload)

    async def __adb_to_websocket(self, websocket) -> None:
        if self.__remote_socket is None:
            raise ConnectionError("Remote ADB TCP socket is not initialized")

        while self.alive:
            payload = await self.__remote_socket.recv()

            if not payload:
                break

            if self.on_adb_to_ws is not None:
                result = self.on_adb_to_ws(payload)
                if inspect.isawaitable(result):
                    result = await result
                payload = result

            if payload is None:
                continue

            await websocket.send_bytes(payload)

    async def proxy_websocket(self, websocket) -> None:
        """
        Proxy one accepted FastAPI/Starlette WebSocket to device tcp:8886.

        Important:
            The caller should call `await websocket.accept()` before this method.
        """
        if self.__remote_socket is None:
            raise RuntimeError("ScrcpyClient is not initialized. Call await init() first.")

        self.alive = True

        tasks = [
            asyncio.create_task(self.__adb_to_websocket(websocket)),
            asyncio.create_task(self.__websocket_to_adb(websocket)),
        ]

        try:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

            for task in pending:
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            for task in done:
                exc = task.exception()
                if exc is not None:
                    raise exc

        finally:
            self.alive = False
            await self.__send_to_listeners(EVENT_DISCONNECT)
            await self.stop(kill_server=True)

    # -----------------------------------------------------------------------
    # listener API
    # -----------------------------------------------------------------------

    def add_listener(self, cls: str, listener: Callable[..., Any]) -> None:
        if cls not in self.listeners:
            self.listeners[cls] = []

        self.listeners[cls].append(listener)

    def remove_listener(self, cls: str, listener: Callable[..., Any]) -> None:
        if cls in self.listeners and listener in self.listeners[cls]:
            self.listeners[cls].remove(listener)

    def has_listener(self, cls: str, listener: Callable[..., Any]) -> bool:
        return cls in self.listeners and listener in self.listeners[cls]

    def any_listener(self, cls: str) -> bool:
        return cls in self.listeners and len(self.listeners[cls]) > 0

    async def __send_to_listeners(self, cls: str, *args, **kwargs) -> None:
        tasks = []

        for func in list(self.listeners.get(cls, [])):
            try:
                result = func(*args, **kwargs)
                if inspect.isawaitable(result):
                    tasks.append(asyncio.create_task(result))  # type: ignore[arg-type]
            except Exception:
                import traceback
                traceback.print_exc()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
