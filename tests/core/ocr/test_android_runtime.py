from __future__ import annotations

from core.ocr.baas_ocr_client import Client
from core.ocr.baas_ocr_client import server_installer


class _Logger:
    def info(self, _message):
        return None

    def warning(self, _message):
        return None


def test_android_ocr_installer_reuses_internal_runtime(monkeypatch, tmp_path):
    branch = "android-x86_64"
    remote_sha = "abc123"
    internal_root = tmp_path / "files"
    runtime_root = internal_root / "ocr-runtime" / branch
    runtime_lib = runtime_root / "lib" / "x86_64" / "libBAAS_ocr_server.so"
    runtime_lib.parent.mkdir(parents=True)
    runtime_lib.write_bytes(b"runtime")
    (runtime_root / ".baas-ocr-prebuild-sha").write_text(remote_sha, encoding="utf-8")

    source_root = tmp_path / "source"
    monkeypatch.setenv("BAAS_ANDROID_INTERNAL_FILES_DIR", str(internal_root))
    monkeypatch.setattr(server_installer, "TARGET_BRANCH", branch)
    monkeypatch.setattr(server_installer, "SERVER_BIN_DIR", str(source_root))
    monkeypatch.setattr(server_installer, "ANDROID_VERSION_FILE", str(source_root / ".baas-ocr-prebuild-sha"))
    monkeypatch.setattr(server_installer, "_get_android_remote_sha", lambda _branch: remote_sha)

    def fail_download(*_args, **_kwargs):
        raise AssertionError("installed Android OCR runtime should not be downloaded again")

    monkeypatch.setattr(server_installer, "_download_android_archive", fail_download)

    server_installer._install_android_prebuild(_Logger())


def test_android_ocr_client_reuses_internal_runtime_without_source(monkeypatch, tmp_path):
    branch = "android-x86_64"
    runtime_root = tmp_path / "files" / "ocr-runtime" / branch
    runtime_lib = runtime_root / "lib" / "x86_64" / "libBAAS_ocr_server.so"
    runtime_lib.parent.mkdir(parents=True)
    runtime_lib.write_bytes(b"runtime")
    (runtime_root / ".baas-ocr-prebuild-sha").write_text("abc123", encoding="utf-8")

    source_root = tmp_path / "source"
    monkeypatch.setenv("BAAS_ANDROID_INTERNAL_FILES_DIR", str(tmp_path / "files"))
    monkeypatch.setattr(Client, "_server_folder_path", lambda: str(source_root))
    monkeypatch.setattr(Client, "_android_ocr_branch", lambda: branch)

    client = Client.BaasOcrClient.__new__(Client.BaasOcrClient)

    assert client._prepare_android_runtime_folder() == str(runtime_root)
