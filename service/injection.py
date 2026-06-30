from __future__ import annotations

import os
import queue
import sys
import traceback
import types
from datetime import datetime
from functools import wraps
from inspect import signature
from typing import Any


_APPLIED = False


def _supports_parameter(callable_obj: Any, name: str) -> bool:
    try:
        return name in signature(callable_obj).parameters
    except (TypeError, ValueError):
        return False


def _ensure_logger_extensions(logger: Any, jsonify: bool = False) -> None:
    if not hasattr(logger, "log_collector"):
        logger.log_collector = queue.Queue()
    if not hasattr(logger, "jsonify"):
        logger.jsonify = False
    if jsonify:
        logger.jsonify = True


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _install_gui_stubs() -> None:
    if "gui.util.translator" not in sys.modules:
        translator = types.ModuleType("gui.util.translator")

        class _Translator:
            @staticmethod
            def tr(_domain, value):
                return value

            @staticmethod
            def undo(value):
                return value

        translator.baasTranslator = _Translator()
        sys.modules["gui.util.translator"] = translator

    if "gui.util.customized_ui" not in sys.modules:
        customized_ui = types.ModuleType("gui.util.customized_ui")

        class BoundComponent:
            def __init__(self, component, string_rule, config_set, attribute="setText"):
                self.component = component
                self.string_rule = string_rule
                self.config_set = config_set
                self.attribute = attribute

            def config_updated(self, _key):
                return None

        customized_ui.BoundComponent = BoundComponent
        sys.modules["gui.util.customized_ui"] = customized_ui


def _install_android_ocr_modules() -> None:
    if not _env_enabled("BAAS_ANDROID"):
        return
    from service import android_ocr_client, android_ocr_installer

    sys.modules["core.ocr.baas_ocr_client.Client"] = android_ocr_client
    sys.modules["core.ocr.baas_ocr_client.server_installer"] = android_ocr_installer


def prepare_service_imports() -> None:
    _install_gui_stubs()
    _install_android_ocr_modules()


def _patch_logger() -> None:
    _install_gui_stubs()
    _install_android_ocr_modules()
    from core import utils

    logger_cls = utils.Logger
    if getattr(logger_cls, "_baas_service_injected", False):
        return

    original_init = logger_cls.__init__
    original_log = getattr(logger_cls, "log", None)

    @wraps(original_init)
    def init(self, logger_signal, jsonify=False):
        if _supports_parameter(original_init, "jsonify"):
            original_init(self, logger_signal, jsonify=jsonify)
        else:
            original_init(self, logger_signal)
        _ensure_logger_extensions(self, jsonify=jsonify)

    logger_cls.__init__ = init
    if original_log is not None:
        @wraps(original_log)
        def log(self, level, message):
            _ensure_logger_extensions(self)
            if getattr(self, "jsonify", False):
                self.log_collector.put({
                    "time": datetime.now(),
                    "level": level,
                    "message": message,
                })
                return
            return original_log(self, level, message)

        logger_cls.log = log
    logger_cls._baas_service_injected = True


def _patch_main() -> None:
    _install_gui_stubs()
    _install_android_ocr_modules()
    import main as main_module
    from core.ocr import ocr
    from core.ocr.baas_ocr_client.server_installer import check_git
    from core.utils import Logger
    from core.config.config_set import ConfigSet

    main_cls = main_module.Main
    if getattr(main_cls, "_baas_service_injected", False):
        return

    def init(self, logger_signal=None, ocr_needed=None, **kwargs):
        self.ocr_needed = ocr_needed
        self.ocr = None
        self.logger = Logger(logger_signal, jsonify=kwargs.get("jsonify", False))
        self.project_dir = os.path.abspath(os.path.dirname(main_module.__file__))
        self.logger.info(self.project_dir)
        if not kwargs.get("lazy_data", False):
            self.init_all_data()
        self.threads = {}

    def init_all_data(self, need_ocr_update_check=True):
        if not self.init_ocr(need_ocr_update_check=need_ocr_update_check):
            if os.getenv("BAAS_ALLOW_MISSING_OCR", "").strip().lower() in {"1", "true", "yes", "on"}:
                self.logger.warning("Ocr Init Incomplete. Continuing because missing OCR is allowed.")
            else:
                self.logger.error("Ocr Init Incomplete Please restart .")
                return False
        self.init_static_config()
        self.logger.info("-- All Data Initialization Complete Script ready--")
        return True

    def init_ocr(self, need_ocr_update_check=True):
        if need_ocr_update_check:
            try:
                check_git(self.logger)
            except Exception:
                self.logger.error("OCR Update Failed.")
                self.logger.error(traceback.format_exc())
                self.logger.info("Try to Start OCR Server Without Update.")
        try:
            self.ocr = ocr.Baas_ocr(logger=self.logger, ocr_needed=self.ocr_needed)
            return True
        except Exception:
            self.logger.error("OCR initialization failed")
            self.logger.error(traceback.format_exc())
            return False

    def init_static_config(self):
        try:
            if ConfigSet.static_config is None:
                ConfigSet._init_static_config()
            return True
        except Exception:
            self.logger.error("Static Config initialization failed")
            self.logger.error(traceback.format_exc())
            return False

    main_cls.__init__ = init
    main_cls.init_all_data = init_all_data
    main_cls.init_ocr = init_ocr
    if not hasattr(main_cls, "init_static_config"):
        main_cls.init_static_config = init_static_config
    main_cls._baas_service_injected = True


