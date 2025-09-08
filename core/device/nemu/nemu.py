import asyncio
import ctypes
import os
import sys
import time
from functools import partial

import cv2
import numpy as np


class NemuIpcIncompatible(Exception):
    pass


class NemuIpcError(Exception):
    pass


class NemuInvalidSerialError(Exception):
    pass


# reference : [ https://github.com/LmeSzinc/AzurLaneAutoScript/blob/master/module/device/method/nemu_ipc.py ]

class CaptureStd:
    """
    Capture stdout and stderr from both python and C library
    https://stackoverflow.com/questions/5081657/how-do-i-prevent-a-c-shared-library-to-print-on-stdout-in-python/17954769

    ```
    with CaptureStd() as capture:
        # String wasn't printed
        print('whatever')
    # But captured in ``capture.stdout``
    print(f'Got stdout: "{capture.stdout}"')
    print(f'Got stderr: "{capture.stderr}"')
    ```
    """

    def __init__(self):
        self.stdout = b''
        self.stderr = b''

    def _redirect_stdout(self, to):
        sys.stdout.close()
        os.dup2(to, self.fdout)
        sys.stdout = os.fdopen(self.fdout, 'w')

    def _redirect_stderr(self, to):
        sys.stderr.close()
        os.dup2(to, self.fderr)
        sys.stderr = os.fdopen(self.fderr, 'w')

    def __enter__(self):
        self.fdout = sys.stdout.fileno()
        self.fderr = sys.stderr.fileno()
        self.reader_out, self.writer_out = os.pipe()
        self.reader_err, self.writer_err = os.pipe()
        self.old_stdout = os.dup(self.fdout)
        self.old_stderr = os.dup(self.fderr)

        file_out = os.fdopen(self.writer_out, 'w')
        file_err = os.fdopen(self.writer_err, 'w')
        self._redirect_stdout(to=file_out.fileno())
        self._redirect_stderr(to=file_err.fileno())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._redirect_stdout(to=self.old_stdout)
        self._redirect_stderr(to=self.old_stderr)
        os.close(self.old_stdout)
        os.close(self.old_stderr)

        self.stdout = self.recvall(self.reader_out)
        self.stderr = self.recvall(self.reader_err)
        os.close(self.reader_out)
        os.close(self.reader_err)

    @staticmethod
    def recvall(reader, length=1024) -> bytes:
        fragments = []
        while 1:
            chunk = os.read(reader, length)
            if chunk:
                fragments.append(chunk)
            else:
                break
        output = b''.join(fragments)
        return output


class CaptureNemuIpc(CaptureStd):
    instance = None

    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def is_capturing(self):
        """
        Only capture at the topmost wrapper to avoid nested capturing
        If a capture is ongoing, this instance does nothing
        """
        cls = self.__class__
        return isinstance(cls.instance, cls) and cls.instance != self

    def __enter__(self):
        if self.is_capturing():
            return self
        super().__enter__()
        CaptureNemuIpc.instance = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_capturing():
            return

        CaptureNemuIpc.instance = None
        super().__exit__(exc_type, exc_val, exc_tb)

        self.check_stdout()
        self.check_stderr()

    def check_stdout(self):
        if not self.stdout:
            return
        self.logger.info(f'NemuIpc stdout: {self.stdout}')

    def check_stderr(self):
        if not self.stderr:
            return
        self.logger.error(f'NemuIpc stderr: {self.stderr}')

        # Calling an old MuMu12 player
        # Tested on 3.4.0
        # b'nemu_capture_display rpc error: 1783\r\n'
        # Tested on 3.7.3
        # b'nemu_capture_display rpc error: 1745\r\n'
        if b'error: 1783' in self.stderr or b'error: 1745' in self.stderr:
            raise NemuIpcIncompatible(
                f'NemuIpc requires MuMu12 version >= 3.8.13, please check your version')
        # contact_id incorrect
        # b'nemu_capture_display cannot find rpc connection\r\n'
        if b'cannot find rpc connection' in self.stderr:
            raise NemuIpcError(self.stderr)
        # Emulator died
        # b'nemu_capture_display rpc error: 1722\r\n'
        # MuMuVMMSVC.exe died
        # b'nemu_capture_display rpc error: 1726\r\n'
        # No idea how to handle yet
        if b'error: 1722' in self.stderr or b'error: 1726' in self.stderr:
            raise NemuIpcError('Emulator instance is probably dead')


