from __future__ import annotations

import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from service import asset_compat


@pytest.fixture
def baas_type(monkeypatch):
    class Baas:
        def get_creditpoints(self, is_main_page=False):
            self.original_calls.append(is_main_page)
            return "original"

        def get_ap(self, is_main_page=False):
            self.original_calls.append(is_main_page)
            return "original-ap"

    monkeypatch.setitem(sys.modules, "core.Baas_thread", SimpleNamespace(Baas_thread=Baas))
    asset_compat.install_asset_compat()
    wrapped = Baas.get_creditpoints
    wrapped_ap = Baas.get_ap
    asset_compat.install_asset_compat()
    assert Baas.get_creditpoints is wrapped
    assert Baas.get_ap is wrapped_ap
    return Baas


def _context(baas_type, text="987,654,321", server="CN"):
    context = baas_type()
    context.server = server
    context.original_calls = []
    context.ocr_calls = []
    context.saved = []
    context.warnings = []
    context.logger = SimpleNamespace(warning=lambda message: context.warnings.append(message))

    def recognize(*args):
        context.ocr_calls.append(args)
        return text

    context.ocr = SimpleNamespace(get_region_res=recognize)
    context.config_set = SimpleNamespace(set=lambda *args: context.saved.append(args))
    return context


@pytest.mark.parametrize("text,expected", [
    ("987,654,321", 987654321), (" 987,654,321 ", 987654321), ("0", 0), ("", 0),
])
def test_cn_secondary_credit_region_preserves_digit_parsing_and_persistence(
    baas_type, monkeypatch, text, expected,
):
    monkeypatch.setattr(asset_compat, "time", SimpleNamespace(time=lambda: 1234.5))
    context = _context(baas_type, text=text)
    assert context.get_creditpoints(False) == expected
    assert context.original_calls == []
    assert context.ocr_calls == [
        (context, (741, 10, 908, 40), "en-us", "Credit Points", "0123456789,", 0.2),
    ]
    assert context.saved == [("creditpoints", {"count": expected, "time": 1234.5})]


@pytest.mark.parametrize("server,home", [
    ("Global", False), ("JP", False), ("Global", True), ("JP", True),
])
def test_other_servers_keep_original_credit_method(baas_type, server, home):
    context = _context(baas_type, server=server)
    assert context.get_creditpoints(home) == "original"
    assert context.original_calls == [home]
    assert context.ocr_calls == [] and context.saved == []


def test_cn_home_credit_crop_preserves_leading_digits(baas_type):
    context = _context(baas_type)
    assert context.get_creditpoints(True) == 987654321
    assert context.ocr_calls == [
        (context, (671, 20, 832, 52), "en-us", "Credit Points", "0123456789,", 0.2),
    ]


@pytest.mark.parametrize("home,region", [
    (True, (484, 25, 609, 52)), (False, (530, 10, 662, 40)),
])
@pytest.mark.parametrize("text,count,maximum", [
    ("999/240", 999, 240), ("9/240", 9, 240), ("0/240", 0, 240),
    (" 123/240 ", 123, 240),
])
def test_cn_ap_regions_keep_parsing_and_config_persistence(
    baas_type, monkeypatch, home, region, text, count, maximum,
):
    monkeypatch.setattr(asset_compat, "time", SimpleNamespace(time=lambda: 1234.5))
    context = _context(baas_type, text=text)
    assert context.get_ap(home) == count
    assert context.original_calls == []
    assert context.ocr_calls == [(context, region, "en-us", "AP", "0123456789/")]
    assert context.saved == [("ap", {"count": count, "max": maximum, "time": 1234.5})]


@pytest.mark.parametrize("text", ["", "bad", "999/", "1000/240", "123/1000", "51", "123/0", "-1/240"])
def test_invalid_ap_keeps_original_warning_and_fallback(baas_type, text):
    context = _context(baas_type, text=text)
    assert context.get_ap() == 999
    assert context.saved == []
    assert context.warnings == ["Failed to get AP."]


