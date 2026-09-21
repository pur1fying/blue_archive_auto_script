from __future__ import annotations

import sys
import types

from service import injection


def _install_fake_core(monkeypatch, logger_cls):
    utils = types.SimpleNamespace(Logger=logger_cls)
    core = types.SimpleNamespace(utils=utils)
    monkeypatch.setitem(sys.modules, "core", core)
    monkeypatch.setitem(sys.modules, "core.utils", utils)


def test_patch_logger_supports_core_logger_without_log(monkeypatch):
    class Logger:
        def __init__(self, logger_signal):
            self.logger_signal = logger_signal

        def __out__(self, message, level=1, raw_print=False):
            raise AssertionError("json logger should queue instead of writing directly")

        def info(self, message):
            self.__out__(message, 1)

    monkeypatch.delenv("BAAS_ANDROID", raising=False)
    _install_fake_core(monkeypatch, Logger)

    injection._patch_logger()
    logger = Logger(None, jsonify=True)
    logger.info("message")

    assert logger.jsonify is True
    assert logger.log_collector.get_nowait()["message"] == "message"
    assert not hasattr(Logger, "log")


def test_patch_logger_wraps_legacy_log_when_available(monkeypatch):
    class Logger:
        def __init__(self, logger_signal):
            self.logger_signal = logger_signal
            self.messages = []

        def log(self, level, message):
            self.messages.append((level, message))

    monkeypatch.delenv("BAAS_ANDROID", raising=False)
    _install_fake_core(monkeypatch, Logger)

    injection._patch_logger()
    logger = Logger(None, jsonify=True)
    logger.log(2, "message")

    assert logger.log_collector.get_nowait()["message"] == "message"