class NemuClient:
    clients = dict()

    @staticmethod
    def get_instance(conn):
        if conn.serial not in NemuClient.clients:
            return NemuClient.new_instance(conn)
        return NemuClient.clients[conn.serial]

    @staticmethod
    def new_instance(conn):
        try:
            nemu_client = NemuClient(conn)
            return nemu_client
        except (NemuIpcIncompatible, NemuIpcError) as e:
            conn.logger.warning(e.__str__())
            conn.logger.info("Emulator info incorrect. Try to auto detect mumu player path.")
            try:
                nemu_client = NemuClient(conn, auto_detect=True)
                return nemu_client
            except (NemuIpcIncompatible, NemuIpcError) as e:
                conn.logger.error(e.__str__())
                raise Exception("Unable to init with auto detected path.")
        except NemuInvalidSerialError:
            conn.logger.error('Can\'t convert serial to instance id.')
            raise NemuInvalidSerialError("Invalid serial. Unable to use Init.")
        else:
            conn.logger.error("MuMu Player 12 not found.")
            raise Exception("Unable to use Init.")

    def __init__(self, conn, display_id=0, auto_detect=False):
        self.lib = None
        self._ev = asyncio.new_event_loop()
        if auto_detect:
            path = NemuClient.get_possible_mumu12_folder()
            self.logger.info(f"Auto detect mumu player path: {str(path)}")
            if path is not None:
                self.config_set.set("program_address", path)
                self.nemu_folder = os.path.dirname(path)
        else:
            self.nemu_folder = conn.config.program_address
        self.nemu_folder = os.path.dirname(os.path.dirname(self.nemu_folder))  # C:/Program Files/Netease/MuMu Player 12
        self.instance_id = NemuClient.serial_to_id(conn.serial)
        if self.instance_id is None:
            raise NemuInvalidSerialError("Invalid serial. Unable to use Init.")
        self.logger = conn.logger
        self.display_id = display_id
        # try to load dll from various pathAdd commentMore actions
        list_dll = [
            # MuMuPlayer12
            os.path.abspath(os.path.join(self.nemu_folder, './shell/sdk/external_renderer_ipc.dll')),
            # MuMuPlayer12 5.0
            os.path.abspath(os.path.join(self.nemu_folder, './nx_device/12.0/shell/sdk/external_renderer_ipc.dll')),
        ]
        ipc_dll = ''
        for ipc_dll in list_dll:
            if not os.path.exists(ipc_dll):
                continue
            try:
                self.lib = ctypes.CDLL(ipc_dll)
                break
            except OSError as e:
                self.logger.error(e.__str__())
                self.logger.error(f'ipc_dll={ipc_dll} exists, but cannot be loaded')
                continue
        if not self.lib:
            self.logger.error("NemuIpc requires MuMu12 version >= 3.8.13, please check your version.")
            self.logger.error(f'None of the following path exists')
            for path in list_dll:
                self.logger.error(f'{path}')
            raise NemuIpcIncompatible("Please check your MuMu Player 12 version and install path in BAAS settings.")

        self.logger.info('NemuIpcImpl init')
        self.logger.info(f'nemu_folder = {self.nemu_folder}')
        self.logger.info(f'ipc_dll     = {ipc_dll}')
        self.logger.info(f'instance_id = {self.instance_id}')
        self.logger.info(f'display_id  = {self.display_id}')

        self.connect_id: int = 0
        self.width = 0
        self.height = 0
        NemuClient.clients[conn.serial] = self

    def connect(self):
        if self.connect_id > 0:
            return

        connect_id = self.ev_run_sync(
            self.lib.nemu_connect,
            self.nemu_folder, self.instance_id
        )
        if connect_id == 0:
            raise NemuIpcError(
                'Connection failed, please check if nemu_folder is correct and emulator is running'
            )

        self.connect_id = connect_id

        NemuClient.clients[self.connect_id] = self
        # logger.info(f'NemuIpc connected: {self.connect_id}')

    def disconnect(self):
        if self.connect_id == 0:
            return

        self.ev_run_sync(
            self.lib.nemu_disconnect,
            self.connect_id
        )

        # logger.info(f'NemuIpc disconnected: {self.connect_id}')
        self.connect_id = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    async def ev_run_async(self, func, *args, timeout=0.15, **kwargs):
        """
        Args:
            func: Sync function to call
            *args:
            timeout:
            **kwargs:

        Raises:
            asyncio.TimeoutError: If function call timeout
        """
        func_wrapped = partial(func, *args, **kwargs)
        # Increased timeout for slow PCs
        # Default screenshot interval is 0.2s, so a 0.15s timeout would have a fast retry without extra time costs
        result = await asyncio.wait_for(self._ev.run_in_executor(None, func_wrapped), timeout=timeout)
        return result

    def ev_run_sync(self, func, *args, **kwargs):
        """
        Args:
            func: Sync function to call
            *args:
            **kwargs:

        Raises:
            asyncio.TimeoutError: If function call timeout
            NemuIpcIncompatible:
            NemuIpcError
        """
        result = self._ev.run_until_complete(self.ev_run_async(func, *args, **kwargs))

        err = False
        if func.__name__ == 'nemu_connect':
            if result == 0:
                err = True
        else:
            if result > 0:
                err = True
        # Get to actual error message printed in std
        if err:
            self.logger.warning(f'Failed to call {func.__name__}, result={result}')
            with CaptureNemuIpc(self.logger):
                result = self._ev.run_until_complete(self.ev_run_async(func, *args, **kwargs))

        return result

    def get_resolution(self):
        """
        Get emulator resolution, `self.width` and `self.height` will be set
        """
        if self.connect_id == 0:
            self.connect()

        width_ptr = ctypes.pointer(ctypes.c_int(0))
        height_ptr = ctypes.pointer(ctypes.c_int(0))
        nullptr = ctypes.POINTER(ctypes.c_int)()

        ret = self.ev_run_sync(
            self.lib.nemu_capture_display,
            self.connect_id, self.display_id, 0, width_ptr, height_ptr, nullptr,
            timeout=10.0
        )
        if ret > 0:
            raise NemuIpcError('nemu_capture_display failed during get_resolution()')
        self.width = width_ptr.contents.value
        self.height = height_ptr.contents.value

    def down(self, x, y):
        """
        Contact down, continuous contact down will be considered as swipe
        """
        if self.connect_id == 0:
            self.connect()
        if self.height == 0:
            self.get_resolution()

        ret = self.ev_run_sync(
            self.lib.nemu_input_event_touch_down,
            self.connect_id, self.display_id, x, y,
            timeout=10.0
        )
        if ret > 0:
            raise NemuIpcError('nemu_input_event_touch_down failed')

    def up(self):
        """
        Contact up
        """
        if self.connect_id == 0:
            self.connect()

        ret = self.ev_run_sync(
            self.lib.nemu_input_event_touch_up,
            self.connect_id, self.display_id,
            timeout=10.0
        )
        if ret > 0:
            raise NemuIpcError('nemu_input_event_touch_up failed')

    @staticmethod
    def serial_to_id(serial: str):
        """
        Predict instance ID from serial
        E.g.
            "127.0.0.1:16384" -> 0
            "127.0.0.1:16416" -> 1
            Port from 16414 to 16418 -> 1

        Returns:
             int: instance_id, or None if failed to predict
        """
        try:
            port = int(serial.split(':')[1])
        except (IndexError, ValueError):
            return None
        if port >= 16384 and port < 16384 + 32 * 32:
            index, offset = divmod(port - 16384 + 16, 32)
            offset -= 16
            if 0 <= index < 32 and offset in [-2, -1, 0, 1, 2]:
                return index
        if port >= 5555 and port < 5555 + 32:
            index, offset = divmod(port - 5555, 2)
            if 0 <= index < 32 and offset in [0, 1]:
                return index

    @staticmethod
    def get_possible_mumu12_folder():
        from core.device.emulator_manager import mumu12_api_backend
        try:
            path = mumu12_api_backend("mumu", 0, operation="get_path")
            return path
        except Exception as e:
            return None

    # --------------------------------------------
    # Screenshot functions
    # --------------------------------------------
    def screenshot(self):
        """
        Returns:
            np.ndarray: Image array in RGBA color space
                Note that image is upside down
        """
        if self.connect_id == 0:
            self.connect()

        self.get_resolution()

        width_ptr = ctypes.pointer(ctypes.c_int(self.width))
        height_ptr = ctypes.pointer(ctypes.c_int(self.height))
        length = self.width * self.height * 4
        pixels_pointer = ctypes.pointer((ctypes.c_ubyte * length)())

        for i in range(3):
            try:
                ret = self.ev_run_sync(
                    self.lib.nemu_capture_display,
                    self.connect_id, self.display_id, length, width_ptr, height_ptr, pixels_pointer,
                    timeout=10.0
                )
                if ret > 0:
                    raise NemuIpcError('nemu_capture_display failed during screenshot()')
                break
            except TimeoutError:
                self.logger.warning('nemu_capture_display timeout, retrying...')
                if i == 2:
                    raise TimeoutError("nemu_capture_display timeout 3 times.")

        # image = np.ctypeslib.as_array(pixels_pointer, shape=(self.height, self.width, 4))
        image = np.ctypeslib.as_array(pixels_pointer.contents).reshape((self.height, self.width, 4))
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        cv2.flip(image, 0, dst=image)
        return image

    # --------------------------------------------
    # Control functions
    # --------------------------------------------
    def click(self, x, y):
        self.down(x, y)
        time.sleep(0.015)
        self.up()
        time.sleep(0.035)

    def swipe(self, x1, y1, x2, y2, duration):
        points = insert_swipe(p0=(x1, y1), p3=(x2, y2))

        for point in points:
            self.down(*point)
            time.sleep(0.010)

        self.up()
        time.sleep(0.050)

    def long_click(self, x, y, duration):
        self.down(x, y)
        time.sleep(duration)
        self.up()
        time.sleep(0.050)


