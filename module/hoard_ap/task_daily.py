"""每日任务体力：只领「每日」tab，避开周常 150 坑。

背景：
- 原 collect_daily_power / collect_reward 进任务页后直接点右下角一键领取，
  若当前停在「周常」且周二有 150 体，会误领。
- 本模块：
  1) collect_daily_except_weekly：若已校准「每日」tab 坐标，先点每日再领；
     未校准则拒绝自动领，只 notify。
  2) calibrate_daily_tab_at(x,y)：用户在任务页点一次「每日」位置后写入 state。
  3) 默认推荐坐标（1280x720 国服经验值，可被校准覆盖）。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, List, Optional, Tuple


# 国服 1280x720 基准；运行时按实际分辨率缩放
_BASE_W, _BASE_H = 1280, 720
DEFAULT_DAILY_TAB_XY = (302, 92)  # 任务页「每日」tab 中心（1280x720）
DEFAULT_CLAIM_ALL_XY = (1145, 670)


def _screen_wh(self) -> Tuple[int, int]:
    for attr in ("ratio", "screenshot_size", "resolution"):
        try:
            v = getattr(self, attr, None)
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                return int(v[0]), int(v[1])
        except Exception:
            pass
    try:
        img = getattr(self, "latest_img_array", None)
        if img is not None and hasattr(img, "shape"):
            h, w = int(img.shape[0]), int(img.shape[1])
            if w > 0 and h > 0:
                return w, h
    except Exception:
        pass
    try:
        u2 = getattr(self, "u2", None)
        if u2 is not None and hasattr(u2, "window_size"):
            w, h = u2.window_size()
            return int(w), int(h)
    except Exception:
        pass
    return _BASE_W, _BASE_H


def scale_xy(self, x: int, y: int) -> Tuple[int, int]:
    """把 1280x720 基准坐标缩到当前分辨率。"""
    w, h = _screen_wh(self)
    nx = int(round(int(x) * w / float(_BASE_W)))
    ny = int(round(int(y) * h / float(_BASE_H)))
    return nx, ny


def default_daily_tab_xy(self) -> Tuple[int, int]:
    return scale_xy(self, DEFAULT_DAILY_TAB_XY[0], DEFAULT_DAILY_TAB_XY[1])


def default_claim_all_xy(self) -> Tuple[int, int]:
    return scale_xy(self, DEFAULT_CLAIM_ALL_XY[0], DEFAULT_CLAIM_ALL_XY[1])


def _config_dir_of(self) -> str:
    return getattr(self, "config_path", None) or getattr(
        getattr(self, "config_set", None), "config_dir", "."
    ) or "."


def load_daily_tab_xy(config_dir: str) -> Optional[Tuple[int, int]]:
    try:
        from module.hoard_ap.state import load_state

        st = load_state(config_dir)
        if st.task_daily_tab_xy and len(st.task_daily_tab_xy) >= 2:
            return int(st.task_daily_tab_xy[0]), int(st.task_daily_tab_xy[1])
    except Exception:
        pass
    # 独立小文件，方便 UI 只写坐标
    path = os.path.join(config_dir, "hoard_ap_task_daily_tab.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return int(data["x"]), int(data["y"])
        except Exception:
            pass
    return None


def save_daily_tab_xy(config_dir: str, x: int, y: int) -> None:
    path = os.path.join(config_dir, "hoard_ap_task_daily_tab.json")
    os.makedirs(config_dir or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"x": int(x), "y": int(y)}, f, ensure_ascii=False, indent=2)
    try:
        from module.hoard_ap.state import load_state, save_state

        st = load_state(config_dir)
        st.task_daily_tab_xy = [int(x), int(y)]
        save_state(config_dir, st)
    except Exception:
        pass


def calibrate_daily_tab_at(self, x: int, y: int) -> bool:
    """记录用户点的「每日」tab 坐标。"""
    cfg = _config_dir_of(self)
    save_daily_tab_xy(cfg, x, y)
    try:
        self.logger.info("[囤体] 已记录每日 tab 坐标 (%s,%s)" % (x, y))
    except Exception:
        pass
    return True


def _click_daily_tab(self, xy: Tuple[int, int]) -> None:
    x, y = xy
    self.click(int(x), int(y), duration=0.4, wait_over=True)
    time.sleep(0.35)


def collect_daily_except_weekly(self, allow_default_xy: bool = True) -> bool:
    """先点每日 tab，再一键领取。未校准且不允许默认坐标 → 只提醒不领。"""
    cfg = _config_dir_of(self)
    xy = load_daily_tab_xy(cfg)
    if xy is None:
        if allow_default_xy:
            xy = default_daily_tab_xy(self)
            try:
                self.logger.info(
                    "[囤体] 每日 tab 使用分辨率自适应坐标 %s（基准 1280x720→当前屏）"
                    % (xy,)
                )
            except Exception:
                pass
        else:
            try:
                from core.notification import notify

                notify(
                    title="囤体：请先校准每日 tab",
                    body="打开任务页，在囤体设置里点「记录每日位置」，避免误领周常。",
                )
            except Exception:
                pass
            try:
                self.logger.info("[囤体] 拒绝自动领任务体：未校准每日 tab")
            except Exception:
                pass
            return False

    try:
        from module.collect_daily_task_power import to_tasks
    except Exception:
        try:
            from module.collect_reward import to_tasks  # type: ignore
        except Exception:
            to_tasks = None

    try:
        self.to_main_page()
    except Exception:
        pass

    if to_tasks is not None:
        try:
            to_tasks(self, True)
        except Exception:
            try:
                to_tasks(self)
            except Exception as _te:
                try:
                    self.logger.warning(f"[囤体] 打开任务页失败，按已存坐标尝试: {_te}")
                except Exception:
                    pass
    time.sleep(0.5)
    _click_daily_tab(self, xy)
    time.sleep(0.4)

    # 复用原一键领取逻辑（颜色判断）
    try:
        from core import color

        self.latest_img_array = self.get_screenshot_array()
        # 右下角一键
        if color.rgb_in_range(self, 1148, 691, 239, 255, 228, 248, 64, 84) and color.rgb_in_range(
            self, 1142, 649, 239, 255, 228, 248, 64, 84
        ):
            self.logger.info("[囤体] 每日 tab 下一键领取")
            self.click(*default_claim_all_xy(self), duration=0.4, wait_over=True)
            self.click(254, 72, wait_over=True)
            self.click(254, 72, wait_over=True)
            return True
        # 非高亮：当作未领成功，绝不返回 True（避免误勾已领）
        self.logger.info("[囤体] 每日领取按钮非高亮，视为未领成功")
        return False
    except Exception as e:
        try:
            self.logger.error("[囤体] collect_daily_except_weekly 失败: %s" % e)
        except Exception:
            pass
        return False


def implement_collect_daily_except_weekly(self) -> bool:
    """可供 func_dict 注册的入口。"""
    return collect_daily_except_weekly(self, allow_default_xy=True)
