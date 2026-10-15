import json
from types import SimpleNamespace

import pytest

from core.ocr.baas_ocr_client import server_installer


@pytest.mark.parametrize(
    ("has_repository", "needs_update", "expected"),
    [
        (False, False, ["clone"]),
        (True, False, ["local", "remote"]),
        (True, True, ["local", "remote", "update", "local"]),
    ],
)
def test_stale_native_installer_marker_does_not_bypass_ocr_updates(
    monkeypatch, tmp_path, has_repository, needs_update, expected
):
    calls = []
    local_sha = "a" * 40
    remote_sha = "b" * 40 if needs_update else local_sha
    monkeypatch.setattr(server_installer, "SERVER_BIN_DIR", str(tmp_path))
    monkeypatch.setattr(server_installer, "_is_android_runtime", lambda: False)
    monkeypatch.setattr(
        server_installer.pygit2,
        "Repository",
        lambda _path: SimpleNamespace(head=SimpleNamespace(target=local_sha)),
    )
    # Existing installations can retain the removed installer's handoff file.
    # A valid old marker must no longer suppress ordinary Python OCR updates.
    (tmp_path / ".baas-installer-managed.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "managed_by": "baas-installer",
                "branch": server_installer.TARGET_BRANCH,
                "commit": local_sha,
            }
        ),
        encoding="utf-8",
    )
    binary = server_installer._server_binary_path()
    with open(binary, "wb") as output:
        output.write(b"server")
    if has_repository:
        (tmp_path / ".git").mkdir()

    class RepositoryManager:
        def __init__(self, *_args):
            self.git_dir = str(tmp_path / ".git")
            self.current_sha = local_sha

        def clone(self):
            calls.append("clone")

        def get_local_sha(self):
            calls.append("local")
            return self.current_sha

        def get_remote_sha(self):
            calls.append("remote")
            return remote_sha

        def update(self):
            calls.append("update")
            self.current_sha = remote_sha

    monkeypatch.setattr(server_installer, "OcrRepoManager", RepositoryManager)
    logger = SimpleNamespace(info=lambda _message: None, warning=lambda _message: None)

    server_installer.check_git(logger)

    assert calls == expected
