from __future__ import annotations

import time
from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from module import cafe_reward


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cafe_reward_match_maps_scaled_roi_coordinates(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    cafe_reward._happy_face_templates = None

    template_path = REPO_ROOT / "src" / "images" / "CN" / "cafe" / "happy_face1.png"
    template = cv2.imread(str(template_path))
    assert template is not None

    image = np.full((720, 1280, 3), 40, dtype=np.uint8)
    x, y = 300, 200
    height, width = template.shape[:2]
    image[y:y + height, x:x + width] = template

    matches = cafe_reward.match(image)

    expected_x = x + width / 2
    expected_y = y + height / 2 + 58
    assert any(abs(mx - expected_x) <= 4 and abs(my - expected_y) <= 4 for mx, my in matches)


def test_cafe_reward_match_is_bounded_on_broad_matches(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    cafe_reward._happy_face_templates = None

    image = np.full((720, 1280, 3), 255, dtype=np.uint8)
    start = time.perf_counter()
    matches = cafe_reward.match(image)
    elapsed = time.perf_counter() - start

    assert elapsed < 3
    assert len(matches) <= 64


def test_cafe_reward_match_android_skips_template_fallback(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("BAAS_ANDROID", "1")
    cafe_reward._happy_face_templates = None

    image = np.full((720, 1280, 3), 255, dtype=np.uint8)
    start = time.perf_counter()
    matches = cafe_reward.match(image)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.2
    assert matches == []
    assert cafe_reward._happy_face_templates is None


def test_android_gift_to_cafe_avoids_slow_detection(monkeypatch):
    calls = []

    class FakeBaas:
        is_android_device = True

        def click(self, *args, **kwargs):
            calls.append(("click", args, kwargs))

    def fail_detect(*_args, **_kwargs):
        raise AssertionError("Android gift_to_cafe should not use co_detect")

    monkeypatch.setattr(cafe_reward.picture, "co_detect", fail_detect)
    monkeypatch.setattr(cafe_reward.time, "sleep", lambda _seconds: None)

    cafe_reward.gift_to_cafe(FakeBaas())

    assert calls == [("click", (1240, 574), {"wait_over": True})]
