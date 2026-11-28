import json
import os
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core.Baas_thread import Baas_thread
from core.config.default_config import DEFAULT_CONFIG
from core.config.generated_user_config import Config


class CapturingLogger:
    def __init__(self):
        self.infos = []
        self.warnings = []
        self.errors = []

    def info(self, message):
        self.infos.append(str(message))

    def warning(self, message):
        self.warnings.append(str(message))

    def error(self, message):
        self.errors.append(str(message))


class FakeShellReturn:
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


class FakeSync:
    def __init__(self, mode=33206, content_bytes=b'{"Language":"En"}', stat_error=None, read_error=None):
        self.mode = mode
        self.content_bytes = content_bytes
        self.stat_error = stat_error
        self.read_error = read_error
        self.stat_calls = []
        self.read_calls = []

    def stat(self, path):
        self.stat_calls.append(path)
        if self.stat_error is not None:
            raise self.stat_error
        return SimpleNamespace(mode=self.mode)

    def read_bytes(self, path):
        self.read_calls.append(path)
        if self.read_error is not None:
            raise self.read_error
        return self.content_bytes


class PullOnlyFakeSync:
    def __init__(self, mode=33206, content_bytes=b'{"Language":"Tw"}'):
        self.mode = mode
        self.content_bytes = content_bytes
        self.pull_calls = []

    def stat(self, path):
        return SimpleNamespace(mode=self.mode)

    def pull_file(self, src, dst):
        self.pull_calls.append((src, dst))
        Path(dst).write_bytes(self.content_bytes)
        return len(self.content_bytes)


class FakeAdbDevice:
    def __init__(self, sync, shell2_handler=None):
        self.sync = sync
        self._shell2_handler = shell2_handler
        self.shell2_calls = []

    def shell2(self, command, timeout=None):
        self.shell2_calls.append((command, timeout))
        if self._shell2_handler is None:
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            return FakeShellReturn(1, "")
        return self._shell2_handler(command, timeout)


def make_baas(adb_device=None, server="Global", package_name="com.nexon.bluearchive", global_ocr_language="auto"):
    baas = Baas_thread.__new__(Baas_thread)
    baas.logger = CapturingLogger()
    baas.server = server
    baas.package_name = package_name
    baas.ocr_language = "None"
    baas.config = SimpleNamespace(global_ocr_language=global_ocr_language)
    baas.config_set = SimpleNamespace(config_dir="/tmp/default_config", config=baas.config)
    baas.u2 = SimpleNamespace(_adb_device=adb_device) if adb_device is not None else None
    return baas


