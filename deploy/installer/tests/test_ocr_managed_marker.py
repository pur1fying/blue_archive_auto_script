import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types


class FakeHead:
    target = "a" * 40


class FakeRepository:
    def __init__(self, _path):
        self.head = FakeHead()


module_names = ("pygit2", "pygit2.enums", "requests", "core.exception")
saved_modules = {name: sys.modules.get(name) for name in module_names}

fake_pygit2 = types.ModuleType("pygit2")
fake_pygit2.Repository = FakeRepository
fake_pygit2.init_repository = lambda *_args, **_kwargs: None
fake_pygit2.clone_repository = lambda *_args, **_kwargs: None
fake_pygit2.Commit = type("Commit", (), {})
fake_pygit2_enums = types.ModuleType("pygit2.enums")
fake_pygit2_enums.ResetMode = types.SimpleNamespace(HARD="hard")
sys.modules["pygit2"] = fake_pygit2
sys.modules["pygit2.enums"] = fake_pygit2_enums
sys.modules["requests"] = types.ModuleType("requests")

core_exception = types.ModuleType("core.exception")
core_exception.OcrInternalError = RuntimeError
sys.modules["core.exception"] = core_exception

source = pathlib.Path(__file__).parents[3] / "core" / "ocr" / "baas_ocr_client" / "server_installer.py"
spec = importlib.util.spec_from_file_location("baas_test_server_installer", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Logger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)


root = pathlib.Path(tempfile.mkdtemp(prefix="baas-ocr-marker-"))
try:
    module.SERVER_BIN_DIR = str(root)
    executable = pathlib.Path(module._server_binary_path())
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_bytes(b"server")
    marker = {
        "schema_version": 1,
        "managed_by": "baas-installer",
        "branch": module.TARGET_BRANCH,
        "commit": "a" * 40,
    }
    (root / ".baas-installer-managed.json").write_text(json.dumps(marker), encoding="utf-8")

    assert module.should_skip_installer_managed_update()

    class ForbiddenRepoManager:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("valid installer marker must bypass legacy OCR repository management")

    module.OcrRepoManager = ForbiddenRepoManager
    logger = Logger()
    module.check_git(logger)
    assert logger.messages == ["OCR server was verified by the BAAS installer; skipping legacy network update."]

    executable.unlink()
    assert not module.should_skip_installer_managed_update()
    executable.write_bytes(b"server")

    marker["branch"] = "wrong-platform"
    (root / ".baas-installer-managed.json").write_text(json.dumps(marker), encoding="utf-8")
    assert not module.should_skip_installer_managed_update()

    marker["branch"] = module.TARGET_BRANCH
    (root / ".baas-installer-managed.json").write_text(json.dumps(marker), encoding="utf-8")
    (root / ".git").mkdir()
    FakeHead.target = "b" * 40
    assert not module.should_skip_installer_managed_update()
    FakeHead.target = "a" * 40
    assert module.should_skip_installer_managed_update()
finally:
    shutil.rmtree(root, ignore_errors=True)
    for name, saved_module in saved_modules.items():
        if saved_module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = saved_module
