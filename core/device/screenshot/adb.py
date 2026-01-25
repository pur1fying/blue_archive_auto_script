from adbutils import adb
import cv2
import numpy as np
import socket
import threading

from core.utils import is_android


class AdbScreenshot:
    def __init__(self, conn):
        self.serial = conn.serial
        self.logger = conn.logger

        self.adb = adb.device(self.serial)
        self.display_id = None

        # Create a localhost listener on a random free port
        if is_android():
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind(('127.0.0.1', 0))
            self._server.listen(1)
            self._host, self._port = self._server.getsockname()

    def __del__(self):
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass

    def set_display_id(self, display_id):
        self.display_id = display_id

    def _accept_and_read(self, out_container):
        # Blocking accept and read all bytes until EOF
        conn, addr = self._server.accept()
        try:
            chunks = []
            while True:
                data = conn.recv(8192)
                if not data:
                    break
                chunks.append(data)
            out_container.append(b''.join(chunks))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def screenshot(self):
        if is_android() and self.display_id:
            # Binder IPC on Android cannot pass data larger than 500 KB,
            # so we have to pipe the screenshot data through a socket.
            # Thus we have to use sh to pipe the output of screencap to nc.
            cmd = f'screencap -p -d {self.display_id} | nc 127.0.0.1 {self._port}'
            out = []
            th = threading.Thread(target=self._accept_and_read, args=(out,), daemon=True)
            th.start()
            self.adb.shell(cmd, stream=False, encoding=None, timeout=10)
            # Wait for accept thread to finish reading
            th.join(10)
            if th.is_alive():
                raise TimeoutError('Timed out waiting for screenshot data')
            data = out[0] if out else b''
        else:
            cmd = ['screencap', '-p']
            data = self.adb.shell(cmd, stream=False, encoding=None)

        if len(data) < 500:
            self.logger.warning(f'Unexpected screenshot: {data}')
        image = np.frombuffer(data, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