def random_normal_distribution(a, b, n=5):
    output = np.mean(np.random.uniform(a, b, size=n))
    return output


def insert_swipe(p0, p3, speed=15, min_distance=10):
    """
    Insert way point from start to end.
    First generate a cubic bézier curve

    Args:
        p0: Start point.
        p3: End point.
        speed: Average move speed, pixels per 10ms.
        min_distance:

    Returns:
        list[list[int]]: List of points.

    Examples:
        > insert_swipe((400, 400), (600, 600), speed=20)
        [[400, 400], [406, 406], [416, 415], [429, 428], [444, 442], [462, 459], [481, 478], [504, 500], [527, 522],
        [545, 540], [560, 557], [573, 570], [584, 582], [592, 590], [597, 596], [600, 600]]
    """
    p0 = np.array(p0)
    p3 = np.array(p3)

    # Random control points in Bézier curve
    distance = np.linalg.norm(p3 - p0)
    p1 = 2 / 3 * p0 + 1 / 3 * p3 + random_theta() * random_rho(distance * 0.1)
    p2 = 1 / 3 * p0 + 2 / 3 * p3 + random_theta() * random_rho(distance * 0.1)

    # Random `t` on Bézier curve, sparse in the middle, dense at start and end
    segments = max(int(distance / speed) + 1, 5)
    lower = random_normal_distribution(-85, -60)
    upper = random_normal_distribution(80, 90)
    theta = np.arange(lower + 0., upper + 0.0001, (upper - lower) / segments)
    ts = np.sin(theta / 180 * np.pi)
    ts = np.sign(ts) * abs(ts) ** 0.9
    ts = (ts - min(ts)) / (max(ts) - min(ts))

    # Generate cubic Bézier curve
    points = []
    prev = (-100, -100)
    for t in ts:
        point = p0 * (1 - t) ** 3 + 3 * p1 * t * (1 - t) ** 2 + 3 * p2 * t ** 2 * (1 - t) + p3 * t ** 3
        point = point.astype(int).tolist()
        if np.linalg.norm(np.subtract(point, prev)) < min_distance:
            continue

        points.append(point)
        prev = point

    # Delete nearing points
    if len(points[1:]):
        distance = np.linalg.norm(np.subtract(points[1:], points[0]), axis=1)
        mask = np.append(True, distance > min_distance)
        points = np.array(points)[mask].tolist()
        if len(points) <= 1:
            points = [p0, p3]
    else:
        points = [p0, p3]
    return points


def random_rho(dis):
    return random_normal_distribution(-dis, dis)


def random_theta():
    theta = np.random.uniform(0, 2 * np.pi)
    return np.array([np.sin(theta), np.cos(theta)])