class GlobalDeviceOptionLanguageTest(unittest.TestCase):
    def test_sync_fast_path_reads_in_memory_without_cwd_file(self):
        sync = FakeSync(mode=33206, content_bytes='\ufeff{"Language":"Tw"}'.encode("utf-8"))
        adb_device = FakeAdbDevice(sync=sync)
        baas = make_baas(adb_device=adb_device)

        cwd_before = set(os.listdir(os.getcwd()))
        baas._get_android_device_ocr_language()
        cwd_after = set(os.listdir(os.getcwd()))

        self.assertEqual(baas.ocr_language, "zh-tw")
        self.assertEqual(
            sync.stat_calls,
            ["/sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption"],
        )
        self.assertEqual(len(sync.read_calls), 1)
        # Only queried $EXTERNAL_STORAGE, never invoked su
        self.assertEqual([cmd for cmd, _ in adb_device.shell2_calls], ["echo $EXTERNAL_STORAGE"])
        self.assertEqual(cwd_before, cwd_after)

    def test_sync_pull_file_fallback_cleans_up_temp_file(self):
        sync = PullOnlyFakeSync(mode=33206, content_bytes='\ufeff{"Language":"Kr"}'.encode("utf-8"))
        adb_device = FakeAdbDevice(sync=sync)
        baas = make_baas(adb_device=adb_device)

        baas._get_android_device_ocr_language()

        self.assertEqual(baas.ocr_language, "ko-kr")
        self.assertEqual(len(sync.pull_calls), 1)
        _, pulled_path = sync.pull_calls[0]
        self.assertFalse(os.path.exists(pulled_path))

    def test_su_dash_c_fallback_plain_utf8_and_bom(self):
        for payload, expected in (
            ('{"Language":"En"}', "en-us"),
            ('\ufeff{"Language":"Tw"}', "zh-tw"),
        ):
            with self.subTest(expected=expected):
                sync = FakeSync(mode=0)

                def handler(command, timeout):
                    if command == "echo $EXTERNAL_STORAGE":
                        return FakeShellReturn(0, "/sdcard\n")
                    if command.startswith("su -c "):
                        self.assertEqual(timeout, Baas_thread._DEVICE_OPTION_SHELL_TIMEOUT)
                        return FakeShellReturn(0, payload)
                    return FakeShellReturn(1, "unexpected")

                adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
                baas = make_baas(adb_device=adb_device)

                baas._get_android_device_ocr_language()

                self.assertEqual(baas.ocr_language, expected)
                self.assertTrue(any(cmd.startswith("su -c ") for cmd, _ in adb_device.shell2_calls))
                self.assertFalse(any(cmd.startswith("su 0 ") for cmd, _ in adb_device.shell2_calls))

    def test_su_falls_back_to_su_0_when_su_dash_c_fails(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "")  # also exercises empty EXTERNAL_STORAGE -> /sdcard
            if command.startswith("su -c "):
                return FakeShellReturn(1, "su: invalid option -c")
            if command.startswith("su 0 cat "):
                return FakeShellReturn(0, '{"Language":"Kr"}')
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        baas._get_android_device_ocr_language()

        self.assertEqual(baas.ocr_language, "ko-kr")
        commands = [cmd for cmd, _ in adb_device.shell2_calls]
        self.assertIn(
            "su -c 'cat /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption'",
            commands,
        )
        self.assertIn(
            "su 0 cat /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption",
            commands,
        )

    def test_su_falls_back_to_data_media_0_on_mount_namespace_restriction(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/storage/emulated/0\n")
            if "/storage/emulated/0/" in command:
                return FakeShellReturn(1, "cat: /storage/emulated/0/Android/data/com.nexon.bluearchive/files/DeviceOption: No such file or directory")
            if "/data/media/0/" in command and command.startswith("su -c "):
                return FakeShellReturn(0, '{"Language":"Tw"}')
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        baas._get_android_device_ocr_language()

        self.assertEqual(baas.ocr_language, "zh-tw")
        self.assertTrue(any("/data/media/0/" in cmd for cmd, _ in adb_device.shell2_calls))

    def test_su_warning_output_does_not_bypass_json_validation(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            if command.startswith("su -c "):
                return FakeShellReturn(0, 'WARNING: linker warning\n{"Language":"Tw"}')
            if command.startswith("su 0 cat "):
                return FakeShellReturn(0, '{"Language":"Tw"}')
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        baas._get_android_device_ocr_language()

        self.assertEqual(baas.ocr_language, "zh-tw")

    def test_permission_denied_without_su_raises_clear_permission_error(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            if command.startswith("su "):
                return FakeShellReturn(127, "/system/bin/sh: su: inaccessible or not found")
            if command.startswith("ls -ld "):
                return FakeShellReturn(
                    1,
                    "ls: /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption: Permission denied",
                )
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        with self.assertRaises(PermissionError) as ctx:
            baas._get_android_device_ocr_language()

        message = str(ctx.exception)
        self.assertIn("Permission denied", message)
        self.assertIn("Android 11+", message)
        self.assertIn("adb root", message)
        self.assertIn("global_ocr_language", message)
        self.assertTrue(baas.logger.errors)

    def test_su_timeout_falls_through_to_permission_diagnosis(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            if command.startswith("su "):
                raise TimeoutError("su prompt timed out")
            if command.startswith("ls -ld "):
                return FakeShellReturn(
                    1,
                    "ls: /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption: Permission denied",
                )
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        with self.assertRaises(PermissionError) as ctx:
            baas._get_android_device_ocr_language()

        self.assertIn("TimeoutError", str(ctx.exception))

    def test_missing_file_raises_file_not_found_error(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            if command.startswith("su "):
                return FakeShellReturn(127, "/system/bin/sh: su: inaccessible or not found")
            if command.startswith("ls -ld "):
                return FakeShellReturn(
                    1,
                    "ls: /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption: No such file or directory",
                )
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        with self.assertRaises(FileNotFoundError) as ctx:
            baas._get_android_device_ocr_language()

        self.assertIn("Global Server DeviceOption File not exist", str(ctx.exception))

    def test_root_confirmed_missing_file_beats_non_root_permission_denied(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            if command.startswith("su -c "):
                if "/data/media/0/" in command:
                    return FakeShellReturn(
                        1,
                        "cat: /data/media/0/Android/data/com.nexon.bluearchive/files/DeviceOption: No such file or directory",
                    )
                return FakeShellReturn(
                    1,
                    "cat: /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption: No such file or directory",
                )
            if command.startswith("su 0 "):
                return FakeShellReturn(1, "su: invalid user")
            if command.startswith("ls -ld "):
                return FakeShellReturn(
                    1,
                    "ls: /sdcard/Android/data/com.nexon.bluearchive/files/DeviceOption: Permission denied",
                )
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        with self.assertRaises(FileNotFoundError) as ctx:
            baas._get_android_device_ocr_language()

        self.assertIn("Global Server DeviceOption File not exist", str(ctx.exception))

    def test_corrupted_json_and_invalid_language_raise_value_error(self):
        for payload, expected_fragment in (
            (b"{not-valid-json", "Failed to parse Global Server DeviceOption JSON"),
            (b'{"BGM": {}}', "missing 'Language' field"),
            (b'{"Language":"De"}', "Global Server Invalid Language : De."),
        ):
            with self.subTest(payload=payload):
                sync = FakeSync(mode=33206, content_bytes=payload)
                adb_device = FakeAdbDevice(sync=sync)
                baas = make_baas(adb_device=adb_device)

                with self.assertRaises(ValueError) as ctx:
                    baas._get_android_device_ocr_language()

                self.assertIn(expected_fragment, str(ctx.exception))

    def test_corrupted_json_via_su_raises_value_error(self):
        sync = FakeSync(mode=0)

        def handler(command, timeout):
            if command == "echo $EXTERNAL_STORAGE":
                return FakeShellReturn(0, "/sdcard\n")
            if command.startswith("su "):
                return FakeShellReturn(0, "{broken-json")
            return FakeShellReturn(1, "")

        adb_device = FakeAdbDevice(sync=sync, shell2_handler=handler)
        baas = make_baas(adb_device=adb_device)

        with self.assertRaises(ValueError) as ctx:
            baas._get_android_device_ocr_language()

        self.assertIn("Failed to parse Global Server DeviceOption JSON", str(ctx.exception))

    def test_config_override_skips_adb_completely(self):
        baas = make_baas(adb_device=None, global_ocr_language="ZH-TW")

        baas._get_android_device_ocr_language()

        self.assertEqual(baas.ocr_language, "zh-tw")

    def test_invalid_config_override_raises_value_error(self):
        baas = make_baas(adb_device=None, global_ocr_language="ja-jp")

        with self.assertRaises(ValueError) as ctx:
            baas._get_android_device_ocr_language()

        self.assertIn("Invalid global_ocr_language config", str(ctx.exception))

    def test_host_device_option_reads_utf8_bom(self):
        baas = make_baas(adb_device=None)
        with tempfile.TemporaryDirectory() as tmp_dir:
            option_path = Path(tmp_dir) / "DeviceOption"
            option_path.write_bytes('\ufeff{"Language":"Tw"}'.encode("utf-8"))
            baas._read_DeviceOption_ocr_language(str(option_path))

        self.assertEqual(baas.ocr_language, "zh-tw")

    def test_cn_and_jp_servers_unchanged(self):
        for server, expected in (("CN", "zh-cn"), ("JP", "ja-jp")):
            with self.subTest(server=server):
                baas = make_baas(adb_device=None, server=server)
                baas._get_android_device_ocr_language()
                self.assertEqual(baas.ocr_language, expected)

    def test_default_config_and_dataclass_include_global_ocr_language(self):
        default_data = json.loads(DEFAULT_CONFIG)
        self.assertEqual(default_data.get("global_ocr_language"), "auto")
        field_names = {f.name for f in fields(Config)}
        self.assertIn("global_ocr_language", field_names)


if __name__ == "__main__":
    unittest.main()
