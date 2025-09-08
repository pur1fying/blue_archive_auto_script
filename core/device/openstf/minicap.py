import os
import socket
import threading

from adbutils import adb
from adbutils._device import AdbDevice


class IncompatibleDeviceError(Exception):
    pass


class MinicapStartupError(Exception):
    pass


class MinicapClient:
    clients = {}

    @staticmethod
    def get_instance(serial: str):
        if serial not in MinicapClient.clients:
            MinicapClient.clients[serial] = MinicapClient(serial)
        return MinicapClient.clients[serial]

    def __init__(self, serial: str):
        self.serial = serial
        self.adb_connection = adb.device(self.serial)
        self.minicap_process_thread = None
        self.minicap_port = -1
        self.minicap_socket = None

        self._start_minicap(force_reinstall=True)
        MinicapClient.clients[serial] = self

    def screenshot(self):
        frame_len_data = minicap_socket.recv(4)
        if len(frame_len_data) != 4:
            raise Exception("Failed to read frame length")
        frame_len = struct.unpack("<I", frame_len_data)[0]

        frame_data = b''
        while len(frame_data) < frame_len:
            chunk = socket_conn.recv(frame_len - len(frame_data))
            if not chunk:
                break
            frame_data += chunk

        image = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        return image

    def _start_minicap(self, force_reinstall=False):

        # -----------------------------------------
        # Install minicap
        # -----------------------------------------
        # Check if minicap is already installed
        installed = self.adb_connection.shell(
            "[ -f /data/local/tmp/minicap ] && [ -f /data/local/tmp/minicap.so ] && echo true || echo false")
        if (not force_reinstall) and installed == "true":
            return

        # Install minicap binary and shared library
        abi = self.adb_connection.shell('getprop ro.product.cpu.abi').strip()
        sdk = self.adb_connection.shell('getprop ro.build.version.sdk').strip()

        # Paths to minicap binary and shared library on host machine
        minicap_bin_path = f"{os.path.dirname(__file__)}\\stf_libs\\minicap\\{abi}\\minicap"
        minicap_so_path = f'{os.path.dirname(__file__)}\\stf_libs\\minicap-so\\android-{sdk}\\{abi}\\minicap.so'

        if not os.path.exists(minicap_bin_path) or not os.path.exists(minicap_so_path):
            raise IncompatibleDeviceError(f"Minicap binaries not found for ABI: {abi}, SDK: {sdk}")

        # Push files to device
        self.adb_connection.push(minicap_bin_path, "/data/local/tmp/minicap")
        self.adb_connection.push(minicap_so_path, "/data/local/tmp/minicap.so")

        # Set executable permissions
        self.adb_connection.shell("chmod 755 /data/local/tmp/minicap")

        # -----------------------------------------
        # Verify minicap installation and startup
        # -----------------------------------------
        width, height = MinicapClient._get_display_info(self.adb_connection)
        verify_msg = self.adb_connection.shell(
            f"LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -P {height}x{width}@1280x720/0 -t")
        if verify_msg.splitlines()[-1] == "OK":
            try:
                self.minicap_process_thread = threading.Thread(
                    target=lambda: self.adb_connection.shell(
                        f"LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -P {height}x{width}@1280x720/0",
                        stream=True
                    ),
                    daemon=True
                )
                self.minicap_process_thread.start()
                self.minicap_port = MinicapClient._find_available_port()
                self.adb_connection.forward(f"tcp:{self.minicap_port}", "localabstract:minicap")
                self.minicap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.minicap_socket.connect(("localhost", self.minicap_port))
            except Exception as e:
                raise MinicapStartupError(f"Failed to start minicap: {e}")
        else:
            raise MinicapStartupError(f"Minicap installation verify failed: {verify_msg}")

    @staticmethod
    def _find_available_port(start_port=1717, end_port=65535):
        for port in range(start_port, end_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("localhost", port))
                    return port
                except OSError:
                    continue
        raise RuntimeError("No available port found in the specified range.")

    @staticmethod
    def _get_display_info(adb_connection: AdbDevice) -> tuple[int, int]:
        result = adb_connection.shell("wm size")
        # Output example: "Physical size: 1080x1920"
        _, size_str = result.strip().split(": ")
        width, height = map(int, size_str.split("x"))
        return width, height
