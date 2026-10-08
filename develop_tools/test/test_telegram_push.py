import os
import unittest
from unittest.mock import patch

import requests

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core import pushkit

BOT_TOKEN = "123456:ABC-DEF_TELEGRAM_TEST_TOKEN"
CHAT_ID = "987654321"
DATA = {"title": "Baas Error", "desp": "something went wrong"}


class CapturingLogger:
    def __init__(self):
        self.errors = []
        self.infos = []
        self.warnings = []

    def error(self, message):
        self.errors.append(str(message))

    def info(self, message):
        self.infos.append(str(message))

    def warning(self, message):
        self.warnings.append(str(message))


class FakeResponse:
    def __init__(self, status_code=200, payload=None, raise_on_json=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._raise_on_json = raise_on_json

    def json(self):
        if self._raise_on_json:
            raise ValueError("no json in response")
        return self._payload


class FakeTelegramConfig:
    def __init__(self, **overrides):
        self.push_after_error = True
        self.push_after_completion = True
        self.push_json = ""
        self.push_serverchan = ""
        self.push_feishu = ""
        self.push_wecom = ""
        self.push_telegram_bot_token = BOT_TOKEN
        self.push_telegram_chat_id = CHAT_ID
        self.push_telegram_proxy = ""
        self.push_telegram_api = ""
        for key, value in overrides.items():
            setattr(self, key, value)


class TelegramPushTest(unittest.TestCase):
    def test_default_url_and_payload(self):
        logger = CapturingLogger()
        with patch.object(pushkit.requests, "post", return_value=FakeResponse(payload={"ok": True})) as mock_post:
            pushkit.push_telegram(logger, BOT_TOKEN, CHAT_ID, DATA)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage")
        self.assertEqual(kwargs["json"], {"chat_id": CHAT_ID, "text": DATA["title"] + "\n" + DATA["desp"]})
        self.assertIsNone(kwargs["proxies"])
        self.assertEqual(kwargs["timeout"], 30)
        self.assertEqual(logger.infos, ["[ Telegram ] push success"])
        self.assertEqual(logger.errors, [])

    def test_custom_api_base_strips_trailing_slash(self):
        logger = CapturingLogger()
        with patch.object(pushkit.requests, "post", return_value=FakeResponse(payload={"ok": True})) as mock_post:
            pushkit.push_telegram(logger, BOT_TOKEN, CHAT_ID, DATA, api="https://tlg.example.com/")

        args, _ = mock_post.call_args
        self.assertEqual(args[0], f"https://tlg.example.com/bot{BOT_TOKEN}/sendMessage")

    def test_proxies_are_passed_when_set(self):
        logger = CapturingLogger()
        with patch.object(pushkit.requests, "post", return_value=FakeResponse(payload={"ok": True})) as mock_post:
            pushkit.push_telegram(logger, BOT_TOKEN, CHAT_ID, DATA, proxy="http://127.0.0.1:7890")

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["proxies"], {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"})

    def test_api_error_description_is_logged(self):
        logger = CapturingLogger()
        with patch.object(
            pushkit.requests,
            "post",
            return_value=FakeResponse(status_code=400, payload={"ok": False, "description": "chat not found"}),
        ):
            pushkit.push_telegram(logger, BOT_TOKEN, CHAT_ID, DATA)

        self.assertEqual(logger.infos, [])
        self.assertEqual(logger.errors, ["[ Telegram ] push failed: chat not found"])

    def test_non_json_response_is_handled(self):
        # e.g. a proxy answering HTTP 200 with an HTML page
        logger = CapturingLogger()
        with patch.object(pushkit.requests, "post", return_value=FakeResponse(raise_on_json=True)):
            pushkit.push_telegram(logger, BOT_TOKEN, CHAT_ID, DATA)

        self.assertEqual(logger.infos, [])
        self.assertEqual(len(logger.errors), 1)
        self.assertIn("not JSON", logger.errors[0])

    def test_exception_log_does_not_leak_token(self):
        logger = CapturingLogger()
        with patch.object(
            pushkit.requests,
            "post",
            side_effect=requests.ConnectionError(f"cannot reach bot{BOT_TOKEN}"),
        ):
            pushkit.push_telegram(logger, BOT_TOKEN, CHAT_ID, DATA)

        self.assertEqual(logger.infos, [])
        self.assertEqual(len(logger.errors), 1)
        self.assertNotIn(BOT_TOKEN, logger.errors[0])
        self.assertIn("ConnectionError", logger.errors[0])

    def test_push_dispatches_telegram_only_when_both_set(self):
        logger = CapturingLogger()
        config = FakeTelegramConfig(push_telegram_chat_id="")

        with patch.object(pushkit, "push_telegram") as mock_push:
            pushkit.push(logger, config)

        mock_push.assert_not_called()

    def test_push_dispatches_telegram_with_all_settings(self):
        logger = CapturingLogger()
        config = FakeTelegramConfig(
            push_after_error=False,
            push_telegram_proxy="http://127.0.0.1:7890",
            push_telegram_api="https://tlg.example.com",
        )

        with patch.object(pushkit, "push_telegram", return_value=None) as mock_push:
            pushkit.push(logger, config)

        mock_push.assert_called_once_with(
            logger,
            BOT_TOKEN,
            CHAT_ID,
            {"title": "Baas Completed", "desp": "all activities finished"},
            "http://127.0.0.1:7890",
            "https://tlg.example.com",
        )


if __name__ == "__main__":
    unittest.main()
