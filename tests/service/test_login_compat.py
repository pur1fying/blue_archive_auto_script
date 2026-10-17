from __future__ import annotations

import ast
import importlib.util
import os
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

from core import color, image, position
from core.exception import FunctionCallTimeout, PackageIncorrect, RequestHumanTakeOver
from service import login_compat


def _load_core_function(path, name, namespace):
    """Exercise the real task retry/stage order without loading a GUI or device."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


def test_import_does_not_install_hooks_for_legacy_gui(monkeypatch):
    before = (image.compare_image, color.match_rgb_feature, sys.modules.get("core.Baas_thread"))
    spec = importlib.util.spec_from_file_location("_login_compat_import_test", login_compat.__file__)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    assert (image.compare_image, color.match_rgb_feature, sys.modules.get("core.Baas_thread")) == before


@pytest.fixture
def runtime(monkeypatch):
    import core
    import time

    root = Path(__file__).resolve().parents[2]
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(login_compat.time, "monotonic", lambda: clock.now)
    picture = SimpleNamespace(deal_with_pop_ups=lambda context, *args, **kwargs: context.popups.append((args, kwargs)) or False)
    monkeypatch.setattr(core, "picture", picture, raising=False)
    monkeypatch.setitem(sys.modules, "core.picture", picture)
    matches = []

    def match(context, name, threshold=0.8, rgb_diff=20):
        matches.append((name, threshold, rgb_diff))
        return context.frame == "login"

    monkeypatch.setattr(image, "compare_image", match)
    monkeypatch.setattr(color, "match_rgb_feature", lambda context, name: context.frame == "home" and name == "main_page")
    tasks = {}
    namespace = dict(func_dict=tasks, FunctionCallTimeout=FunctionCallTimeout, PackageIncorrect=PackageIncorrect, traceback=traceback)

    class Baas:
        def __init__(self):
            self.identifier = "CN"
            self.is_android_device = True
            self.flag_run = True
            self.frame = "login"
            self.calls = []
            self.popups = []
            self.logs = []
            self.errors = []
            self.home_calls = 0
            self.timeout_calls = 0
            self.package_calls = 0
            self.on_home = None
            self.on_screenshot = None
            self.logger = SimpleNamespace(info=self.logs.append, warning=self.logs.append, error=self.logs.append)

        def update_screenshot_array(self):
            if self.on_screenshot:
                self.on_screenshot(self)
            return "screenshot-result"

        def to_main_page(self):
            self.home_calls += 1
            if self.on_home:
                return self.on_home(self)
            # Nested popup processing during home navigation must not recurse.
            picture.deal_with_pop_ups(self)
            self.frame = "home"
            self.update_screenshot_array()

        def deal_with_func_call_timeout(self):
            self.timeout_calls += 1
            return False

        def deal_with_package_incorrect(self, package):
            self.package_calls += 1
            return False

        def push_and_log_error_msg(self, title, message):
            self.errors.append((title, message))

    Baas.solve = _load_core_function(root / "core/Baas_thread.py", "solve", namespace)
    monkeypatch.setitem(sys.modules, "core.Baas_thread", SimpleNamespace(Baas_thread=Baas))
    login_compat.install_login_compat()
    wrapped = Baas.solve
    login_compat.install_login_compat()
    assert Baas.solve is wrapped

    def arena(context):
        context.calls.append("arena-entry")
        picture.deal_with_pop_ups(context)
        return True

    tasks["arena"] = arena
    return SimpleNamespace(Baas=Baas, picture=picture, tasks=tasks, clock=clock, matches=matches, root=root, time=time)


def test_login_recovers_once_and_retries_actual_task_entry(runtime):
    context = runtime.Baas()
    assert context.solve("arena") is True
    assert context.calls == ["arena-entry", "arena-entry"]
    assert context.home_calls == 1 and context.timeout_calls == 0
    assert context.errors == []
    assert runtime.matches[0] == ("main_page_login-feature", 0.9, 12)
    assert not hasattr(context, login_compat._STATE_ATTRIBUTE)
    # A different scheduled solve receives a new, independent recovery budget.
    context.frame = "login"
    assert context.solve("arena") is True
    assert context.home_calls == 2


def test_repeated_login_in_same_task_fails_without_second_recovery(runtime):
    context = runtime.Baas()

    def arena(context):
        context.calls.append("arena-entry")
        context.frame = "login"
        runtime.picture.deal_with_pop_ups(context)

    runtime.tasks["arena"] = arena
    assert context.solve("arena") is False
    assert context.home_calls == 1 and context.timeout_calls == 0
    assert len(context.calls) == 2
    assert "limited to one attempt" in context.errors[0][1]
    assert not hasattr(context, login_compat._STATE_ATTRIBUTE)


@pytest.mark.parametrize("during_screenshot", [False, True])
def test_recovery_timeout_checked_before_and_after_screenshot(runtime, during_screenshot):
    context = runtime.Baas()

    def home(context):
        if during_screenshot:
            context.on_screenshot = lambda _: setattr(runtime.clock, "now", 191)
        else:
            runtime.clock.now = 191
        context.update_screenshot_array()

    context.on_home = home
    assert context.solve("arena") is False
    assert "within 90 seconds" in context.errors[0][1]
    assert context.timeout_calls == 0 and len(context.calls) == 1
    assert not hasattr(context, login_compat._STATE_ATTRIBUTE)


def test_user_stop_during_login_is_not_retried_or_reported_as_timeout(runtime):
    context = runtime.Baas()

    def home(context):
        context.flag_run = False
        context.update_screenshot_array()

    context.on_home = home
    # Existing solve() treats human takeover as a normal, stopped task return.
    assert context.solve("arena") is True
    assert context.flag_run is False and len(context.calls) == 1
    assert context.errors == [] and context.timeout_calls == 0
    assert not hasattr(context, login_compat._STATE_ATTRIBUTE)


@pytest.mark.parametrize("identifier,android", [("JP", True), ("Global_zh-tw", True), ("CN", False)])
def test_unrelated_regions_and_non_android_keep_original_path(runtime, identifier, android):
    context = runtime.Baas()
    context.identifier, context.is_android_device = identifier, android
    assert context.solve("arena") is True
    assert context.home_calls == 0 and context.calls == ["arena-entry"]
    assert runtime.matches == []


def test_stage_which_handles_login_itself_is_not_intercepted(runtime):
    context = runtime.Baas()
    namespace = dict(
        time=runtime.time,
        color=SimpleNamespace(wait_loading=lambda context: None, match_rgb_feature=color.match_rgb_feature),
        match_rgb_feature=color.match_rgb_feature,
        match_img_feature=lambda context, name, *args: name == "main_page_login-feature" and context.frame == "login",
        deal_with_pop_ups=lambda *args, **kwargs: runtime.picture.deal_with_pop_ups(*args, **kwargs),
        FunctionCallTimeout=FunctionCallTimeout,
        RequestHumanTakeOver=RequestHumanTakeOver,
        PackageIncorrect=PackageIncorrect,
    )
    co_detect = _load_core_function(runtime.root / "core/picture.py", "co_detect", namespace)
    context.click = lambda *args: setattr(context, "frame", "home")

    def handles_login(context):
        return co_detect(context, rgb_ends="main_page", img_reactions={"main_page_login-feature": (640, 360)})

    runtime.tasks["login"] = handles_login
    assert context.solve("login") == "main_page"
    assert context.home_calls == 0 and runtime.matches == []


def test_ordinary_timeout_preserves_existing_handler(runtime):
    context = runtime.Baas()
    runtime.tasks["timeout"] = lambda context: (_ for _ in ()).throw(FunctionCallTimeout("ordinary"))
    assert context.solve("timeout") is False
    assert context.timeout_calls == 1 and context.home_calls == 0


@pytest.mark.parametrize("failure", ["not-home", "navigation-timeout", "package-incorrect"])
def test_failed_recovery_is_explicit_and_does_not_restart_game(runtime, failure):
    context = runtime.Baas()

    def home(context):
        if failure == "navigation-timeout":
            raise FunctionCallTimeout("nested navigation")
        if failure == "package-incorrect":
            raise PackageIncorrect("different.package")

    context.on_home = home
    assert context.solve("arena") is False
    assert "Login session recovery failed" in context.errors[0][1]
    assert context.timeout_calls == 0 and len(context.calls) == 1
    assert context.package_calls == 0


def test_ordinary_package_incorrect_preserves_existing_handler(runtime):
    context = runtime.Baas()
    runtime.tasks["package"] = lambda context: (_ for _ in ()).throw(PackageIncorrect("different.package"))
    assert context.solve("package") is False
    assert context.package_calls == 1 and context.home_calls == 0


def _real_image_match(runtime, monkeypatch):
    import cv2

    template = cv2.imread(str(runtime.root / "src/images/CN/main_page/login-feature.png"))
    monkeypatch.setattr(position, "image_dic", {"CN": {"main_page_login-feature": template}})
    monkeypatch.setattr(position, "get_area", lambda *args: (1105, 601, 1142, 640))
    compare = _load_core_function(runtime.root / "core/image.py", "compare_image", dict(
        position=position, screenshot_cut=image.screenshot_cut, compare_image_rgb=image.compare_image_rgb, cv2=cv2,
    ))
    monkeypatch.setattr(image, "compare_image", compare)
    return template


def test_real_co_detect_frame_sequence_unwinds_to_task_entry(runtime, monkeypatch):
    import numpy as np

    template = _real_image_match(runtime, monkeypatch)
    title = np.zeros((720, 1280, 3), dtype=np.uint8)
    title[601:640, 1105:1142] = template
    context = runtime.Baas()
    context.ratio = 1
    context.latest_img_array = title
    context.connection = SimpleNamespace(get_current_package=lambda: "game")
    context.package_name = "game"
    namespace = dict(
        time=runtime.time, color=SimpleNamespace(wait_loading=lambda context: None, match_rgb_feature=color.match_rgb_feature),
        match_rgb_feature=color.match_rgb_feature,
        match_img_feature=lambda *args: False,
        deal_with_pop_ups=lambda *args, **kwargs: runtime.picture.deal_with_pop_ups(*args, **kwargs),
        FunctionCallTimeout=FunctionCallTimeout, RequestHumanTakeOver=RequestHumanTakeOver, PackageIncorrect=PackageIncorrect,
    )
    co_detect = _load_core_function(runtime.root / "core/picture.py", "co_detect", namespace)

    def screenshot(context):
        context.latest_img_array = title if context.frame == "login" else np.zeros_like(title)

    context.on_screenshot = screenshot

    def task(context):
        context.calls.append("task-entry")
        return co_detect(context, rgb_ends="main_page")

    runtime.tasks["arena"] = task
    assert context.solve("arena") == "main_page"
    assert context.calls == ["task-entry", "task-entry"]
    assert context.home_calls == 1 and context.timeout_calls == 0
    assert context.errors == []


@pytest.mark.skipif(not os.getenv("BAAS_LOGIN_FRAME_DIR"), reason="requires local captured game frames")
def test_real_captured_login_frames_and_negative_screens(runtime, monkeypatch):
    import cv2

    _real_image_match(runtime, monkeypatch)
    context = runtime.Baas()
    context.ratio = 1
    frames = Path(os.environ["BAAS_LOGIN_FRAME_DIR"])
    for name, expected in [
        ("1792208381539.png", True), ("1792208429226.png", True),
        ("1792208357270.png", False), ("1792208345223.png", False),
    ]:
        context.latest_img_array = cv2.imread(str(frames / name))
        assert context.latest_img_array is not None, name
        assert bool(image.compare_image(context, "main_page_login-feature", threshold=0.9, rgb_diff=12)) is expected, name