def _patch_baas_thread() -> None:
    _install_gui_stubs()
    _install_android_ocr_modules()
    from core.Baas_thread import Baas_thread

    if getattr(Baas_thread, "_baas_service_injected", False):
        return

    original_init = Baas_thread.__init__
    original_set_ocr = Baas_thread.set_ocr
    original_start_emulator = Baas_thread.start_emulator
    original_android_language = Baas_thread._get_android_device_ocr_language
    original_check_atx = Baas_thread.check_atx
    original_wait_uiautomator_start = Baas_thread.wait_uiautomator_start
    original_check_resolution = Baas_thread.check_resolution
    original_swipe = Baas_thread.swipe

    @wraps(original_init)
    def init(self, config, logger_signal=None, button_signal=None, update_signal=None, exit_signal=None, **kwargs):
        original_init(self, config, logger_signal, button_signal, update_signal, exit_signal)
        _ensure_logger_extensions(self.logger, jsonify=kwargs.get("jsonify", False))

    @wraps(original_set_ocr)
    def set_ocr(self, ocr):
        self.ocr = ocr
        ocr_client = getattr(ocr, "client", None)
        ocr_config = getattr(ocr_client, "config", None)
        if _env_enabled("BAAS_ANDROID"):
            self.ocr_img_pass_method = 1
        elif ocr_config is not None and getattr(ocr_config, "server_is_remote", False):
            self.ocr_img_pass_method = 1
        elif ocr is None:
            self.ocr_img_pass_method = 1
        else:
            self.ocr_img_pass_method = 0
            self.shared_memory_name = os.path.basename(self.config_set.config_dir)

    @wraps(original_start_emulator)
    def start_emulator(self):
        if _env_enabled("BAAS_ANDROID"):
            self.logger.info("Android embedded mode detected; skip desktop emulator startup.")
            return
        return original_start_emulator(self)

    @wraps(original_android_language)
    def _get_android_device_ocr_language(self):
        if _env_enabled("BAAS_ANDROID") and self.server == "Global":
            self.ocr_language = os.getenv("BAAS_ANDROID_GLOBAL_OCR_LANGUAGE", "en-us")
            self.logger.warning(
                "Android embedded mode cannot pull DeviceOption through adb; use " + self.ocr_language
            )
            return
        return original_android_language(self)

    @wraps(original_check_atx)
    def check_atx(self):
        if not _env_enabled("BAAS_ANDROID"):
            return original_check_atx(self)
        import requests

        self.logger.info("--------------Check ATX install ----------------")
        try:
            version = requests.get("http://127.0.0.1:7912/version", timeout=3).text
        except requests.RequestException as exc:
            raise RuntimeError(
                "Android embedded mode requires local uiautomator2 agent on 127.0.0.1:7912"
            ) from exc
        self.logger.info("ATX agent version: [ " + version + " ].")
        self.wait_uiautomator_start()
        self.logger.info("Uiautomator2 service started.")

    @wraps(original_wait_uiautomator_start)
    def wait_uiautomator_start(self):
        if not _env_enabled("BAAS_ANDROID"):
            return original_wait_uiautomator_start(self)
        import time
        import cv2
        import numpy as np

        for _ in range(0, 10):
            try:
                self.u2.uiautomator.start()
                while not self.u2.uiautomator.running():
                    time.sleep(0.1)
                self.latest_img_array = self.normalize_screenshot(
                    cv2.cvtColor(np.array(self.u2.screenshot()), cv2.COLOR_RGB2BGR)
                )
                return
            except Exception as exc:  # noqa: BLE001 - retry uiautomator startup
                print(exc)
                time.sleep(0.3)
        raise RuntimeError("Android embedded uiautomator2 agent is not responding")

    @wraps(original_check_resolution)
    def check_resolution(self):
        try:
            return original_check_resolution(self)
        except Exception:
            if _env_enabled("BAAS_ANDROID"):
                self.logger.warning("Android embedded mode accepts non-16:9 device screens.")
                return None
            raise

    @wraps(original_swipe)
    def swipe(self, fx, fy, tx, ty, duration=None, post_sleep_time=0):
        if not _env_enabled("BAAS_ANDROID"):
            return original_swipe(self, fx, fy, tx, ty, duration, post_sleep_time)
        width, height = self.resolution if getattr(self, "resolution", None) else (1280, 720)
        max_x = max(0, int(width) - 1)
        max_y = max(0, int(height) - 1)
        return original_swipe(
            self,
            min(max_x, max(0, int(fx))),
            min(max_y, max(0, int(fy))),
            min(max_x, max(0, int(tx))),
            min(max_y, max(0, int(ty))),
            duration,
            post_sleep_time,
        )

    Baas_thread.__init__ = init
    Baas_thread.set_ocr = set_ocr
    Baas_thread.start_emulator = start_emulator
    Baas_thread._get_android_device_ocr_language = _get_android_device_ocr_language
    Baas_thread.check_atx = check_atx
    Baas_thread.wait_uiautomator_start = wait_uiautomator_start
    Baas_thread.check_resolution = check_resolution
    Baas_thread.swipe = swipe
    Baas_thread._baas_service_injected = True


