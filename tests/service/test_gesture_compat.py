from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from service import gesture_compat


class Clock:
    def __init__(self):
        self.now = 20.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        assert seconds > 0
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def setup(monkeypatch):
    clock, original_calls, curve_calls, events = Clock(), [], [], []

    class NemuControl:
        def swipe(self, *args):
            original_calls.append(args)
            return "original"

    def insert_swipe(**kwargs):
        curve_calls.append(kwargs)
        return [(10, 20), (15, 30), (20, 40)]

    module = SimpleNamespace(NemuControl=NemuControl, insert_swipe=insert_swipe)
    monkeypatch.setitem(sys.modules, "core.device.control.nemu", module)
    monkeypatch.setattr(gesture_compat, "time", clock)
    gesture_compat.install_gesture_compat()
    installed = NemuControl.swipe
    gesture_compat.install_gesture_compat()
    assert NemuControl.swipe is installed
    control = NemuControl()
    control.nemu_client = SimpleNamespace(
        down=lambda *point: events.append(("down", point, clock.now)),
        up=lambda: events.append(("up", clock.now)),
    )
    return SimpleNamespace(
        control=control, clock=clock, events=events, curves=curve_calls, original=original_calls,
    )


@pytest.mark.parametrize("duration", [0.05, 0.3, 1.0])
def test_explicit_duration_preserves_curve_coordinates_and_one_release(setup, duration):
    setup.control.swipe(10, 20, 20, 40, duration)
    assert setup.original == []
    assert setup.curves == [{"p0": (10, 20), "p3": (20, 40)}]
    assert [event[1] for event in setup.events[:-1]] == [(10, 20), (15, 30), (20, 40)]
    assert [event[2] - 20 for event in setup.events[:-1]] == pytest.approx(
        [0, duration / 2, duration]
    )
    assert setup.events[-1] == ("up", pytest.approx(20 + duration))
    assert setup.clock.now == pytest.approx(20 + duration + 0.05)


def test_none_duration_delegates_to_original_without_new_touch_events(setup):
    assert setup.control.swipe(10, 20, 20, 40, None) == "original"
    assert setup.original == [(10, 20, 20, 40, None)]
    assert setup.curves == [] and setup.events == [] and setup.clock.sleeps == []


def test_client_overhead_does_not_accumulate_into_requested_intervals(setup):
    def down(*point):
        setup.events.append(("down", point, setup.clock.now))
        setup.clock.now += 0.02

    setup.control.nemu_client.down = down
    setup.control.swipe(10, 20, 20, 40, 0.3)
    assert [event[2] - 20 for event in setup.events[:-1]] == pytest.approx([0, 0.15, 0.3])
    assert setup.events[-1] == ("up", pytest.approx(20.32))


def test_curve_rounding_does_not_omit_requested_final_coordinate(setup):
    setup.control.swipe(10, 20, 21, 41, 0.3)
    assert setup.curves == [{"p0": (10, 20), "p3": (21, 41)}]
    assert [event[1] for event in setup.events[:-1]] == [
        (10, 20), (15, 30), (20, 40), (21, 41),
    ]
    assert setup.events[-2][2] == pytest.approx(20.3)
    assert setup.events[-1][0] == "up"


def test_failed_touch_releases_once_and_propagates_error(setup):
    def down(*point):
        setup.events.append(("down", point, setup.clock.now))
        if len(setup.events) == 2:
            raise RuntimeError("touch RPC failed")

    setup.control.nemu_client.down = down
    with pytest.raises(RuntimeError, match="touch RPC failed"):
        setup.control.swipe(10, 20, 20, 40, 0.3)
    assert [event[0] for event in setup.events] == ["down", "down", "up"]


@pytest.mark.parametrize("duration", [-0.1, float("inf"), float("nan")])
def test_invalid_duration_fails_before_touching_device(setup, duration):
    with pytest.raises(ValueError, match="finite and non-negative"):
        setup.control.swipe(10, 20, 20, 40, duration)
    assert setup.events == [] and setup.curves == []


def test_zero_duration_still_finishes_at_target_and_releases_once(setup):
    setup.control.swipe(10, 20, 20, 40, 0)
    assert setup.events[-2] == ("down", (20, 40), 20)
    assert setup.events[-1] == ("up", 20)
    assert setup.clock.sleeps == [0.05]
