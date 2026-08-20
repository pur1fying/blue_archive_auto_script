import os
import traceback
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QWidget

from core import pushkit
from deploy.installer.mirrorc_update import mirrorc_updater
from gui.components.expand import baasUpdateConfig


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


class FakeConfig:
    def __init__(self):
        self.saved = []

    def set_and_save(self, key, value):
        self.saved.append((key, value))


class SecretRedactionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def assert_masked(self, output, secret, label):
        self.assertNotIn(secret, output)
        self.assertIn(f"{label}=**", output)

    def test_feishu_exception_masks_webhook(self):
        webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/FEISHU_TEST_SECRET"
        logger = CapturingLogger()

        with patch.object(
            pushkit.requests,
            "post",
            side_effect=requests.ConnectionError(f"failed to connect to {webhook}"),
        ):
            pushkit.push_feishu(logger, webhook, {"title": "title", "desp": "body"})

        self.assertEqual(len(logger.errors), 1)
        self.assertIn("ConnectionError", logger.errors[0])
        self.assert_masked(logger.errors[0], "FEISHU_TEST_SECRET", "webhook")

    def test_wecom_exception_masks_webhook(self):
        webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=WECOM_TEST_SECRET"
        logger = CapturingLogger()

        with patch.object(
            pushkit.requests,
            "post",
            side_effect=requests.ConnectionError(f"failed to connect to {webhook}"),
        ):
            pushkit.push_wecom(logger, webhook, {"title": "title", "desp": "body"})

        self.assertEqual(len(logger.errors), 1)
        self.assertIn("ConnectionError", logger.errors[0])
        self.assert_masked(logger.errors[0], "WECOM_TEST_SECRET", "webhook")

    def test_push_requests_keep_complete_webhooks(self):
        feishu_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/FEISHU_FULL_SECRET"
        wecom_webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=WECOM_FULL_SECRET"
        logger = CapturingLogger()
        feishu_response = Mock(status_code=200)
        feishu_response.json.return_value = {"code": 0}
        wecom_response = Mock(status_code=200)
        wecom_response.json.return_value = {"errcode": 0}

        with patch.object(
            pushkit.requests,
            "post",
            side_effect=[feishu_response, wecom_response],
        ) as post_request:
            pushkit.push_feishu(logger, feishu_webhook, {"title": "title", "desp": "body"})
            pushkit.push_wecom(logger, wecom_webhook, {"title": "title", "desp": "body"})

        self.assertEqual(post_request.call_args_list[0].args[0], feishu_webhook)
        self.assertEqual(post_request.call_args_list[1].args[0], wecom_webhook)

    def test_mirrorc_latest_version_masks_request_exception(self):
        cdk = "MIRRORC_LATEST_TEST_SECRET"
        updater = mirrorc_updater.MirrorC_Updater()

        with patch.object(
            mirrorc_updater.requests,
            "get",
            side_effect=requests.ConnectionError(f"failed URL ?cdk={cdk}"),
        ):
            with self.assertRaises(Exception) as raised:
                updater.get_latest_version(cdk=cdk)

        self.assertEqual(type(raised.exception).__name__, "MirrorCRequestError")
        self.assertIn("ConnectionError", str(raised.exception))
        self.assert_masked(str(raised.exception), cdk, "cdk")

    def test_mirrorc_cdk_state_masks_request_exception(self):
        cdk = "MIRRORC_STATE_TEST_SECRET"
        updater = mirrorc_updater.MirrorC_Updater()

        with patch.object(
            mirrorc_updater.requests,
            "get",
            side_effect=requests.ConnectionError(f"failed URL ?cdk={cdk}"),
        ):
            with self.assertRaises(Exception) as raised:
                updater.get_cdk_state(cdk=cdk)

        self.assertEqual(type(raised.exception).__name__, "MirrorCRequestError")
        self.assertIn("ConnectionError", str(raised.exception))
        self.assert_masked(str(raised.exception), cdk, "cdk")

    def test_mirrorc_response_parse_exception_masks_cdk_and_traceback(self):
        cdk = "MIRRORC_PARSE_TEST_SECRET"
        response = Mock()
        response.json.side_effect = ValueError(f"invalid response for cdk={cdk}")
        updater = mirrorc_updater.MirrorC_Updater()

        with patch.object(mirrorc_updater.requests, "get", return_value=response):
            with self.assertRaises(Exception) as raised:
                updater.get_latest_version(cdk=cdk)

        rendered_traceback = "".join(
            traceback.format_exception(
                type(raised.exception), raised.exception, raised.exception.__traceback__
            )
        )
        self.assertEqual(type(raised.exception).__name__, "MirrorCRequestError")
        self.assertIn("ValueError", str(raised.exception))
        self.assert_masked(rendered_traceback, cdk, "cdk")

    def test_mirrorc_cdk_state_masks_malformed_response(self):
        cdk = "MIRRORC_STATE_PARSE_TEST_SECRET"
        response = Mock()
        response.json.return_value = {"code": f"invalid cdk={cdk}"}
        updater = mirrorc_updater.MirrorC_Updater()

        with patch.object(mirrorc_updater.requests, "get", return_value=response):
            with self.assertRaises(Exception) as raised:
                updater.get_cdk_state(cdk=cdk)

        self.assertEqual(type(raised.exception).__name__, "MirrorCRequestError")
        self.assertIn("TypeError", str(raised.exception))
        self.assert_masked(str(raised.exception), cdk, "cdk")

    def test_mirrorc_latest_version_masks_malformed_response(self):
        cdk = "MIRRORC_LATEST_PARSE_TEST_SECRET"
        response = Mock()
        response.json.return_value = {"code": 0, "msg": "ok", "data": []}
        updater = mirrorc_updater.MirrorC_Updater()

        with patch.object(mirrorc_updater.requests, "get", return_value=response):
            with self.assertRaises(Exception) as raised:
                updater.get_latest_version(cdk=cdk)

        self.assertEqual(type(raised.exception).__name__, "MirrorCRequestError")
        self.assertIn("AttributeError", str(raised.exception))
        self.assert_masked(str(raised.exception), cdk, "cdk")

    def test_mirrorc_cdk_state_does_not_print_response(self):
        response = Mock()
        response.json.return_value = {"code": 0, "msg": "ok", "data": {}}
        updater = mirrorc_updater.MirrorC_Updater()

        with patch.object(mirrorc_updater.requests, "get", return_value=response), patch(
            "builtins.print"
        ) as printed:
            state = updater.get_cdk_state(cdk="MIRRORC_VALID_TEST_SECRET")

        self.assertEqual(state, mirrorc_updater.CdkState.VALID)
        printed.assert_not_called()

    def test_mirrorc_error_logger_omits_server_message(self):
        secret = "MIRRORC_SERVER_MESSAGE_TEST_SECRET"
        logger = CapturingLogger()
        request_return = Mock(
            code=mirrorc_updater.MirrorCErrorCode.UNDIVIDED.value,
            message=f"server rejected cdk={secret}",
        )

        mirrorc_updater.MirrorC_Updater.log_mirrorc_error(request_return, logger)

        output = "\n".join(logger.warnings)
        self.assertIn(str(request_return.code), output)
        self.assert_masked(output, secret, "cdk")

    def test_legacy_installer_does_not_log_raw_mirrorc_message(self):
        installer_path = (
            Path(__file__).resolve().parents[2] / "deploy" / "installer" / "installer.py"
        )
        installer_source = installer_path.read_text(encoding="utf-8")

        self.assertNotIn("latest_mirrorc_return.message", installer_source)
        self.assertIn("latest_mirrorc_return.code", installer_source)
        self.assertIn("cdk=**", installer_source)

    def test_mirrorc_gui_masks_saved_cdk_notification(self):
        cdk = "MIRRORC_GUI_SAVE_TEST_SECRET"
        layout = baasUpdateConfig.Layout.__new__(baasUpdateConfig.Layout)
        QWidget.__init__(layout)
        layout.config = FakeConfig()
        notifications = []

        def capture_success(label, message, config):
            notifications.append((label, message, config))

        with patch.object(baasUpdateConfig, "success", capture_success):
            layout._Layout__set_config_and_display_message("General.mirrorc_cdk", cdk)

        self.assertEqual(layout.config.saved, [("General.mirrorc_cdk", cdk)])
        self.assertEqual(len(notifications), 1)
        self.assertNotIn(cdk, notifications[0][1])
        self.assertEqual(notifications[0][1], "General.mirrorc_cdk = **")
        layout.deleteLater()

    def test_mirrorc_gui_keeps_non_secret_notification_value(self):
        layout = baasUpdateConfig.Layout.__new__(baasUpdateConfig.Layout)
        QWidget.__init__(layout)
        layout.config = FakeConfig()
        notifications = []

        def capture_success(label, message, config):
            notifications.append((label, message, config))

        with patch.object(baasUpdateConfig, "success", capture_success):
            layout._Layout__set_config_and_display_message("General.get_remote_sha_method", "github")

        self.assertEqual(notifications[0][1], "General.get_remote_sha_method = github")
        layout.deleteLater()

    def test_mirrorc_gui_masks_error_notification(self):
        cdk = "MIRRORC_GUI_ERROR_TEST_SECRET"
        notifications = []

        class FailingMirrorC:
            def get_latest_version(self, cdk, timeout):
                raise requests.ConnectionError(f"failed URL ?cdk={cdk}")

        layout = Mock()
        layout._mirrorc_inst = FailingMirrorC()
        worker = baasUpdateConfig.MirrorCCDKTestThread(layout, cdk)

        def capture_error(label, message, config):
            notifications.append((label, message, config))

        with patch.object(baasUpdateConfig, "error", capture_error):
            worker.run()

        self.assertEqual(len(notifications), 1)
        self.assertIn("ConnectionError", notifications[0][1])
        self.assert_masked(notifications[0][1], cdk, "cdk")


if __name__ == "__main__":
    unittest.main()