def _patch_device_modules() -> None:
    _install_gui_stubs()
    from service.android_local_device import ANDROID_LOCAL_METHOD, AndroidLocalControl, AndroidLocalScreenshot
    from core.device.connection import Connection
    from core.device.Control import Control
    from core.device.Screenshot import Screenshot
    from core.device.uiautomator2_client import U2Client
    from core.exception import RequestHumanTakeOver

    if not getattr(Connection, "_baas_service_injected", False):
        original_connection_init = Connection.__init__

        @staticmethod
        def _split_serial(serial):
            serial = Connection.revise_serial(serial)
            try:
                ip, port = serial.rsplit(":", 1)
            except ValueError:
                return serial, ""
            return ip, port

        def _resolve_configured_package(self):
            server = self.config.server
            if server == "auto":
                raise RequestHumanTakeOver("Android embedded mode requires an explicit game server.")
            if server == "官服" or server == "B服":
                self.server = "CN"
            elif server == "国际服" or server == "国际服青少年" or server == "韩国ONE":
                self.server = "Global"
            elif server == "日服":
                self.server = "JP"
            else:
                raise RequestHumanTakeOver("Unsupported Android game server: " + str(server))
            try:
                self.package = self.static_config.package_name[server]
                self.activity = self.static_config.activity_name[server]
            except KeyError as exc:
                raise RequestHumanTakeOver("Game package is not configured: " + str(server)) from exc
            self.logger.info("Package : " + self.package)
            self.logger.info("Server : " + self.server)

        @wraps(original_connection_init)
        def connection_init(self, Baas_instance, skip_package_detection=False):
            if _env_enabled("BAAS_ANDROID"):
                self.Baas_thread = Baas_instance
                self.logger = Baas_instance.get_logger()
                self.config_set = Baas_instance.get_config()
                self.config = self.config_set.config
                self.static_config = self.config_set.static_config
                self.skip_package_detection = skip_package_detection
                self.server = None
                self.activity = None
                self.package = None
                self.serial = os.getenv("BAAS_ANDROID_U2_SERIAL", "127.0.0.1:7912").strip() or "127.0.0.1:7912"
                self.adbIP, self.adbPort = Connection._split_serial(self.serial)
                self._is_android_device = True
                self.logger.info("Android embedded mode detected; use local uiautomator2 agent.")
                self.logger.info(f"Serial : {self.serial}")
                self._resolve_configured_package()
                return
            if skip_package_detection:
                self.Baas_thread = Baas_instance
                self.logger = Baas_instance.get_logger()
                self.config_set = Baas_instance.get_config()
                self.config = self.config_set.config
                self.static_config = self.config_set.static_config
                self.server = None
                original_detect_package = self.detect_package
                self.detect_package = lambda: None
                try:
                    self._init_android_device()
                finally:
                    self.detect_package = original_detect_package
                self._is_android_device = True
                return
            return original_connection_init(self, Baas_instance)

        original_get_current_package = Connection.get_current_package

        @wraps(original_get_current_package)
        def get_current_package(self):
            if _env_enabled("BAAS_ANDROID"):
                u2 = getattr(self.Baas_thread, "u2", None)
                if u2 is None:
                    return ""
                current = u2.app_current()
                if isinstance(current, dict):
                    return current.get("package", "")
                return getattr(current, "package", "") or ""
            return original_get_current_package(self)

        Connection._split_serial = _split_serial
        Connection._resolve_configured_package = _resolve_configured_package
        Connection.__init__ = connection_init
        Connection.get_current_package = get_current_package
        Connection._baas_service_injected = True

    if not getattr(Control, "_baas_service_injected", False):
        original_control_init = Control.init_control_instance

        @wraps(original_control_init)
        def init_control_instance(self):
            if _env_enabled("BAAS_ANDROID") and self.Baas_instance.is_android_device:
                self.method = ANDROID_LOCAL_METHOD
                self.config.control_method = ANDROID_LOCAL_METHOD
                self.logger.info("Control method : " + self.method)
                self.control_instance = AndroidLocalControl(self.connection)
                return
            return original_control_init(self)

        Control.init_control_instance = init_control_instance
        Control._baas_service_injected = True

    if not getattr(Screenshot, "_baas_service_injected", False):
        original_screenshot_init = Screenshot.init_screenshot_instance

        @wraps(original_screenshot_init)
        def init_screenshot_instance(self):
            if _env_enabled("BAAS_ANDROID") and self.Baas_instance.is_android_device:
                self.method = ANDROID_LOCAL_METHOD
                self.config.screenshot_method = ANDROID_LOCAL_METHOD
                self.logger.info("Screenshot method : " + self.method)
                self.screenshot_instance = AndroidLocalScreenshot(self.connection)
                return
            return original_screenshot_init(self)

        Screenshot.init_screenshot_instance = init_screenshot_instance
        Screenshot._baas_service_injected = True

    if not getattr(U2Client, "_baas_service_injected", False):
        original_u2_init = U2Client.__init__

        @wraps(original_u2_init)
        def u2_init(self, serial):
            if _env_enabled("BAAS_ANDROID") and not serial.startswith(("http://", "https://")):
                import uiautomator2 as u2

                self.serial = serial
                self.connection = u2.connect("http://" + serial)
                return
            return original_u2_init(self, serial)

        U2Client.__init__ = u2_init
        U2Client._baas_service_injected = True


