import datetime
from retry import retry
import adbutils
import uiautomator2 as u2
import cv2
import numpy as np
import requests
from uiautomator2.version import (__apk_version__, __atx_agent_version__, __version__)
import os
import json

appdir = os.path.join(os.path.expanduser("~"), '.uiautomator2')

GITHUB_BASEURL = "https://github.com/openatx"


class U2Client:
    connections = dict()

    def __init__(self, serial):
        self.serial = serial
        if ":" in serial:
            self.connection = u2.connect(serial)
        else:
            self.connection = u2.connect_usb(serial)

    @staticmethod
    def get_instance(serial):
        if serial not in U2Client.connections:
            U2Client.connections[serial] = U2Client(serial)
        return U2Client.connections[serial]

    @staticmethod
    def release_instance(serial):
        if serial in U2Client.connections:
            del U2Client.connections[serial]

    def click(self, x, y):
        self.connection.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self.connection.swipe(x1, y1, x2, y2, duration)

    def screenshot(self):
        return cv2.cvtColor(np.array(self.connection.screenshot()), cv2.COLOR_RGB2BGR)

    def get_connection(self):
        return self.connection




class BAAS_U2_Initer:
    """
        Class to initialize uiautomator2 by following local files
            src/atx_app
            │
            ├── app-uiautomator.apk
            ├── app-uiautomator-test.apk
            └── atx-agent(in different archs)

        If it's your first time to use uiautomator2 (or start baas), it will initialize by downloading files from github.
        It will cause following error if you can't connect to github (mainly by cn users):

        HTTPSConnectionPool(host='github.com', port=443):
        Max retries exceeded with url:/openatx/atx-agent/releases/download/0.10.0/atx-agent_0.10.0_linux_386_tar_gz
        (Caused by NewconnectionError(': failed to establish a new connection:[winError 10061]由于目标计算机积极拒绝，无法连接。))

    """

    def __init__(self, device: adbutils.AdbDevice, logger):
        d = self._device = device
        self.sdk = d.getprop('ro.build.version.sdk')
        self.abi = d.getprop('ro.product.cpu.abi')
        self.pre = d.getprop('ro.build.version.preview_sdk')
        self.arch = d.getprop('ro.arch')
        self.abis = (d.getprop('ro.product.cpu.abilist').strip() or self.abi).split(",")

        self.__atx_listen_addr = "127.0.0.1:7912"
        self.logger = logger
        # self.logger.debug("Initial device %s", device)
        self.logger.info("uiautomator2 version: [ " + __version__ + " ].")

    @property
    def atx_agent_path(self):
        return "/data/local/tmp/atx-agent"

    def shell(self, *args, timeout=60):
        return self._device.shell(args, timeout=timeout)

    @property
    def local_atx_agent_path(self):
        """
        Returns:
            str: local atx-agent path according to device abi
        """
        files = {
            'armeabi-v7a': 'atx-agent_{v}_linux_armv7/atx-agent',
            'arm64-v8a': 'atx-agent_{v}_linux_arm64/atx-agent',
            'armeabi': 'atx-agent_{v}_linux_armv6/atx-agent',
            'x86': 'atx-agent_{v}_linux_386/atx-agent',
            'x86_64': 'atx-agent_{v}_linux_386/atx-agent',
        }
        name = None
        for abi in self.abis:
            name = files.get(abi)
            if name:
                break
        if not name:
            raise Exception(
                "arch(%s) need to be supported yet, please report an issue in github"
                % self.abis)
        return os.path.abspath("src/atx_app/%s" % name.format(v=__atx_agent_version__))

    def is_apk_outdated(self):
        """
        If apk signature mismatch, the uiautomator test will fail to start
        command: am instrument -w -r -e debug false \
                -e class com.github.uiautomator.stub.Stub \
                com.github.uiautomator.test/android.support.test.runner.AndroidJUnitRunner
        java.lang.SecurityException: Permission Denial: \
            starting instrumentation ComponentInfo{com.github.uiautomator.test/android.support.test.runner.AndroidJUnitRunner} \
            from pid=7877, uid=7877 not allowed \
            because package com.github.uiautomator.test does not have a signature matching the target com.github.uiautomator
        """
        apk_debug = self._device.package_info("com.github.uiautomator")
        apk_debug_test = self._device.package_info("com.github.uiautomator.test")
        self.logger.info("apk-debug package-info: [ " + str(apk_debug) + " ].")
        self.logger.info("apk-debug-test package-info: [ " + str(apk_debug_test) + " ].")
        if not apk_debug or not apk_debug_test:
            return True
        if apk_debug['version_name'] != __apk_version__:
            self.logger.info(
                "package com.github.uiautomator version [ " + apk_debug[
                    'version_name'] + " ] latest [ " + __apk_version__ + " ].")
            return True

        if apk_debug['signature'] != apk_debug_test['signature']:
            # On vivo-Y67 signature might not same, but signature matched.
            # So here need to check first_install_time again
            max_delta = datetime.timedelta(minutes=3)
            if abs(apk_debug['first_install_time'] -
                   apk_debug_test['first_install_time']) > max_delta:
                self.logger.info(
                    "package com.github.uiautomator does not have a signature matching the target com.github.uiautomator"
                )
                return True
        return False

    def is_atx_agent_outdated(self):
        """
        Returns:
            bool
        """
        agent_version = self._device.shell([self.atx_agent_path, "version"]).strip()
        if agent_version == "dev":
            self.logger.info("skip version check for atx-agent dev")
            return False

        # semver major.minor.patch
        try:
            real_ver = list(map(int, agent_version.split(".")))
            want_ver = list(map(int, __atx_agent_version__.split(".")))
        except ValueError:
            return True

        self.logger.info("Real version: " + str(real_ver) + ", Expect version:" + str(want_ver) + ".")

        if real_ver[:2] != want_ver[:2]:
            return True

        return real_ver[2] < want_ver[2]

    def _install_uiautomator_apks(self):
        """ use uiautomator 2.0 to run uiautomator test
        通常在连接USB数据线的情况下调用
        """
        self.shell("pm", "uninstall", "com.github.uiautomator")
        self.shell("pm", "uninstall", "com.github.uiautomator.test")
        for filename, url in app_uiautomator_apk_local_path():
            path = self.push_url(url, mode=0o644)
            self.shell("pm", "install", "-r", "-t", path)
            self.logger.info("- " + filename + " installed.")

    def push_url(self, path, dest=None, mode=0o755):
        if not dest:
            dest = self.atx_agent_path

        self.logger.info("Push to + " + dest + " . ")
        self._device.sync.push(path, dest, mode=mode)
        return dest

    def setup_atx_agent(self):
        # stop atx-agent first
        self.logger.info("Stop atx-agent.")
        self.shell(self.atx_agent_path, "server", "--stop")
        if self.is_atx_agent_outdated():
            self.logger.info("Install atx-agent [ " + __atx_agent_version__ + " ].")
            self.push_url(self.local_atx_agent_path)

        self.logger.info("Start atx-agent.")
        self.shell(self.atx_agent_path, 'server', '--nouia', '-d', "--addr", self.__atx_listen_addr)
        self.logger.info("Check atx-agent version")
        self.check_atx_agent_version()

    @retry((requests.ConnectionError, requests.ReadTimeout, requests.HTTPError), delay=.5, tries=10)
    def check_atx_agent_version(self):
        port = self._device.forward_port(7912)
        self.logger.info("Forward: local:tcp:" + str(port) + " -> remote:tcp:7912")
        version = requests.get("http://%s:%d/version" % (self._device._client.host, port)).text.strip()
        self.logger.info("atx-agent version [ " + version + " ].")

        wlan_ip = requests.get("http://%s:%d/wlan/ip" % (self._device._client.host, port)).text.strip()
        self.logger.info("device wlan ip: [ " + wlan_ip + " ].")
        return version

    def install(self):
        if self.is_apk_outdated():
            self.logger.info(
                "Install com.github.uiautomator, com.github.uiautomator.test + [ " + __apk_version__ + " ].")
            self._install_uiautomator_apks()
        else:
            self.logger.info("Already installed com.github.uiautomator apks")
        self.setup_atx_agent()

    def uninstall(self):
        self._device.shell([self.atx_agent_path, "server", "--stop"])
        self._device.shell(["rm", self.atx_agent_path])
        self.logger.info("atx-agent stopped and removed")
        self._device.shell(["pm", "uninstall", "com.github.uiautomator"])
        self._device.shell(["pm", "uninstall", "com.github.uiautomator.test"])
        self.logger.info("com.github.uiautomator uninstalled.")


def app_uiautomator_apk_local_path():
    """
    Returns:
        List[Tuple[str, str]]: [(filename, local_path)]
    """
    ret = []
    for name in ["app-uiautomator.apk", "app-uiautomator-test.apk"]:
        ret.append((name, "src/atx_app/" + name))
    return ret
