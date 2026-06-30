from __future__ import annotations

import os
import queue
import traceback
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


def _patch_logger() -> None:
    from core import utils

    logger_cls = utils.Logger
    if getattr(logger_cls, "_baas_service_injected", False):
        return

    original_init = logger_cls.__init__
    original_log = logger_cls.log

    @wraps(original_init)
    def init(self, logger_signal, jsonify=False):
        if _supports_parameter(original_init, "jsonify"):
            original_init(self, logger_signal, jsonify=jsonify)
        else:
            original_init(self, logger_signal)
        _ensure_logger_extensions(self, jsonify=jsonify)

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

    logger_cls.__init__ = init
    logger_cls.log = log
    logger_cls._baas_service_injected = True


def _patch_main() -> None:
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
            ConfigSet.static_config = ConfigSet.static_config
            if ConfigSet.static_config is None:
                ConfigSet.static_config = ConfigSet().static_config
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
    from core.Baas_thread import Baas_thread

    if getattr(Baas_thread, "_baas_service_injected", False):
        return

    original_init = Baas_thread.__init__

    @wraps(original_init)
    def init(self, config, logger_signal=None, button_signal=None, update_signal=None, exit_signal=None, **kwargs):
        original_init(self, config, logger_signal, button_signal, update_signal, exit_signal)
        _ensure_logger_extensions(self.logger, jsonify=kwargs.get("jsonify", False))

    Baas_thread.__init__ = init
    Baas_thread._baas_service_injected = True


def apply_service_injections() -> None:
    global _APPLIED
    if _APPLIED:
        return
    _patch_logger()
    _patch_main()
    _patch_baas_thread()
    _APPLIED = True
