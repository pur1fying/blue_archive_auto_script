"""配置页按钮 → 运行中 Baas_thread 的桥。

识别邮箱 / 点选校准每日 tab：必须脚本在跑且已连上模拟器。
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional, Tuple


def get_baas_thread(config) -> Any:
    """从 ConfigSet 取正在跑的 baas 线程。"""
    try:
        mt = None
        if hasattr(config, "get_main_thread"):
            mt = config.get_main_thread()
        if mt is None and hasattr(config, "main_thread"):
            mt = config.main_thread
        if mt is None:
            return None
        if hasattr(mt, "get_baas_thread"):
            return mt.get_baas_thread()
        return getattr(mt, "baas_thread", None) or getattr(mt, "baas", None)
    except Exception:
        return None


def require_running_baas(config) -> Tuple[Any, str]:
    """要完整调度在跑（清体等）。"""
    baas = get_baas_thread(config)
    if baas is None:
        return None, "脚本没在跑或还没连上模拟器。请先在首页点开始，再点这个按钮。"
    running = getattr(baas, "flag_run", None)
    if running is False:
        return None, "脚本已停止。请先开始运行，再点这个按钮。"
    return baas, ""


def require_baas_for_ocr(config) -> Tuple[Any, str]:
    """识别邮箱专用：优先用已在跑的线程；否则尝试只连设备做一次 OCR，不跑囤体其它步骤。

    用户明确要求：不要为了识别去「启动整套囤体」从而误触发清体。
    """
    baas = get_baas_thread(config)
    if baas is not None:
        # 即使 flag_run 为 False，只要对象还在且能截图，也允许识别
        return baas, ""
    # 尝试从 ConfigSet 拉起 / 取静态连接（不启动 hoard 计划）
    try:
        mt = None
        if hasattr(config, "get_main_thread"):
            mt = config.get_main_thread()
        if mt is None:
            mt = getattr(config, "main_thread", None)
        if mt is not None:
            for attr in ("baas_thread", "baas", "thread"):
                b = getattr(mt, attr, None)
                if b is not None:
                    return b, ""
            if hasattr(mt, "get_baas_thread"):
                b = mt.get_baas_thread()
                if b is not None:
                    return b, ""
    except Exception:
        pass
    return (
        None,
        "还没连上模拟器。请先在首页点一次「开始」连上设备（连上后可立刻停），"
        "再点识别邮箱——识别不会自动跑清体。",
    )


def _read_pos(baas) -> Optional[Tuple[int, int]]:
    """尽量从 baas / control / u2 读到最近一次点击。"""
    for obj_name in (None, "control", "u2", "connection"):
        obj = baas if obj_name is None else getattr(baas, obj_name, None)
        if obj is None:
            continue
        for attr in (
            "last_click_position",
            "last_click_pos",
            "last_touch_position",
            "last_pos",
        ):
            p = getattr(obj, attr, None)
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                try:
                    return int(p[0]), int(p[1])
                except Exception:
                    pass
    return None


def _hook_click_tracker(baas) -> Tuple[Any, Any]:
    """临时包一层 click，记录坐标。返回 (restore_fn, box_dict)。"""
    box = {"pos": None, "n": 0}
    originals = []

    def _wrap(obj, name):
        if obj is None or not hasattr(obj, name):
            return
        orig = getattr(obj, name)
        if not callable(orig):
            return

        def hooked(x, y, *a, **k):
            try:
                box["pos"] = (int(x), int(y))
                box["n"] = int(box["n"]) + 1
                try:
                    baas.last_click_position = (int(x), int(y))
                except Exception:
                    pass
            except Exception:
                pass
            return orig(x, y, *a, **k)

        try:
            setattr(obj, name, hooked)
            originals.append((obj, name, orig))
        except Exception:
            pass

    _wrap(baas, "click")
    ctrl = getattr(baas, "control", None)
    _wrap(ctrl, "click")
    if ctrl is not None:
        inst = getattr(ctrl, "control_instance", None)
        _wrap(inst, "click")
    u2 = getattr(baas, "u2", None)
    _wrap(u2, "click")

    def restore():
        for obj, name, orig in originals:
            try:
                setattr(obj, name, orig)
            except Exception:
                pass

    return restore, box


def capture_next_click(
    baas,
    *,
    timeout_s: float = 45.0,
    poll_s: float = 0.2,
    on_status: Optional[Callable[[str], None]] = None,
) -> Optional[Tuple[int, int]]:
    """等一次有效点击坐标。

    优先：临时 hook baas.click / control.click（脚本自己点也会记）。
    其次：轮询 last_click_position。
    再：u2 无原生监听时，提示用户改用「任务页打开后点 BAAS 日志里的坐标」——
    并尝试读 scrcpy/u2 的 touch。
    """
    if on_status:
        on_status(
            "请在 %d 秒内点游戏里的「每日」页签（脚本需在跑；点完等提示）"
            % int(timeout_s)
        )

    restore, box = _hook_click_tracker(baas)
    start = _read_pos(baas)
    start_n = int(box.get("n") or 0)
    t0 = time.time()
    try:
        # 若有 u2 watcher
        try:
            u2 = getattr(baas, "u2", None)
            if u2 is not None and hasattr(u2, "click"):
                pass
        except Exception:
            pass

        while time.time() - t0 < timeout_s:
            time.sleep(poll_s)
            # hook 到了
            if int(box.get("n") or 0) > start_n and box.get("pos"):
                pos = box["pos"]
                if on_status:
                    on_status("已记录点击 (%d,%d)" % (pos[0], pos[1]))
                return int(pos[0]), int(pos[1])
            cur = _read_pos(baas)
            if cur is None:
                continue
            if start is None or cur != start:
                time.sleep(0.12)
                cur2 = _read_pos(baas)
                if cur2 == cur:
                    if on_status:
                        on_status("已记录点击 (%d,%d)" % (cur[0], cur[1]))
                    return cur
        if on_status:
            on_status(
                "超时：没检测到点击。可手动在「每日位置」填 x,y（任务页顶栏「每日」中心）"
            )
        return None
    finally:
        try:
            restore()
        except Exception:
            pass


def run_mail_ocr_on_baas(baas, config_dir: str) -> dict:
    from module.hoard_ap.mail_ocr import scan_mail_ap, apply_scan_to_inventory

    scan = scan_mail_ap(baas)
    if scan.get("ok"):
        apply_scan_to_inventory(config_dir, scan)
    return scan
