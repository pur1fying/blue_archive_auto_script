import asyncio
import inspect
import socket
import struct
import threading
from pathlib import Path
from time import sleep
from typing import Any, Callable, Optional, Tuple

import numpy as np
from adbutils import AdbConnection, AdbDevice, AdbError, Network

from .codec import H264AnnexBFramer
from .const import (
    EVENT_DISCONNECT,
    EVENT_STREAM,
    EVENT_INIT,
    LOCK_SCREEN_ORIENTATION_UNLOCKED,
)
from .control import ControlSender


class ScrcpyClient:
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
        """
        Create a scrcpy client, this client won't be started until you call the start function

        Args:
            device: Android device, required.
            max_width: frame width that will be broadcast from android server
            bitrate: bitrate
            max_fps: maximum fps, 0 means not limited (supported after android 10)
            flip: flip the video
            block_frame: only return nonempty frames
            stay_awake: keep Android device awake
            lock_screen_orientation: lock screen orientation, LOCK_SCREEN_ORIENTATION_*
            connection_timeout: timeout for connection, unit is ms
            encoder_name: encoder name, enum: [OMX.google.h264.encoder, OMX.qcom.video.encoder.avc, c2.qti.avc.encoder, c2.android.avc.encoder], default is None (Auto)
            codec_name: codec name, enum: [h264, h265, av1], default is None (Auto)
        """
        # Check Params
        assert max_width >= 0, "max_width must be greater than or equal to 0"
        assert bitrate >= 0, "bitrate must be greater than or equal to 0"
        assert max_fps >= 0, "max_fps must be greater than or equal to 0"
        assert (
            -1 <= lock_screen_orientation <= 3
        ), "lock_screen_orientation must be LOCK_SCREEN_ORIENTATION_*"
        assert (
            connection_timeout >= 0
        ), "connection_timeout must be greater than or equal to 0"
        assert encoder_name in [
            None,
            "OMX.google.h264.encoder",
            "OMX.qcom.video.encoder.avc",
            "c2.qti.avc.encoder",
            "c2.android.avc.encoder",
        ]
        assert codec_name in [None, "h264", "h265", "av1"]

        # Params
        self.flip = flip
        self.device = device
        self.max_width = max_width
        self.bitrate = bitrate
        self.max_fps = max_fps
        self.block_frame = block_frame
        self.stay_awake = stay_awake
        self.lock_screen_orientation = lock_screen_orientation
        self.connection_timeout = connection_timeout
        self.encoder_name = encoder_name
        self.codec_name = codec_name

        self.framer = H264AnnexBFramer(max_fps if max_fps > 0 else 30)
        self.listeners = dict(frame=[], init=[], disconnect=[], stream=[])

        # User accessible
        self.last_frame: Optional[np.ndarray] = None
        self.resolution: Optional[Tuple[int, int]] = None
        self.device_name: Optional[str] = None
        self.control = ControlSender(self)

        # Need to destroy
        self.alive = False
        self.__server_stream: Optional[AdbConnection] = None
        self.__video_socket: Optional[socket.socket] = None
        self.control_socket: Optional[socket.socket] = None
        self.control_socket_lock = threading.Lock()

        self.stream_loop_thread = None

    def __init_server_connection(self) -> None:
        """
        Connect to android server, there will be two sockets, video and control socket.
        This method will set: video_socket, control_socket, resolution variables
        """
        for _ in range(self.connection_timeout // 100):
            try:
                self.__video_socket = self.device.create_connection(
                    Network.LOCAL_ABSTRACT, "scrcpy"
                )
                break
            except AdbError:
                sleep(0.1)
                pass
        else:
            raise ConnectionError("Failed to connect scrcpy-server after 3 seconds")

        if self.__video_socket is None:
            raise ConnectionError("Unexpected Null Video Socket!")

        dummy_byte = self.__video_socket.recv(1)
        if not len(dummy_byte) or dummy_byte != b"\x00":
            raise ConnectionError("Did not receive Dummy Byte!")

        self.control_socket = self.device.create_connection(
            Network.LOCAL_ABSTRACT, "scrcpy"
        )
        self.device_name = self.__video_socket.recv(64).decode("utf-8").rstrip("\x00")
        if self.device_name == "":
            raise ConnectionError("Did not receive Device Name!")

        res = self.__video_socket.recv(4)
        self.resolution = struct.unpack(">HH", res)
        self.__video_socket.setblocking(False)

    def __deploy_server(self) -> None:
        """
        Deploy server to android device
        """
        jar_name = "scrcpy-server.jar"
        root_path = Path(__file__).parent.parent.parent.parent
        server_file_path = root_path / "src" / "scrcpy_bin" / jar_name
        self.device.sync.push(server_file_path, f"/data/local/tmp/{jar_name}")
        commands = [
            f"CLASSPATH=/data/local/tmp/{jar_name}",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            "2.4",  # Scrcpy server version
            "log_level=info",
            f"max_size={self.max_width}",
            f"max_fps={self.max_fps}",
            f"video_bit_rate={self.bitrate}",
            f"video_encoder={self.encoder_name}"
            if self.encoder_name
            else "video_encoder=OMX.google.h264.encoder",
            f"video_codec={self.codec_name}" if self.codec_name else "video_codec=h264",
            "tunnel_forward=true",
            "send_frame_meta=false",
            "control=true",
            "audio=false",
            "show_touches=false",
            "stay_awake=false",
            "power_off_on_close=false",
            "clipboard_autosync=false",
        ]

        self.device = self.device

        fetched_response = self.device.shell(
            commands,
            stream=True,
        )

        assert isinstance(fetched_response, AdbConnection), \
            "Unexpected Type: {}".format(type(fetched_response))

        self.__server_stream: AdbConnection = fetched_response

        assert self.__server_stream is not None, \
            "Did not receive Server Stream!"

        # Wait for server to start
        self.__server_stream.read(10)

    async def start(self, daemon_threaded: bool = False) -> None:
        """
        Start listening video stream

        Args:
            daemon_threaded: Run stream loop in a daemon thread to avoid blocking
        """
        if self.stream_loop_thread: return
        self.stream_loop_thread = threading.Thread(
            target=asyncio.run, args=(self.__stream_loop(),), daemon=daemon_threaded
        )
        self.stream_loop_thread.start()

    async def init(self):
        assert self.alive is False
        self.__deploy_server()
        self.__init_server_connection()
        self.alive = True
        await self.__send_to_listeners(EVENT_INIT)
        return self

    # noinspection PyBroadException
    def stop(self) -> None:
        """
        Stop listening (both threaded and blocked)
        """
        self.alive = False
        if self.__server_stream is not None:
            try:
                self.__server_stream.close()
            except Exception:
                pass

        if self.control_socket is not None:
            try:
                self.control_socket.close()
            except Exception:
                pass

        if self.__video_socket is not None:
            try:
                self.__video_socket.close()
            except Exception:
                pass
        self.stream_loop_thread = None

    async def __stream_loop(self) -> None:
        while self.alive:
            try:
                if self.__video_socket is None:
                    raise ConnectionError("Did not receive Video Stream!")

                raw_h264 = self.__video_socket.recv(0x10000)
                if raw_h264 == b"":
                    raise ConnectionError("Video stream is disconnected")

                for to_send_content in self.framer.decode(raw_h264):
                    await self.__send_to_listeners(EVENT_STREAM, to_send_content)

            except BlockingIOError:
                await asyncio.sleep(0.01)

            except (ConnectionError, OSError):
                import traceback
                traceback.print_exc()
                print("++++++++++++++++++++++++++++++++++++++++")
                if self.alive:
                    await self.__send_to_listeners(EVENT_DISCONNECT)

            except Exception:
                import traceback
                traceback.print_exc()
                print("========================================")
                self.alive = False

    def add_listener(self, cls: str, listener: Callable[..., Any]) -> None:
        """
        Add a video listener

        Args:
             :param cls: Listener category, support: init, frame
             :param listener:A function to receive frame np.ndarray
        """
        self.listeners[cls].append(listener)

    def remove_listener(self, cls: str, listener: Callable[..., Any]) -> None:
        """
        Remove a video listener

        Args:
            cls: Listener category, support: init, frame
            listener: A function to receive frame np.ndarray
        """
        if listener in self.listeners[cls]:
            self.listeners[cls].remove(listener)

    def has_listener(self, cls: str, listener: Callable[..., Any]) -> bool:
        return listener in self.listeners[cls]

    def any_listener(self, cls: str) -> bool:
        return len(self.listeners[cls]) > 0

    async def __send_to_listeners(self, cls: str, *args, **kwargs) -> None:
        loop = asyncio.get_running_loop()
        tasks = []

        for fun in list(self.listeners.get(cls, [])):
            try:
                result = fun(*args, **kwargs)

                if inspect.isawaitable(result):
                    # 不直接 await，而是绑定到当前 loop
                    tasks.append(loop.create_task(result))

            except Exception:
                import traceback
                traceback.print_exc()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
