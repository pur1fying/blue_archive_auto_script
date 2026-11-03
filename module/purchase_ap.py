"""青辉石买体力（管）。

硬约束：购买瞬间 ap + 120*tubes 必须 <= 999（买管永不进邮箱）。

实现策略（国服优先）：
1. 主页 OCR 当前 AP，检查 headroom
2. 点击主页体力条打开购买体力弹窗（与扫荡时弹出的 purchase_ap_notice 同源）
3. 按需连点「+」增加管数到目标
4. 确认购买，处理 full-notice / reward_acquired
5. 回到主页

若图像节点不足，降级为：记录日志 + 返回 False，由囤体执行器提醒用户。
坐标按 1280x720 逻辑分辨率，与项目其它模块一致。
"""

from __future__ import annotations

import time
from typing import Optional

from core import picture
from core.picture import GAME_ONE_TIME_POP_UPS

from module.hoard_ap.constants import AP_HARD_CAP, TUBE_AP


def tube_cost_pyroxene(tubes: int) -> int:
    tubes = int(tubes)
    cost = 0
    for i in range(1, tubes + 1):
        cost += 30 if i <= 3 else 60
    return cost


def implement(self, tubes: int = 3, skip_headroom_check: bool = False) -> bool:
    """购买 tubes 管体力。tubes 建议 1..6。"""
    tubes = int(tubes)
    if tubes <= 0:
        return True
    if tubes > 6:
        self.logger.warning("purchase_ap: tubes>6 not supported, clamp to 6")
        tubes = 6

    need = tubes * TUBE_AP
    cost = tube_cost_pyroxene(tubes)
    self.logger.info(f"purchase_ap: tubes={tubes}, +{need} AP, ~{cost} pyroxene")

    self.to_main_page()
    cur = _safe_get_ap(self)
    if cur is None:
        self.logger.warning("purchase_ap: failed to OCR AP, abort")
        return False

    if not skip_headroom_check and cur + need > AP_HARD_CAP:
        self.logger.warning(
            f"purchase_ap: headroom insufficient ap={cur} need={need} cap={AP_HARD_CAP}"
        )
        return False

    if not _open_purchase_ap_menu(self):
        self.logger.error("purchase_ap: cannot open purchase AP menu")
        return False

    if not _set_tube_count(self, tubes):
        self.logger.warning("purchase_ap: cannot confirm tube count UI; try buy once")
        # 仍尝试按一次购买（默认 1 管），循环 tubes 次
        ok = True
        for i in range(tubes):
            if not _confirm_buy_one(self):
                ok = False
                break
            # 每次买完可能要重新打开
            if i != tubes - 1:
                self.to_main_page()
                if _safe_get_ap(self) is not None:
                    if not _open_purchase_ap_menu(self):
                        ok = False
                        break
        _close_to_main(self)
        return ok

    if not _confirm_buy_one(self):
        self.logger.error("purchase_ap: confirm buy failed")
        _close_to_main(self)
        return False

    _close_to_main(self)
    after = _safe_get_ap(self)
    if after is not None:
        self.logger.info(f"purchase_ap: AP {cur} -> {after}")
    return True


# 兼容旧空壳
def start(self):
    tubes = int(getattr(self.config, "hoard_ap_tubes", 3) or 3)
    return implement(self, tubes=tubes)


def _safe_get_ap(self) -> Optional[int]:
    try:
        val = self.get_ap(True)
        return int(val)
    except Exception:
        return None


def _open_purchase_ap_menu(self) -> bool:
    """从主页点体力区域，期望出现 purchase_ap_notice。"""
    # 主页体力条中部（CN/Global 近似）
    ap_click = {
        "CN": (560, 40),
        "Global": (560, 40),
        "JP": (560, 40),
    }
    pos = ap_click.get(self.server, (560, 40))

    img_possibles = dict(GAME_ONE_TIME_POP_UPS.get(self.server, {}))
    rgb_possibles = {"main_page": pos}
    img_ends = [
        "purchase_ap_notice",
        "purchase_ap_notice-localized",
    ]
    try:
        res = picture.co_detect(
            self, None, rgb_possibles, img_ends, img_possibles, True
        )
        if res in ("purchase_ap_notice", "purchase_ap_notice-localized"):
            return True
    except Exception as e:
        self.logger.warning(f"purchase_ap open menu detect failed: {e}")

    # 再点一次体力
    try:
        self.click(pos[0], pos[1], duration=1, wait_over=True)
        time.sleep(0.8)
        self.latest_img_array = self.get_screenshot_array()
        res = picture.co_detect(self, None, None, img_ends, None, True)
        return res in ("purchase_ap_notice", "purchase_ap_notice-localized")
    except Exception:
        return False


def _set_tube_count(self, tubes: int) -> bool:
    """在购买弹窗内把数量加到 tubes。

    游戏 UI 通常默认 1 管，右侧有 + 按钮。坐标为经验值，失败返回 False。
    """
    if tubes <= 1:
        return True
    # 近似 + 按钮位置（弹窗中部偏右）
    plus_btn = (850, 400)
    for _ in range(tubes - 1):
        try:
            self.click(plus_btn[0], plus_btn[1], duration=0.3, wait_over=True)
            time.sleep(0.25)
        except Exception:
            return False
    return True


def _confirm_buy_one(self) -> bool:
    """点确认购买并等待结果。"""
    # 确认按钮（购买弹窗）
    confirm_pos = (770, 500)
    try:
        self.click(confirm_pos[0], confirm_pos[1], duration=0.8, wait_over=True)
    except Exception:
        pass

    img_possibles = {
        "purchase_ap_notice": (770, 500),
        "purchase_ap_notice-localized": (770, 500),
        "main_page_full-notice": (887, 165),
    }
    rgb_possibles = {
        "reward_acquired": (640, 180),
    }
    img_ends = [
        "main_page_full-notice",
    ]
    rgb_ends = ["reward_acquired", "main_page"]
    try:
        picture.co_detect(
            self, rgb_ends, rgb_possibles, img_ends, img_possibles, True
        )
        return True
    except Exception as e:
        self.logger.warning(f"purchase_ap confirm detect: {e}")
        # 尽力关闭
        try:
            self.click(919, 165, duration=0.5, wait_over=True)
        except Exception:
            pass
        return False


def _close_to_main(self) -> None:
    img_possibles = {
        "purchase_ap_notice": (919, 165),
        "purchase_ap_notice-localized": (919, 165),
        "main_page_full-notice": (887, 165),
    }
    rgb_possibles = {
        "reward_acquired": (640, 180),
    }
    try:
        picture.co_detect(
            self, "main_page", rgb_possibles, None, img_possibles, True
        )
    except Exception:
        try:
            self.to_main_page()
        except Exception:
            pass
