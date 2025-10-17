import os
import io
import posixpath
import asyncio
import threading
import struct
from typing import TYPE_CHECKING, Iterable, BinaryIO, TypeVar
from typing_extensions import override
import logging

from pyadbserver.server import OK, AdbServer, App, route
from pyadbserver.transport.device import Device
from pyadbserver.services.host import HostService
from pyadbserver.services.sync import SyncV1Service
from pyadbserver.services.forward import ForwardService
from pyadbserver.services.shell import LocalShellService, g_session, encode_shell_packet, ShellProtocolId, NOOP, ResponseAction, FAIL
from pyadbserver.services.fs import AbstractFileSystem, Dirent, FileStat
from pyadbserver.transport.device_manager import SingleDeviceService

if TYPE_CHECKING:
    from core import Baas_thread
    from .shizuku import ShizukuClient

ADB_PORT = 5037

class ShizukuFileSystem(AbstractFileSystem):
    def __init__(self, shizuku: 'ShizukuClient', logger: 'Baas_thread.Logger'):
        self.shizuku = shizuku
        self.logger = logger
    
    @override
    def stat(self, path: str) -> 'FileStat':
        stat_result = self.shizuku.fs_stat(path)
        if stat_result is None or not stat_result.exists:
            raise FileNotFoundError(f"No such file or directory: {path}")

        return FileStat(
            size=stat_result.size,
            mtime=stat_result.mtime,
            mode=stat_result.mode,
        )

    @override
    def iterdir(self, path: str) -> Iterable[Dirent]:
        dir_stat = self.shizuku.fs_stat(path)
        if dir_stat is None or not dir_stat.exists:
            raise FileNotFoundError(f"No such file or directory: {path}")
        if not dir_stat.isDir:
            raise NotADirectoryError(f"Not a directory: {path}")

        files = self.shizuku.fs_list(path)
        # This is inefficient as it calls fs_stat for each file.
        # A batch API in Shizuku would be better.
        for file_name in files:
            full_path = posixpath.join(path, file_name)
            stat = self.shizuku.fs_stat(full_path)
            if stat and stat.exists:
                yield Dirent(
                    name=file_name,
                    mode=stat.mode,
                    size=stat.size,
                    mtime=stat.mtime
                )
    
    @override
    def open_for_read(self, path: str) -> BinaryIO:
        content = self.shizuku.fs_read(path)
        if content is None:
            stat = self.shizuku.fs_stat(path)
            if stat is None or not stat.exists:
                raise FileNotFoundError(f"No such file or directory: {path}")
            if stat.isDir:
                raise IsADirectoryError(f"Is a directory: {path}")
            raise IOError(f"Could not read file: {path}")

        if isinstance(content, str):
            content = content.encode('utf-8')
        
        return io.BytesIO(content)

    @override
    def open_for_write(self, path: str, mode: int) -> BinaryIO:
        stat = self.shizuku.fs_stat(path)
        if stat and stat.exists and stat.isDir:
            raise IsADirectoryError(f"Is a directory: {path}")

        # NOTE: shizuku fs_write does not support setting file mode.
        buffer = io.BytesIO()
        
        def close_with_writeback():
            try:
                data = buffer.getvalue()
                if not self.shizuku.fs_write(path, data, append=False):
                    raise IOError(f"Could not write to file: {path}")
            finally:
                buffer.close = lambda: None # prevent recursion
                buffer.close()
            
        buffer.close = close_with_writeback
        return buffer

    @override
    def makedirs(self, path: str) -> None:
        if not self.shizuku.fs_mkdirs(path):
            raise IOError(f"Could not create directories: {path}")

    @override
    def set_mtime(self, path: str, mtime: int) -> None:
        # This is a no-op as Shizuku does not provide a way to set mtime.
        # Adb push uses this but it's okay to not implement it.
        self.logger.warning(f"ShizukuFileSystem: set_mtime is not implemented for {path}")
        pass

class ShizukuShellService(LocalShellService):
    def __init__(self, shizuku: 'ShizukuClient', logger: 'Baas_thread.Logger'):
        self.shizuku = shizuku
        self.logger = logger

    @override
    async def _run_shell_command(
        self,
        cmd: str,
        use_protocol: bool,
        use_pty: bool
    ):
        session = g_session.get()
        await session.send_okay(flush=True)

        if use_pty:
            session.write(b"PTY mode is not supported by ShizukuShellService\n")
            await session._flush()
            return NOOP(action=ResponseAction.CLOSE)

        loop = asyncio.get_running_loop()
        success, result = await loop.run_in_executor(None, self.shizuku.execute_command, cmd)
        if not success:
            error_msg = str(result)
            if use_protocol:
                packet = encode_shell_packet(ShellProtocolId.STDERR, error_msg.encode('utf-8'))
                session.write(packet)
            else:
                session.write(error_msg.encode('utf-8'))
            
            # send exit code 1
            if use_protocol:
                exit_data = struct.pack("B", 1)
                exit_packet = encode_shell_packet(ShellProtocolId.EXIT, exit_data)
                session.write(exit_packet)
        else:
            # result is a CommandResult
            stdout = result.stdout or ''
            stderr = result.stderr or ''
            full_output = stdout + stderr

            if full_output:
                data = full_output.encode('utf-8')
                if use_protocol:
                    packet = encode_shell_packet(ShellProtocolId.STDOUT, data)
                    session.write(packet)
                else:
                    session.write(data)
            
            exit_code = 0
            if use_protocol:
                exit_data = struct.pack("B", exit_code & 0xFF)
                exit_packet = encode_shell_packet(ShellProtocolId.EXIT, exit_data)
                session.write(exit_packet)

        await session._flush()
        return NOOP(action=ResponseAction.CLOSE)

async def server_main(shizuku: 'ShizukuClient', logger: 'Baas_thread.Logger'):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.getLogger("pyadbserver").setLevel(logging.DEBUG)
    ds = SingleDeviceService(device=Device(
        id="baas",
        serial="baas",
        state="device",
        properties={}
    ))
    app = App(device_manager=ds)
    server = AdbServer(
        port=ADB_PORT,
        app=app,
    )
    app.register(HostService(server, ds))
    app.register(SyncV1Service(ShizukuFileSystem(shizuku, logger)))
    app.register(ShizukuShellService(shizuku, logger))
    app.register(ForwardService())
    await server.start()
    await server.serve_forever()

def patch_adb(shizuku: 'ShizukuClient', logger: 'Baas_thread.Logger'):
    """
    Apply patch to adbutils.
    """
    # Patch adbutils
    from adbutils._device import BaseDevice
    BaseDevice.forward_port = lambda self, remote: int(remote) # prevent random port allocation

    # Start mock server
    os.environ["ANDROID_ADB_SERVER_PORT"] = str(ADB_PORT)
    thread = threading.Thread(
        target=lambda: asyncio.run(server_main(shizuku, logger)),
        name="adb-server-thread",
        daemon=True,
    )
    thread.start()