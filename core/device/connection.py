import re
import sys

from adbutils import adb
from adbutils.errors import AdbTimeout, AdbError
from core.exception import RequestHumanTakeOver

# reference : [ https://github.com/LmeSzinc/AzurLaneAutoScript/blob/master/module/device/connection.py ]
class Connection:

    def __init__(self, Baas_instance):
        self.activity = None
        self.package = None
        self.server = None
        self.Baas_thread = Baas_instance
        self.logger = Baas_instance.get_logger()
        self.config_set = Baas_instance.get_config()
        self.config = self.config_set.config
        self.static_config = self.config_set.static_config
        self.adbIP = self.config.adbIP
        self.adbPort = self.config.adbPort
        is_usb_or_emulator_device = (self.adbIP == "" or self.adbPort == "")
        if self.adbIP == "" and self.adbPort != "":
            self.serial = self.adbPort
        elif self.adbIP != "" and self.adbPort == "":
            self.serial = self.adbIP

        if not is_usb_or_emulator_device:
            if isinstance(self.adbPort, int):
                self.adbPort = str(self.adbPort)
            self.serial = self.adbIP + ":" + self.adbPort
            self.set_serial(self.serial)
        self.check_serial()
        self.detect_device()
        self.adb_connect()

        self.detect_package()
        self.check_mumu_keep_alive()

    def check_serial(self):
        old = self.serial
        new = self.revise_serial(old)
        if old != new:
            self.set_serial(new)
            self.logger.warning(f"Serial [ {old} ] is revised to [ {new} ]")
        self.logger.info(f"Serial : {self.serial}")

    @staticmethod
    def revise_serial(serial):
        serial = serial.replace(' ', '')
        # 127。0。0。1：5555
        serial = serial.replace('。', '.').replace('，', '.').replace(',', '.').replace('：', ':')
        # 127.0.0.1.5555
        serial = serial.replace('127.0.0.1.', '127.0.0.1:')
        # 16384
        try:
            port = int(serial)
            if 1000 < port < 65536:
                serial = f'127.0.0.1:{port}'
        except ValueError:
            pass
        # 夜神模拟器 127.0.0.1:62001
        # MuMu模拟器12127.0.0.1:16384
        if '模拟' in serial:
            res = re.search(r'(127\.\d+\.\d+\.\d+:\d+)', serial)
            if res:
                serial = res.group(1)
        # 12127.0.0.1:16384
        serial = serial.replace('12127.0.0.1', '127.0.0.1')
        # auto127.0.0.1:16384
        serial = serial.replace('auto127.0.0.1', '127.0.0.1').replace('autoemulator', 'emulator')
        return str(serial)

    @staticmethod
    def serial_port(serial):
        try:
            port = int(serial.split(':')[1])
        except IndexError:
            return 0
        return port

    def detect_device(self):
        self.logger.info("Detect Device")
        devices = self.list_devices()
        n_available = 0
        available = []
        unavailable = []
        self.logger.info("Available devices are listed below, choose the one you want to run BAAS on.")
        for i, device in enumerate(devices):
            if device.state == 'device':
                n_available += 1
                available.append(device.serial)
                self.logger.info(f"{i + 1} : [ {device.serial} ]")
            else:
                unavailable.append(device)

        if n_available == 0:
            self.logger.info("No available device. Please check your device connection.")
        if len(unavailable) > 0:
            self.logger.info("Detected but unavailable devices are listed below.")
            for i, device in enumerate(unavailable):
                self.logger.info(f"{i + 1} : [ {device.serial} ]")
        if self.serial == "auto" and n_available == 0:
            self.logger.warning("No available device. Please check your device connection.")

        if self.serial == "auto":
            if n_available == 0:
                self.logger.error("No available device. Please check your device connection.")
                raise RequestHumanTakeOver("No available device found.")
            elif n_available == 1:
                self.logger.info("Auto device detection found only one device, using it")
                self.set_serial(available[0])
            elif n_available == 2 and (available[0] == "127.0.0.1:16384" and available[1] == "127.0.0.1:7555") or \
                    (available[0] == "127.0.0.1:7555" and available[1] == "127.0.0.1:16384"):
                self.logger.info("Find Same MuMu12 Device, using it")
                self.set_serial("127.0.0.1:16384")
            else:
                self.logger.error("Multiple devices detected, please specify the device serial.")
                raise RequestHumanTakeOver("Multiple devices detected.")

        if self.is_mumu12_family():
            matched = False
            for device in available:
                if device == self.serial:
                    matched = True
                    break
            if not matched:
                self.logger.error("MuMu12 Device not found. It May change to near by serial. Check nearby serials.")
                if sys.platform == 'win32':
                    from core.device import emulator_manager
                    self.logger.info("Detect More Device by Emulator Manager.")
                    # use emulator manager to detect device
                    try:
                        temp = emulator_manager.autosearch()
                        for serial in temp:
                            if serial not in available:
                                available.append(serial)
                                self.logger.info(f"{len(available)} : [ {serial} ]")
                                n_available += 1
                    except:
                        pass
                port = self.serial_port(self.serial)
                for device in available:
                    temp = abs(self.serial_port(device) - port)
                    if temp == 0:
                        break
                    if temp <= 2:
                        self.logger.info(
                            "MuMu12 device serial switched from [ " + self.serial + " ] to [ " + device + " ]")
                        self.set_serial(device)
                        break

    def set_activity(self):
        pass

    def check_mumu_keep_alive(self):
        if not self.is_mumu_family():
            return
        res = self.adb_getprop("nemud.app_keep_alive")
        self.logger.info(f"MuMu Keep Alive : {res}")
        if res == "" or res == "false":
            return
        if res == "true":
            raise RequestHumanTakeOver("Please close the [ MuMu app_keep_alive ] option in the MuMu settings.")
        self.logger.warning(f"Unknown MuMu Keep Alive Value : {res}")
        return

    def is_mumu_family(self):
        return self.adbPort == "7555" or self.is_mumu12_family()

    def set_serial(self, serial):
        try:
            ip = serial.split(':')[0]
            port = serial.split(':')[1]
        except IndexError:
            ip = "127.0.0.1"
            port = "0"
        self.config_set.set('adbIP', ip)
        self.config_set.set('adbPort', port)
        self.adbIP = ip
        self.adbPort = port
        self.serial = ip + ':' + port

    def is_mumu12_family(self):
        try:
            port = int(self.adbPort)
        except ValueError:
            return False
        return 16384 <= port <= 17408

    @staticmethod
    def list_devices():
        return adb.list()

    def adb_shell_bytes(self, command, stream=False):
        d = adb.device(self.serial)
        return d.shell(command, stream=stream)

    def adb_getprop(self, name):
        return self.adb_shell_bytes(['getprop', name])

    # set self.server to ['CN', 'Global', 'JP']
    # set corresponding package
    def detect_package(self):
        self.logger.info("Detect Package")
        server = self.config.server
        package_exist = False
        if server == "auto":
            self.auto_detect_package()
            package_exist = True
        server = self.config.server
        if server == '官服' or server == 'B服':
            self.server = 'CN'
        elif server == '国际服' or server == '国际服青少年' or server == '韩国ONE':
            self.server = 'Global'
        elif server == '日服':
            self.server = 'JP'
        if not package_exist:
            self.check_package_exist(server)
        self.activity = self.static_config.activity_name[server]
        self.logger.info("Server : " + self.server)

    def auto_detect_package(self):
        self.logger.info("Detect Package")
        all_available_packages = self.available_packages()
        installed_packages = self.list_packages()
        available_packages = []
        self.logger.info("Available packages are listed below.")
        for package in all_available_packages:
            if package in installed_packages:
                available_packages.append(package)
                self.logger.info(package)
        if len(available_packages) == 0:
            self.logger.error("No available package found.")
            raise RequestHumanTakeOver("No available package.")
        if len(available_packages) == 1:
            self.logger.info(f"Only find one available package [ {available_packages[0]} ], using it.")
            self.config.server, self.package2server(available_packages[0])
            self.package = available_packages[0]
            return
        self.logger.error("Multiple available packages found.")
        raise RequestHumanTakeOver("Multiple packages")

    def available_packages(self):
        server2package = self.static_config.package_name
        all_available_packages = [server2package[server] for server in server2package]
        return all_available_packages

    def list_packages(self):
        self.logger.info("List Packages")
        for _ in range(3):
            d = adb.device(self.serial)
            result = []
            try:
                output = d.shell(["pm", "list", "packages"], timeout=5)
                for m in re.finditer(r'^package:([^\s]+)\r?$', output, re.M):
                    result.append(m.group(1))
                return list(sorted(result))
            except AdbTimeout as e:
                self.logger.error(f"Error: {e}")
                self.kill_adb()
                self.logger.info("Retry list packages")
        return []

    def kill_adb(self):
        self.logger.info("Kill ADB Server")
        adb.server_kill()

    def package2server(self, package):
        server2package = self.static_config.package_name
        for server in server2package:
            if server2package[server] == package:
                return server
        return None

    def check_package_exist(self, server):
        target_package = self.static_config.package_name[server]
        self.logger.info("Check Package [ " + target_package + " ] Exist.")
        installed_packages = self.list_packages()
        if target_package not in installed_packages:
            self.logger.error(f"Package [ {target_package} ] not found.")
            raise RequestHumanTakeOver("Package not found.")
        self.logger.info(f"Package Found.")
        self.package = target_package

    def get_package_name(self):
        return self.package

    def get_server(self):
        return self.server

    def get_activity_name(self):
        return self.activity

    def get_current_package(self):
        self.logger.info("Get Current Package.")
        for _ in range(3):
            d = adb.device(self.serial)
            try:
                return d.app_current().package
            except AdbError as e:
                self.logger.error(f"Error: {e}")
                self.kill_adb()
                self.logger.info("Retry Get Current Package.")
        return ""

    def adb_connect(self):
        for device in self.list_devices():
            if device.state == 'offline':
                self.logger.warning(f'Device {device.serial} is offline, disconnect it before connecting')
                msg = adb.disconnect(device.serial)
                if msg:
                    self.logger.info(msg)
            elif device.state == 'unauthorized':
                self.logger.error(f'Device {device.serial} is unauthorized, please accept ADB debugging on your device')
            elif device.state == 'device':
                pass
            else:
                self.logger.warning(f'Device {device.serial} is is having a unknown status: {device.state}')

        # Skip for emulator-5554
        if 'emulator-' in self.serial:
            self.logger.info(f'"{self.serial}" is a `emulator-*` serial, skip adb connect')
            return True
        if re.match(r'^[a-zA-Z0-9]+$', self.serial):
            self.logger.info(f'"{self.serial}" seems to be a Android serial, skip adb connect')
            return True

        # Try to connect
        for _ in range(3):
            msg = adb.connect(self.serial)
            self.logger.info(msg)
            # Connected to 127.0.0.1:59865
            # Already connected to 127.0.0.1:59865
            if 'connected' in msg:
                return True
            # bad port number '598265' in '127.0.0.1:598265'
            elif 'bad port' in msg:
                self.logger.error('Serial incorrect, might be a typo')
                raise RequestHumanTakeOver

        # Failed to connect
        self.logger.warning(f'Failed to connect {self.serial} after 3 trial, assume connected')
        self.detect_device()
        return False

    def get_serial(self):
        return self.serial

    def close_current_app(self, pkg_name=None):
        self.logger.info("Close Current App")
        d = adb.device(self.serial)
        if pkg_name is None:
            pkg_name = self.get_current_package()
        d.app_stop(pkg_name)