def test_incomplete_transition_read_retries_fresh_frame_without_caching_bare_number(baas_type, monkeypatch):
    context = _context(baas_type)
    values = iter(["51", "899/240"])
    context.ocr.get_region_res = lambda *args: next(values)
    frames, sleeps = [], []
    context.update_screenshot_array = lambda: frames.append("fresh")
    monkeypatch.setattr(asset_compat.time, "sleep", lambda seconds: sleeps.append(seconds))
    assert context.get_ap(True) == 899
    assert frames == ["fresh"] and sleeps == [0.15]
    assert [(key, value["count"], value["max"]) for key, value in context.saved] == [("ap", 899, 240)]
    assert context.warnings == []


def test_invalid_ap_retries_are_bounded_and_keep_existing_asset_cache(baas_type, monkeypatch):
    context = _context(baas_type, text="51")
    frames = []
    context.update_screenshot_array = lambda: frames.append("fresh")
    monkeypatch.setattr(asset_compat.time, "sleep", lambda seconds: None)
    assert context.get_ap(True) == 999
    assert frames == ["fresh", "fresh"]
    assert len(context.ocr_calls) == 3
    assert context.saved == []
    assert context.warnings == ["Failed to get AP."]


def test_ap_refresh_cancellation_propagates_without_writing_asset(baas_type, monkeypatch):
    context = _context(baas_type, text="51")
    monkeypatch.setattr(asset_compat.time, "sleep", lambda seconds: None)

    def cancelled():
        raise RuntimeError("task cancelled")

    context.update_screenshot_array = cancelled
    with pytest.raises(RuntimeError, match="task cancelled"):
        context.get_ap(True)
    assert context.saved == []


@pytest.mark.parametrize("server", ["Global", "JP"])
@pytest.mark.parametrize("home", [True, False])
def test_other_servers_keep_original_ap_method(baas_type, server, home):
    context = _context(baas_type, server=server)
    assert context.get_ap(home) == "original-ap"
    assert context.original_calls == [home]
    assert context.ocr_calls == [] and context.saved == []


def test_concurrent_configs_keep_shared_ocr_method_and_original_contexts(baas_type):
    contexts = [_context(baas_type), _context(baas_type)]
    barrier = threading.Barrier(2)

    def recognize(context, region, *args):
        assert region == (741, 10, 908, 40)
        barrier.wait(timeout=2)
        return "987,654,321" if context is contexts[0] else "123,456,789"

    shared_ocr = SimpleNamespace(get_region_res=recognize)
    for context in contexts:
        context.ocr = shared_ocr
    with ThreadPoolExecutor(max_workers=2) as pool:
        counts = list(pool.map(lambda context: context.get_creditpoints(), contexts))
    assert counts == [987654321, 123456789]
    assert contexts[0].ocr is shared_ocr and contexts[1].ocr is shared_ocr
    assert vars(shared_ocr) == {"get_region_res": recognize}
    assert [context.saved[0][1]["count"] for context in contexts] == counts


def test_concurrent_ap_layouts_keep_shared_ocr_and_individual_counts(baas_type):
    contexts = [_context(baas_type), _context(baas_type)]
    barrier = threading.Barrier(2)

    def recognize(context, region, *args):
        expected = (484, 25, 609, 52) if context is contexts[0] else (530, 10, 662, 40)
        assert region == expected
        barrier.wait(timeout=2)
        return "999/240" if context is contexts[0] else "9/240"

    shared_ocr = SimpleNamespace(get_region_res=recognize)
    for context in contexts:
        context.ocr = shared_ocr
    with ThreadPoolExecutor(max_workers=2) as pool:
        counts = list(pool.map(lambda item: item[0].get_ap(item[1]), zip(contexts, (True, False))))
    assert counts == [999, 9]
    assert vars(shared_ocr) == {"get_region_res": recognize}
    assert [context.saved[0][1]["count"] for context in contexts] == counts


def test_ap_ocr_failure_propagates_without_overwriting_saved_asset(baas_type):
    context = _context(baas_type)

    def recognize(*args):
        raise ConnectionError("OCR unavailable")

    context.ocr.get_region_res = recognize
    with pytest.raises(ConnectionError, match="OCR unavailable"):
        context.get_ap(True)
    assert context.saved == []


def test_ocr_failure_propagates_without_overwriting_saved_credit(baas_type):
    context = _context(baas_type)

    def recognize(*args):
        raise ConnectionError("OCR unavailable")

    context.ocr.get_region_res = recognize
    with pytest.raises(ConnectionError, match="OCR unavailable"):
        context.get_creditpoints()
    assert context.saved == []
