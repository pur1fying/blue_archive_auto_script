import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types


class FakeRepo:
    expected_head = b"a" * 40

    def __init__(self, _path):
        pass

    def head(self):
        return self.expected_head


core_exception = types.ModuleType("core.exception")
core_exception.OcrInternalError = RuntimeError
sys.modules["core.exception"] = core_exception
dulwich = types.ModuleType("dulwich")
dulwich.porcelain = types.SimpleNamespace()
sys.modules["dulwich"] = dulwich
dulwich_repo = types.ModuleType("dulwich.repo")
dulwich_repo.Repo = FakeRepo
sys.modules["dulwich.repo"] = dulwich_repo

source = pathlib.Path(__file__).parents[3] / "core" / "ocr" / "baas_ocr_client" / "server_installer.py"
spec = importlib.util.spec_from_file_location("baas_test_server_installer", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

root = pathlib.Path(tempfile.mkdtemp(prefix="baas-ocr-marker-"))
try:
    module.SERVER_BIN_DIR = str(root)
    executable = root / ("BAAS_ocr_server.exe" if sys.platform == "win32" else "BAAS_ocr_server")
    executable.write_bytes(b"server")
    marker = {
        "schema_version": 1,
        "managed_by": "baas-installer",
        "branch": module.branch,
        "commit": "a" * 40,
    }
    (root / ".baas-installer-managed.json").write_text(json.dumps(marker), encoding="utf-8")
    assert module.should_skip_installer_managed_update()
    executable.unlink()
    assert not module.should_skip_installer_managed_update()
    executable.write_bytes(b"server")
    marker["branch"] = "wrong-platform"
    (root / ".baas-installer-managed.json").write_text(json.dumps(marker), encoding="utf-8")
    assert not module.should_skip_installer_managed_update()
    marker["branch"] = module.branch
    (root / ".baas-installer-managed.json").write_text(json.dumps(marker), encoding="utf-8")
    (root / ".git").mkdir()
    FakeRepo.expected_head = b"b" * 40
    assert not module.should_skip_installer_managed_update()
    FakeRepo.expected_head = b"a" * 40
    assert module.should_skip_installer_managed_update()
finally:
    shutil.rmtree(root, ignore_errors=True)