def _patch_cafe_reward() -> None:
    import cv2
    import numpy as np
    import threading
    import time
    from module import cafe_reward

    if getattr(cafe_reward, "_baas_service_injected", False):
        return

    original_gift_to_cafe = cafe_reward.gift_to_cafe
    original_swipe_gift_and_screenshot = cafe_reward.swipe_gift_and_screenshot

    cafe_reward._happy_face_templates = None
    cafe_reward._happy_face_match_scale = 0.75
    cafe_reward._happy_face_match_roi = (0, 45, 1280, 555)

    def _resize_for_happy_face_match(img):
        height, width = img.shape[:2]
        size = (
            max(1, int(round(width * cafe_reward._happy_face_match_scale))),
            max(1, int(round(height * cafe_reward._happy_face_match_scale))),
        )
        return cv2.resize(img, size, interpolation=cv2.INTER_AREA)

    def _get_happy_face_templates():
        if cafe_reward._happy_face_templates is None:
            templates = []
            for i in range(1, 5):
                template = cv2.imread("src/images/CN/cafe/happy_face" + str(i) + ".png")
                if template is None:
                    templates.append(None)
                    continue
                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                template = _resize_for_happy_face_match(template)
                templates.append(template)
            cafe_reward._happy_face_templates = templates
        return cafe_reward._happy_face_templates

    def _dedupe_happy_face_points(points):
        deduped = []
        for x, y in sorted(points, key=lambda item: (item[1], item[0])):
            if any(abs(x - px) <= 24 and abs(y - py) <= 24 for px, py in deduped):
                continue
            deduped.append([x, y])
            if len(deduped) >= 32:
                break
        return deduped

    def _match_happy_faces_by_color(img):
        roi_x0, roi_y0, roi_x1, roi_y1 = cafe_reward._happy_face_match_roi
        search_img = img[roi_y0:roi_y1, roi_x0:roi_x1]
        hsv = cv2.cvtColor(search_img, cv2.COLOR_BGR2HSV)
        lower_red = cv2.inRange(hsv, np.array([0, 55, 120]), np.array([12, 255, 255]))
        upper_red = cv2.inRange(hsv, np.array([160, 55, 120]), np.array([179, 255, 255]))
        mask = cv2.bitwise_or(lower_red, upper_red)
        count, _, stats, centers = cv2.connectedComponentsWithStats(mask, 8)
        points = []
        for i in range(1, count):
            _, _, width, height, area = stats[i]
            if not (8 <= area <= 500 and 4 <= width <= 40 and 4 <= height <= 40):
                continue
            cx, cy = centers[i]
            points.append([int(roi_x0 + cx), int(roi_y0 + cy + 58)])
        return _dedupe_happy_face_points(points)

    def match(img):
        color_matches = _match_happy_faces_by_color(img)
        if color_matches or _env_enabled("BAAS_ANDROID"):
            return color_matches

        res = []
        roi_x0, roi_y0, roi_x1, roi_y1 = cafe_reward._happy_face_match_roi
        search_img = img[roi_y0:roi_y1, roi_x0:roi_x1]
        search_img = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)
        search_img = _resize_for_happy_face_match(search_img)
        for template in _get_happy_face_templates():
            if template is None:
                continue
            result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.75
            suppress_x = max(20, template.shape[1])
            suppress_y = max(20, template.shape[0])
            for _ in range(16):
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val < threshold:
                    break
                pt_x, pt_y = max_loc
                res.append([
                    int(roi_x0 + (pt_x + template.shape[1] / 2) / cafe_reward._happy_face_match_scale),
                    int(roi_y0 + (pt_y + template.shape[0] / 2) / cafe_reward._happy_face_match_scale + 58),
                ])
                left = max(0, pt_x - suppress_x)
                right = min(result.shape[1], pt_x + suppress_x + 1)
                top = max(0, pt_y - suppress_y)
                bottom = min(result.shape[0], pt_y + suppress_y + 1)
                result[top:bottom, left:right] = -1
        return res

    @wraps(original_gift_to_cafe)
    def gift_to_cafe(self):
        if getattr(self, "is_android_device", False):
            self.click(1240, 574, wait_over=True)
            time.sleep(0.25)
            return
        return original_gift_to_cafe(self)

    @wraps(original_swipe_gift_and_screenshot)
    def swipe_gift_and_screenshot(self):
        if not getattr(self, "is_android_device", False):
            return original_swipe_gift_and_screenshot(self)
        shot_delay = self.config.cafe_reward_interaction_shot_delay
        thread = threading.Thread(target=cafe_reward.screenshot_thread, args=(self, shot_delay))
        thread.start()
        start_t = time.time()
        self.u2_swipe(131, 660, 1280, 660, duration=0.3)
        thread.join(timeout=max(1.0, shot_delay + 1.0))
        swipe_t = round(time.time() - start_t, 3)
        self.logger.info("Gift swipe duration : [ " + str(swipe_t) + " ]")
        return swipe_t

    original_find_student_position = cafe_reward.find_student_position

    @wraps(original_find_student_position)
    def find_student_position(self):
        match_start_t = time.time()
        res = original_find_student_position(self)
        self.logger.info(
            "Cafe interaction total duration : [ "
            + str(round(time.time() - match_start_t, 3))
            + " ], candidates : [ "
            + str(len(res))
            + " ]"
        )
        return res

    cafe_reward.match = match
    cafe_reward.gift_to_cafe = gift_to_cafe
    cafe_reward.swipe_gift_and_screenshot = swipe_gift_and_screenshot
    cafe_reward.find_student_position = find_student_position
    cafe_reward._baas_service_injected = True


def apply_service_injections() -> None:
    global _APPLIED
    if _APPLIED:
        return
    _install_gui_stubs()
    _install_android_ocr_modules()
    _patch_logger()
    _patch_main()
    _patch_device_modules()
    _patch_baas_thread()
    _patch_cafe_reward()
    _APPLIED = True
