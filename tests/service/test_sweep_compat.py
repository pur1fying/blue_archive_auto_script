from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from core import image, position
from core.exception import RequestHumanTakeOver
from service import sweep_compat


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = cv2.imread(str(ROOT / "src/images/CN/normal_task/sweep-complete.png"))


def _result_frame(ratio=1):
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[561:604, 601:682] = (255, 214, 100)
    frame[562:603, 603:680] = cv2.resize(TEMPLATE, (77, 41), interpolation=cv2.INTER_AREA)
    for x, y, bgr in [(550, 123, (100, 240, 253)), (720, 123, (100, 240, 253)),
                      (1000, 95, (250, 250, 250)), (550, 580, (253, 214, 100)),
                      (725, 580, (253, 214, 100))]:
        frame[y-2:y+3, x-2:x+3] = bgr
    return cv2.resize(frame, (round(1280 * ratio), round(720 * ratio)), interpolation=cv2.INTER_AREA)


def _context(frame=None, ratio=1):
    return SimpleNamespace(latest_img_array=_result_frame(ratio) if frame is None else frame, ratio=ratio, identifier="CN")


def _match(context, threshold=0.8, rgb_diff=20):
    return sweep_compat._match_scrimmage_result(
        context, TEMPLATE, (601, 561, 682, 604), threshold, rgb_diff, image.compare_image_rgb,
    )


@pytest.mark.parametrize("ratio", [0.75, 1, 1.5, 2])
def test_scaled_result_label_preserves_template_threshold_and_screen_ratio(ratio):
    context = _context(ratio=ratio)
    assert _match(context)
    assert not _match(context, threshold=1)


@pytest.mark.parametrize("missing", [(550, 123), (720, 123), (1000, 95), (550, 580), (725, 580), "label"])
def test_result_requires_complete_header_and_button_evidence(missing):
    frame = _result_frame()
    if missing == "label":
        frame[550:615, 590:695] = (255, 214, 100)
    else:
        x, y = missing
        frame[y-2:y+3, x-2:x+3] = 0
    assert not _match(_context(frame))


@pytest.mark.parametrize("kind", ["dark-overlay", "different-title", "skip-label"])
def test_result_rejects_dark_overlay_wrong_header_and_skip_label(kind):
    frame = _result_frame()
    if kind == "dark-overlay":
        frame = (frame * 0.5).astype(np.uint8)
    elif kind == "different-title":
        frame[70:130, 530:750] = (250, 250, 250)
    else:
        other = cv2.imread(str(ROOT / "src/images/CN/normal_task/skip-sweep-complete.png"))
        frame[550:615, 590:695] = (255, 214, 100)
        frame[562:603, 603:680] = cv2.resize(other, (77, 41), interpolation=cv2.INTER_AREA)
    assert not _match(_context(frame))


@pytest.mark.parametrize("ratio", [0, -1, float("nan"), float("inf"), None, False])
def test_result_rejects_invalid_ratio(ratio):
    assert not _match(_context(_result_frame(), ratio=ratio))


def test_result_preserves_rgb_tolerance_and_local_bounds():
    frame = _result_frame()
    frame[561:604, 601:682] = np.clip(frame[561:604, 601:682].astype(np.int16) - 30, 0, 255)
    assert not _match(_context(frame))
    assert _match(_context(frame), rgb_diff=40)
    frame = _result_frame()
    frame[540:625, 580:705] = 0
    frame[562:603, 613:690] = cv2.resize(TEMPLATE, (77, 41), interpolation=cv2.INTER_AREA)
    assert not _match(_context(frame))


def test_patch_limits_scope_and_restores_context_after_error_or_cancel(monkeypatch):
    calls = []

    class Baas:
        def solve(self, activity):
            if activity == "raise":
                raise RuntimeError("cancelled")
            if activity == "cancel":
                raise RequestHumanTakeOver("user stopped")
            if activity == "nested":
                result = self.solve("scrimmage")
                assert getattr(self, sweep_compat._ACTIVE_ATTRIBUTE) is False
                return result
            return image.compare_image(self, self.feature, threshold=self.threshold)

    def original(context, name, threshold=0.8, rgb_diff=20):
        calls.append((name, threshold, rgb_diff))
        return name == "already-matched"

    monkeypatch.setitem(sys.modules, "core.Baas_thread", SimpleNamespace(Baas_thread=Baas))
    monkeypatch.setattr(image, "compare_image", original)
    monkeypatch.setattr(position, "image_dic", {"CN": {"normal_task_sweep-complete": TEMPLATE}})
    monkeypatch.setattr(position, "get_area", lambda *args: (601, 561, 682, 604))
    sweep_compat.install_scrimmage_sweep_compat()
    wrapped = Baas.solve
    sweep_compat.install_scrimmage_sweep_compat()
    assert Baas.solve is wrapped
    context = Baas()
    context.__dict__.update(vars(_context()))
    logs = []
    context.logger = SimpleNamespace(info=logs.append)
    context.feature, context.threshold = "normal_task_sweep-complete", 0.8
    assert context.solve("scrimmage")
    assert context.solve("nested")
    assert logs == ["Matched smaller CN scrimmage result label (0.95 scale)."] * 2
    assert not context.solve("arena")
    assert not hasattr(context, sweep_compat._ACTIVE_ATTRIBUTE)
    with pytest.raises(RequestHumanTakeOver, match="user stopped"):
        context.solve("cancel")
    assert not hasattr(context, sweep_compat._ACTIVE_ATTRIBUTE)
    context.threshold = 1
    assert not context.solve("scrimmage")
    context.threshold = 0.8
    context.feature = "normal_task_skip-sweep-complete"
    assert not context.solve("scrimmage")
    context.feature = "already-matched"
    assert context.solve("arena")
    for identifier in ("JP", "Global_zh-tw"):
        context.identifier = identifier
        context.feature = "normal_task_sweep-complete"
        assert not context.solve("scrimmage")
    with pytest.raises(RuntimeError, match="cancelled"):
        context.solve("raise")
    assert not hasattr(context, sweep_compat._ACTIVE_ATTRIBUTE)
    setattr(context, sweep_compat._ACTIVE_ATTRIBUTE, "previous")
    with pytest.raises(RuntimeError):
        context.solve("raise")
    assert getattr(context, sweep_compat._ACTIVE_ATTRIBUTE) == "previous"
    assert calls[0] == ("normal_task_sweep-complete", 0.8, 20)
    assert len(logs) == 2, "only successful scaled matches should log"


@pytest.mark.skipif(not os.getenv("BAAS_SWEEP_FRAME_DIR"), reason="requires local captured result frames")
def test_real_stalled_result_frames_and_unrelated_screen_negatives():
    frames = Path(os.environ["BAAS_SWEEP_FRAME_DIR"])
    for name, expected in [
        ("1792210314697.png", True), ("1792210308724.png", True),
        ("1792208381539.png", False), ("1792208357270.png", False),
        ("1792208345223.png", False),
    ]:
        frame = cv2.imread(str(frames / name))
        assert frame is not None, name
        if expected:
            original_score = float(cv2.matchTemplate(frame[561:604, 601:682], TEMPLATE, cv2.TM_CCOEFF_NORMED)[0, 0])
            assert 0.79 < original_score < 0.8, (name, original_score)
        assert bool(_match(_context(frame))) is expected, name
