# -*- coding: utf-8 -*-
"""工具大厅 auto_push 插件私有引擎：「推未通关图」块里的「推当前页面剧情/关卡」。

本模块属于工具大厅（module/tools/），只读复用主程序基础设施
（core.picture / core.image / module.activities.activity_utils /
module.explore_tasks.* 等），不修改任何上游文件。

识别思路内化自活动推图的成熟链路（activity_utils.to_story_task_info）：
按"按钮自身特征"（右半屏蓝青色块 + 白色文字）定位可开始的按钮，而不是按
页面身份枚举模板；列表翻页固定落在右侧列表的可拖拽空白列上。

蓝色调色板在真实活动剧情页失败截图上标定（2026-09 Highlander 活动）：
可开始按钮为浅青色（B≈239/G≈208/R≈124，B-R≥40），深藏青锁定钮（B≈109）
被区间天然排除；mini_story 可开始话的浅蓝 (109-129, 211-231, 245-255)
同样落在区间内。
"""
import os
import time

import cv2
import numpy as np

from core import color, image, picture

# 与上游 main_story._story_screen_ends 等价的三族剧情页模板名。
# 本地副本，避免 import 上游私有函数（上游文件保持不动）。
_STORY_FAMILIES = ("main_story", "mini_story", "group_story")

# (r_min, r_max, g_min, g_max, b_min, b_max)，RGB 语义
_BLUE_RANGES = (
    (40, 195, 150, 240, 185, 255),
)

_SCAN_AREA = (640, 60, 1280, 700)   # 右半屏（1280x720 逻辑坐标）
_BTN_W = (45, 130)                  # 按钮几何（逻辑像素）
_BTN_H = (22, 75)
_WHITE_TEXT_MIN = 0.04              # 块内近白文字像素占比下限（区分纯蓝装饰）

_LIST_SWIPE_X_DEFAULT = 907         # 右侧列表的可拖拽空白列（与活动推图一致）
_SWIPE_Y_FROM, _SWIPE_Y_TO = 520, 200
_STORY_TIMEOUT = 8                  # 单轮识别超时（秒），连续 3 次失败放弃
_STAGE_TIMEOUT = 15                  # 关卡单步识别超时（秒），连续 3 次失败自动停止
_ENTER_BTN_AREA = (1055, 191, 1201, 632)    # 选关列表入场按钮列（1280x720 逻辑坐标）
_ENTER_BTN_OCR_OFFSET = (-396, -7, 60, 33)  # 按钮左侧的关卡号标签（与上游 swipe_search 一致）



class _InputHealer:
    """uiautomator 注入自愈：会话陈旧导致 INJECT_EVENTS 权限失效时，
    重启服务并重试。通过实例属性遮罩 click/swipe/u2_swipe 实现，仅引擎
    运行期间生效，退出还原。"""

    _METHODS = ("click", "swipe", "u2_swipe")

    def __init__(self, baas):
        self._baas = baas
        self._saved = {}

    @staticmethod
    def _is_injection_error(e):
        text = str(e)
        return ("INJECT_EVENTS" in text or "SecurityException" in text
                or "-32001" in text)

    def _heal(self):
        baas = self._baas
        logger = baas.logger
        logger.warning("[自愈] 注入权限失效（INJECT_EVENTS），重启 uiautomator 服务...")
        try:
            baas.u2.connection.reset_uiautomator()
        except Exception as e:
            logger.warning("[自愈] reset_uiautomator 失败（%s），改用 BAAS 启动流程。" % e)
            baas.wait_uiautomator_start()
        time.sleep(2)

    def _wrap(self, name):
        baas = self._baas
        original = getattr(baas, name, None)
        if original is None:
            return  # 对象上不存在该方法（如测试桩），跳过
        self._saved[name] = original
        healer = self

        def healed(*args, **kwargs):
            for attempt in range(3):
                try:
                    return original(*args, **kwargs)
                except Exception as e:
                    if attempt >= 2 or not healer._is_injection_error(e):
                        raise
                    healer._heal()

        setattr(baas, name, healed)

    def run(self, fn):
        baas = self._baas
        if getattr(baas, "_input_healer_active", False):
            return fn(baas)  # 已有自愈在生效（嵌套调用），不重复包装
        baas._input_healer_active = True
        try:
            for name in self._METHODS:
                self._wrap(name)
            return fn(baas)
        finally:
            for name in self._saved:
                try:
                    delattr(baas, name)
                except AttributeError:
                    pass
            baas._input_healer_active = False


def _story_screen_ends():
    ends = ["main_story_plot-not-open", "main_story_plot-index"]
    for fam in _STORY_FAMILIES:
        ends.append(fam + "_menu")
        ends.append(fam + "_select-episode")
        ends.append(fam + "_episode-info")
        ends.append(fam + "_episode-cleared-feature")
    return ends


def find_blue_action_buttons(baas, area=_SCAN_AREA):
    """在右半屏扫描"可开始"的蓝青色按钮。

    返回 [(cx, cy, w, h), ...]，1280x720 逻辑坐标，按 y、x 排序。
    """
    ratio = getattr(baas, "ratio", 1.0) or 1.0
    baas.update_screenshot_array()
    img = baas.latest_img_array
    if img is None or img.size == 0:
        return []
    x0, y0, x1, y1 = area
    ax0, ay0 = int(x0 * ratio), int(y0 * ratio)
    roi = img[ay0:int(y1 * ratio), ax0:int(x1 * ratio)]
    if roi.size == 0:
        return []
    b = roi[:, :, 0].astype(np.int16)
    g = roi[:, :, 1].astype(np.int16)
    r = roi[:, :, 2].astype(np.int16)
    mask = np.zeros(roi.shape[:2], dtype=np.uint8)
    for (r_min, r_max, g_min, g_max, b_min, b_max) in _BLUE_RANGES:
        mask |= ((r >= r_min) & (r <= r_max) & (g >= g_min) & (g <= g_max)
                 & (b >= b_min) & (b <= b_max) & ((b - r) >= 40)).astype(np.uint8) * 255
    kx = max(3, int(round(15 * ratio)))
    ky = max(3, int(round(7 * ratio)))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx | 1, ky | 1))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, px = stats[i]
        lw, lh = w / ratio, h / ratio
        if not (_BTN_W[0] <= lw <= _BTN_W[1] and _BTN_H[0] <= lh <= _BTN_H[1]):
            continue
        if px < lw * lh * 0.35:                      # 填充率：排除细长杂带
            continue
        aspect = lw / max(lh, 1.0)
        if not (1.2 <= aspect <= 4.5):
            continue
        bx0, by0 = ax0 + x, ay0 + y
        sub = img[by0:by0 + h, bx0:bx0 + w]          # 白色文字校验（入场/开始为白字）
        if sub.size == 0:
            continue
        white = ((sub[:, :, 0] >= 225) & (sub[:, :, 1] >= 225) & (sub[:, :, 2] >= 225)).mean()
        if white < _WHITE_TEXT_MIN:
            continue
        out.append(((bx0 + w / 2.0) / ratio, (by0 + h / 2.0) / ratio, lw, lh))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def swipe_story_list(baas, x=None):
    """在右侧列表的可拖拽空白列纵向翻一页（修复旧版滑在角色立绘上的问题）。"""
    if x is None:
        x = _LIST_SWIPE_X_DEFAULT
    else:
        x = max(750, min(1100, int(x)))
    duration = 0.1 if getattr(baas, "is_android_device", False) else 0.5
    baas.swipe(x, _SWIPE_Y_FROM, x, _SWIPE_Y_TO, duration, post_sleep_time=1)


def _push_current_story_impl(baas):
    """从当前画面开始推剧情。返回 True=结束（推完/无可推），False=识别失败。"""
    logger = baas.logger
    logger.info("-- Push plots from current screen (tool hall) --")
    reactions = dict(picture.GAME_ONE_TIME_POP_UPS[baas.server])
    failed = 0
    idle_rounds = 0
    activity_tried = False
    while baas.flag_run:
        # 按页面自动切换：先做有界模板探测——主线/外传/小组剧情页命中则走
        # 结构化分发（菜单箭头/绿点判定更准）；未命中（活动等无数据页面）
        # 立即转蓝色按钮优先：点按钮 → 进剧情 → 跳过/战斗 → 结算 → 重扫。
        res = None
        try:
            res = picture.co_detect(baas, None, None, _story_screen_ends(),
                                    reactions, True, time_out=4)
            failed = 0
        except picture.FunctionCallTimeout:
            # 非剧情页：蓝色按钮优先
            btns = find_blue_action_buttons(baas)
            if btns and _generic_blue_loop(baas, btns):
                return True
            failed += 1
            if failed >= 3:
                _save_debug_shot(baas)
                return False
            if not activity_tried:
                # 自愈①：不在"故事"页签就切过去；当期活动的故事页 → 复用上游成熟链路整段推完
                activity_tried = True
                _switch_to_story_tab(baas)
                if _activity_story_available(baas) and _push_activity_stories(baas):
                    return True
            # 自愈②：右侧列表翻页后再试
            logger.warning("4 秒未识别剧情画面，在右侧列表滑动后重试。")
            swipe_story_list(baas, btns[0][0] if btns else None)
            continue

        logger.info("Story screen: " + str(res))
        idle_rounds = 0
        if res.endswith("_episode-info"):
            _clear_plot(baas, res[: -len("_episode-info")])
            continue
        if res.endswith("_episode-cleared-feature"):
            _back_to_menu(baas, res[: -len("_episode-cleared-feature")])
            continue
        if res.endswith("_menu"):
            fam = res[: -len("_menu")]
            if fam == "main_story":
                from module.main_story import check_episode
                ep = check_episode(baas)
                if ep == "ALL_CLEAR":
                    logger.warning("-- Main story all cleared. Done. --")
                    return True
                baas.click(ep[0], ep[1], wait_over=True)
            else:
                from module.mini_story import check_6_region_status
                status = check_6_region_status(baas)
                logger.info("6 region status: " + str(status))
                picked = next((i for i, ok in enumerate(status) if ok), None)
                if picked is None:
                    logger.warning("-- No new stories on this page. Done. --")
                    return True
                pos = _REGION_CLICK_POS[picked]
                baas.click(pos[0], pos[1], wait_over=True)
            continue
        if res == "main_story_plot-not-open":
            logger.warning("-- Remaining plots locked. Done. --")
            return True

        # 选话页：找可开始的话
        fam = res[: -len("_select-episode")]
        if res == "main_story_plot-index":
            fam = "main_story"
        target = None
        if fam == "main_story":
            from module.main_story import check_current_plot_status
            for pos in ([728, 257], [668, 362]):
                if check_current_plot_status(baas, pos) == "UNCLEAR":
                    target = pos
                    break
        else:
            from module.mini_story import one_detect
            target = one_detect(baas)
        if target is not None:
            _to_episode_info(baas, fam, target)
            continue
        # 本页没有可开始的：右侧列表翻页找下一页
        idle_rounds += 1
        if idle_rounds >= 3:
            logger.warning("-- No more startable plots on this page. Done. --")
            return True
        swipe_story_list(baas)
    return False


_POPUP_KINDS = ("normal_task_task-info", "activity_task-info",
                "normal_task_task-A-info", "normal_task_SUB")
_TAKEOVER_FORMATION = "normal_task_formation-menu"   # 出击/编队画面（右下角黄色"出击"按钮）
_POPUP_TAKEOVER_KINDS = _POPUP_KINDS + (_TAKEOVER_FORMATION,)
_STAGE_BOTTOM_Y = 560   # 屏幕底部范畴：入场按钮 y≥此值时启用终止判定


def _find_blue_buttons(baas):
    """右半屏所有蓝色可点按钮（剧情引擎同款调色板扫描），返回 [(cx, cy)]。"""
    return [(int(cx), int(cy)) for (cx, cy, _w, _h) in find_blue_action_buttons(baas)]


def _find_framed_buttons(baas, area=(500, 60, 1280, 700)):
    """白框包蓝芯的入场按钮（浅色主题活动页：入场钮被白色边框包裹）。

    算法：白色掩码洞填充 → 被"白"包围的彩色岛 → 蓝色密度 + 白字过滤。
    返回 [(cx, cy)]。
    """
    ratio = getattr(baas, "ratio", 1.0) or 1.0
    baas.update_screenshot_array()
    img = baas.latest_img_array
    if img is None or img.size == 0:
        return []
    x0, y0, x1, y1 = area
    ax0, ay0, ax1, ay1 = int(x0 * ratio), int(y0 * ratio), int(x1 * ratio), int(y1 * ratio)
    roi = img[ay0:ay1, ax0:ax1]
    if roi.size == 0:
        return []
    b = roi[:, :, 0].astype(np.int16)
    g = roi[:, :, 1].astype(np.int16)
    r = roi[:, :, 2].astype(np.int16)
    blue = ((r >= 40) & (r <= 195) & (g >= 150) & (g <= 240) & (b >= 185)
            & (b <= 255) & ((b - r) >= 40)).astype(np.uint8) * 255
    white = ((r >= 225) & (g >= 225) & (b >= 225)).astype(np.uint8)  # 0/1，供洞填充使用
    inv = (1 - white)
    padded = cv2.copyMakeBorder(inv, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=1)
    ff = padded.copy()
    hmask = np.zeros((padded.shape[0] + 2, padded.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, hmask, (0, 0), 0)
    holes = (ff[1:-1, 1:-1] & inv).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
    holes = cv2.morphologyEx(holes, cv2.MORPH_CLOSE, kernel)
    n, _, stats, _ = cv2.connectedComponentsWithStats(holes, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, px = stats[i]
        if not (35 <= w <= 220 and 18 <= h <= 150):
            continue
        if px < w * h * 0.3:
            continue
        density = blue[y:y + h, x:x + w].mean() / 255.0
        if density < 0.15:
            continue
        sub = roi[y:y + h, x:x + w]
        white_txt = ((sub[:, :, 0] >= 225) & (sub[:, :, 1] >= 225)
                     & (sub[:, :, 2] >= 225)).mean()
        if white_txt < 0.02:
            continue
        out.append((int(x0 + x + w / 2), int(y0 + y + h / 2)))
    return out


def _find_yellow_buttons(baas, area=(850, 400, 1280, 720)):
    """右下角黄色"出击"按钮（出击/编队画面），返回 [(cx, cy)]。

    颜色在真实出击截图上标定：RGB(249,234,84) 大面积纯黄 + 白字。
    """
    ratio = getattr(baas, "ratio", 1.0) or 1.0
    baas.update_screenshot_array()
    img = baas.latest_img_array
    if img is None or img.size == 0:
        return []
    x0, y0, x1, y1 = area
    ax0, ay0, ax1, ay1 = int(x0 * ratio), int(y0 * ratio), int(x1 * ratio), int(y1 * ratio)
    roi = img[ay0:ay1, ax0:ax1]
    if roi.size == 0:
        return []
    b = roi[:, :, 0].astype(np.int16)
    g = roi[:, :, 1].astype(np.int16)
    r = roi[:, :, 2].astype(np.int16)
    mask = ((r >= 220) & (g >= 190) & (b <= 160) & ((r - b) >= 70)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, px = stats[i]
        if not (100 <= w <= 280 and 45 <= h <= 140):
            continue
        if px < w * h * 0.6:
            continue
        sub = roi[y:y + h, x:x + w]
        white_txt = ((sub[:, :, 0] >= 225) & (sub[:, :, 1] >= 225)
                     & (sub[:, :, 2] >= 225)).mean()
        if white_txt < 0.03:
            continue
        out.append((int(x0 + x + w / 2), int(y0 + y + h / 2)))
    return out


def _find_labeled_buttons(baas, with_label=True):
    """普通选关页入场按钮（模板 + 可选关卡号 OCR），返回 [(x, y, label)]。

    label 用于匹配关卡数据（格子模式）；识别失败时为空串。
    with_label=False 仅做存在性检查（省去 OCR），供战斗后等待循环使用。
    """
    positions = image.get_image_all_appear_position(
        baas, "normal_task_enter-task-button", _ENTER_BTN_AREA, 0.8)
    out = []
    for group in image.merge_nearby_coordinates(positions, 5, 5):
        xs = [p[0] for p in group]
        ys = [p[1] for p in group]
        x, y = int(sum(xs) / len(xs)), int(sum(ys) / len(ys))
        label = ""
        if with_label:
            ox, oy, ow, oh = _ENTER_BTN_OCR_OFFSET
            label = baas.ocr.get_region_res(
                baas=baas,
                region=(x + ox, y + oy, x + ox + ow, y + oy + oh),
                language="en-us",
                candidates="1234567890-A-",
                filter_score=0.2,
            )
        out.append((x, y, (label or "").strip()))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def _parse_label(label):
    """"15-3" -> (15, 3)；"15-A" -> (15, 6)；解析失败 -> (None, None)。"""
    label = (label or "").strip().upper()
    if "-" not in label:
        return None, None
    r, m = label.split("-", 1)
    if not r.isdigit():
        return None, None
    if m == "A":
        return int(r), 6
    if m.isdigit():
        return int(r), int(m)
    return None, None


# 以下反应表为上游 task_utils.to_normal_event / to_hard_event 的本地副本
# （逐字一致，另补 formation/activity 弹窗关闭点），仅为了让 co_detect 能
# 带上有界 time_out；上游文件保持不动。
_TO_HARD_RGB_REACTIONS = {
    "event_normal": (1064, 165),
    "main_page": (1198, 580),
    "level_up": (640, 200),
}
_TO_NORMAL_RGB_REACTIONS = {
    "event_hard": (805, 165),
    "main_page": (1198, 580),
    "level_up": (640, 200),
}
_TO_LIST_IMG_REACTIONS = {
    # ── task_utils.to_normal_event 全表 ──
    "main_page_bus": (823, 261),
    "normal_task_sweep-complete": (643, 585),
    "normal_task_start-sweep-notice": (887, 164),
    "normal_task_unlock-notice": (887, 164),
    "normal_task_task-info": (1128, 130),
    "normal_task_skip-sweep-complete": (643, 506),
    "purchase_ap_notice": (919, 165),
    "purchase_ap_notice-localized": (919, 165),
    "normal_task_task-finish": (1038, 662),
    "normal_task_prize-confirm": (776, 655),
    "normal_task_fight-confirm": (1168, 659),
    "normal_task_fight-complete-confirm": (1160, 666),
    "normal_task_reward-acquired-confirm": (800, 660),
    "normal_task_task-A-info": (1128, 130),
    # ── task_utils.to_hard_event 补充 ──
    "normal_task_charge-challenge-counts": (887, 161),
    # ── Baas_thread.to_main_page 全表（逐项收录）──
    "main_page_game-download-resource-notice": (761, 504),
    "main_page_game-download-resource-notice2": (761, 504),
    "main_page_game-download-resource-notice3": (761, 504),
    "main_page_privacy-policy": (772, 501),
    # 刻意不收录 main_page_quick-home / cafe_quick-home：点它=跳回主页，会中断选关流程
    "main_page_daily-attendance": (640, 360),
    "main_page_item-expire": (925, 119),
    "main_page_skip-notice": (762, 507),
    "draw-card-point-exchange-to-stone-piece-notice": (933, 155),
    "main_page_enter-existing-fight": (514, 501),
    "main_page_login-feature": (640, 360),
    "main_page_relationship-rank-up": (640, 360),
    "main_page_full-notice": (887, 165),
    "normal_task_fail-confirm": (643, 658),
    "normal_task_fight-task-info": (420, 592),
    "normal_task_task-operating-feature": (1000, 660),
    "normal_task_mission-operating-task-info": (1000, 664),
    "normal_task_mission-operating-task-info-notice": (416, 595),
    "normal_task_mission-pause": (768, 501),
    "normal_task_task-begin-without-further-editing-notice": (888, 163),
    "normal_task_task-operating-round-over-notice": (888, 163),
    "momo_talk_momotalk-peach": (1123, 122),
    "cafe_students-arrived": (922, 189),
    "pass_menu": (1247, 40),
    "pass_mission-menu": (1247, 40),
    "group_sign-up-reward": (920, 159),
    "cafe_invitation-ticket": (835, 97),
    "lesson_lesson-information": (964, 117),
    "lesson_all-locations": (1138, 117),
    "lesson_lesson-report": (642, 556),
    "lesson_purchase-lesson-ticket-menu": (921, 169),
    "rewarded_task_purchase-bounty-ticket-menu": (921, 165),
    "scrimmage_purchase-scrimmage-ticket-menu": (921, 162),
    "arena_battle-win": (640, 530),
    "arena_battle-lost": (640, 468),
    "arena_season-record": (640, 538),
    "arena_best-record": (640, 538),
    "arena_opponent-info": (1012, 98),
    "plot_menu": (1202, 37),
    "plot_skip-plot-button": (1208, 116),
    "plot_skip-plot-notice": (770, 519),
    "activity_fight-success-confirm": (640, 663),
    "total_assault_reach-season-highest-record": (640, 528),
    "total_assault_total-assault-info": (1165, 107),
    "cafe_cafe-reward-status": (985, 147),
    # CN 专属（to_main_page 的 update['CN']）
    "main_page_news": (1142, 104),
    "main_page_news2": (1142, 104),
    "main_page_net-work-unstable": (753, 500),
    "main_page_fail-to-load-game-resources": (740, 437),
    # ── 本引擎补充的关闭点 / 实测结算链 ──
    "normal_task_fight-success-confirm": (640, 663),  # 外传/活动战斗成功确认（用户截图标定）
    "normal_task_formation-menu": (1154, 625),
    "normal_task_SUB": (1128, 130),
    "activity_task-info": (1128, 130),
    # 注意：刻意不收录 normal_task_fight-end-back-to-main-page（点它会回主
    # 页，中断当前选关页流程）；该画面与 prize-confirm 同屏，点 prize 照常前进。
}
_TO_HARD_IMG_REACTIONS = _TO_LIST_IMG_REACTIONS


def _collect_stage_candidates(baas, done, find_labeled, find_blue, find_framed,
                              region_data_fn):
    """整页扫描一次，合并三类入场按钮来源为候选队列。

    队列元素：(kind, x, y, key, label, region, mission, task_data_name, task_data)，
    按纵坐标排序（自上而下）；带关卡号的模板来源优先覆盖同位置的其他来源。
    """
    items = []
    labeled = [b for b in find_labeled(baas, with_label=True) if b[2] not in done]
    for (x, y, label) in labeled:
        region, mission = _parse_label(label)
        tdn = td = None
        if region and mission:
            try:
                d = region_data_fn(region)
            except Exception:
                d = {}
            matches = {k: v for k, v in d.items()
                       if k.startswith("%s-%s" % (region, mission))}
            if matches:
                tdn, td = next(iter(matches.items()))
        items.append(("labeled", x, y, label, label, region, mission, tdn, td))
    taken = [(x, y) for (k, x, y, *_r) in items]

    def _free(cx, cy):
        return not any(abs(cx - px) < 80 and abs(cy - py) < 30 for (px, py) in taken)

    for (cx, cy) in find_framed(baas):
        key = "f:%d" % (cy // 10)
        if key in done or not _free(cx, cy):
            continue
        items.append(("framed", cx, cy, key, "", None, None, None, None))
        taken.append((cx, cy))
    for (cx, cy) in find_blue(baas):
        key = "b:%d" % (cy // 10)
        if key in done or not _free(cx, cy):
            continue
        items.append(("blue", cx, cy, key, "", None, None, None, None))
        taken.append((cx, cy))
    items.sort(key=lambda t: (t[2], t[1]))
    return items


def _buttons_all(baas):
    """合并三类来源的入场按钮，返回自上而下的点击坐标 [(x, y, label)]。

    模板来源坐标是匹配点左上角，统一换算成按钮中心；同一按钮被多来源
    命中时按位置去重。关卡号 OCR 仅用于查格子数据，不参与去重。
    """
    labeled = _find_labeled_buttons(baas, with_label=True)
    cands = [(x + 34, y + 21, lbl) for (x, y, lbl) in labeled]
    cands += [(cx, cy, "") for (cx, cy) in _find_framed_buttons(baas)]
    cands += [(cx, cy, "") for (cx, cy) in _find_blue_buttons(baas)]
    cands.sort(key=lambda t: (t[1], t[0]))
    out = []
    for c in cands:
        if out and abs(c[0] - out[-1][0]) < 80 and abs(c[1] - out[-1][1]) < 30:
            continue
        out.append(c)
    return out


def push_current_stage(baas):
    """公开入口：包一层输入自愈（INJECT_EVENTS 失效 → 重启服务 → 重试）。"""
    return _InputHealer(baas).run(_push_current_stage_impl)


def _push_current_stage_impl(baas):
    """推当前页面关卡（用户标定的极简循环，不读任何推图清单）：

    1. 扫描屏幕上的入场按钮，点最上面的一个；
    2. 弹窗判定：未通关 → 开战 → 清结算 → 回到 1（游戏会把未通关置顶）；
    3. 已通关 → 往下拽一行，点同一位置的下一个，逐行往下试；
    4. 坐标到屏幕底部尽头：点已通关 → 上拽（列表前进）→ 同一最下位置
       仍已通关 → 走到头了，结束。
    """
    from module.explore_tasks.explore_task import (
        extract_first_team,
        need_fight,
    )
    from module.explore_tasks.task_utils import (
        convert_team_config,
        employ_units,
        execute_grid_task,
        get_stage_data,
    )
    from module.main_story import auto_fight

    logger = baas.logger
    logger.info("-- Push stages from current screen (tool hall) --")

    region_data_cache = {}
    failed = 0
    idle = 0
    rows = 0
    buttons_seen = False
    pushed_any = False
    popup_rounds = 0
    sortie_rounds = 0

    def _cd(*args, **kw):
        kw.setdefault("time_out", _STAGE_TIMEOUT)
        return picture.co_detect(*args, **kw)

    def _region_data(region):
        if region not in region_data_cache:
            try:
                region_data_cache[region] = get_stage_data(region, True)
            except (FileNotFoundError, json.JSONDecodeError):
                logger.warning("区域 %s 没有关卡数据，按通用简易流程推（保持当前队伍）。" % region)
                region_data_cache[region] = {}
        return region_data_cache[region]

    def _set_mode():
        # 上游 set_explore_task_mode 的有界副本（详情页上切换 简易/格子 模式）
        st = "simple" if baas.config.explore_task_use_simple_mode else "grid"
        logger.info("Set Explore Task Mode : [ " + st + " ]")
        mode = "explore-task-%s-mode" % st
        rgb_possibles = {"explore-task-grid-mode": (1120, 187),
                         "explore-task-simple-mode": (611, 178)}
        rgb_possibles.pop(mode)
        _cd(baas, mode, rgb_possibles, skip_first_screenshot=True)

    def _close_info_bounded():
        """关掉关卡详情弹窗，并确认它真的关了。

        旧弹窗残影是"已通关误判"的根源：下一个按钮点下去，模板匹配到
        的其实是上一关还在淡出的弹窗，判的是上一关的状态。所以点 X 后
        验证模板消失，没消失就再点，最多 6 轮。
        """
        for _ in range(6):
            baas.click(1128, 130, wait_over=True)
            time.sleep(0.5)
            baas.update_screenshot_array()
            still = (image.get_image_all_appear_position(
                        baas, "activity_task-info", (0, 0, 1280, 720), 0.8)
                     or image.get_image_all_appear_position(
                        baas, "normal_task_task-info", (0, 0, 1280, 720), 0.8))
            if not still:
                return
        logger.warning("[关窗] 详情弹窗仍未关闭，继续。")

    def _fight_popup(kind, task_data_name=None, task_data=None):
        """战斗前弹窗分发：普通/困难/委托/活动/外传开打，已通关关闭跳过。"""
        time.sleep(1)  # 等弹窗动画结束再判定，防误读"已通关"
        if kind == "activity_task-info":
            from module.activities import activity_utils
            if activity_utils.check_sweep_availability(baas, "activity_task-info") == "sss":
                logger.warning("活动关卡已通关，跳过。")
                return False
            rgb_ends = ["formation_edit1", "formation_edit2", "formation_edit3",
                        "formation_edit4", "reward_acquired"]
            img_ends = ["activity_unit-formation", "activity_formation", "activity_self-formation"]
            img_reactions = {
                "activity_task-info": (940, 538),
                "normal_task_task-info": (940, 538),
                "plot_menu": (1205, 34),
                "plot_skip-plot-button": (1213, 116),
                "plot_skip-plot-notice": (766, 520),
            }
            res = _cd(baas, rgb_ends, None, img_ends, img_reactions, True)
            if res == "reward_acquired":
                return False
            fake = {"start": [[_event_attribute(), [0, 0]]]}
            return _employ_and_fight(fake)
        if kind == "normal_task_task-A-info":
            name = task_data_name or "stage-6"
            if "-6" not in name:
                name += "-6"
            if not need_fight(baas, name, True):
                logger.warning("%s A 关已通关，跳过。" % (task_data_name or ""))
                return False
            _cd(baas, img_ends="normal_task_formation-menu",
                img_reactions={"normal_task_task-A-info": (946, 540)},
                skip_first_screenshot=True)
            return _employ_and_fight(task_data)
        # normal_task_task-info / normal_task_SUB
        if task_data_name:
            _set_mode()
            judge = lambda: need_fight(baas, task_data_name, True)
        else:
            judge = lambda: color.check_sweep_availability(baas, True) in ("no-pass", "pass")
        fight_needed = judge()
        if not fight_needed:
            logger.warning("%s 已通关，跳过。" % (task_data_name or "关卡"))
            return False
        if (task_data is not None and task_data.get("action")
                and not baas.config.explore_task_use_simple_mode):
            return execute_grid_task(baas, task_data)
        _cd(baas, img_ends="normal_task_formation-menu",
            img_reactions={"normal_task_task-info": (946, 540),
                           "normal_task_SUB": (946, 540)},
            skip_first_screenshot=True)
        return _employ_and_fight(task_data)

    def _handle_popup(kind, task_data_name=None, task_data=None):
        fought = _fight_popup(kind, task_data_name, task_data)
        if not fought:
            # 未开战（已通关跳过/编队失败）：有界关掉弹窗回列表，不进入战斗等待
            _close_info_bounded()
        return fought

    def _popup_kind(timeout):
        """有界探测当前是否停在战斗前弹窗（"开始任务"画面）。"""
        try:
            return _cd(baas, None, None, list(_POPUP_KINDS), None, True, time_out=timeout)
        except picture.FunctionCallTimeout:
            return None

    def _formation_detected(timeout):
        """有界探测当前是否停在出击/编队画面。"""
        try:
            return _cd(baas, None, None, _TAKEOVER_FORMATION, None, True, time_out=timeout)
        except picture.FunctionCallTimeout:
            return None

    def _wait_back_to_page():
        """战斗后等待：以结算画面信号为锚等战斗结束，再清结算链。

        - 锚点信号（fight-confirm/fight-success/prize 等 8 个）一出现立即
          接管，最长等 300 秒。
        - 结算链逐屏清（每轮 4 秒有界，共 40 轮）；按钮出现后隔 1.2 秒二次
          确认仍存在才算回到页面（结算动画残影会变，真实页面不变）。
        """
        logger.info("[战斗后] 等待战斗结束（以结算画面信号为锚，最长 300 秒）...")
        anchors = ["normal_task_fight-confirm", "normal_task_fight-success-confirm",
                   "activity_fight-success-confirm", "normal_task_task-finish",
                   "normal_task_prize-confirm", "normal_task_fight-complete-confirm",
                   "normal_task_reward-acquired-confirm", "normal_task_fail-confirm"]
        try:
            img = dict(_TO_HARD_IMG_REACTIONS)
            img.update(picture.GAME_ONE_TIME_POP_UPS[baas.server])
            anchor = _cd(baas, None, None, anchors, img, True, time_out=300,
                         check_pkg_interval=120)
            logger.info("[战斗后] 结算信号出现：%s，立即接管。" % anchor)
        except picture.FunctionCallTimeout:
            logger.warning("[战斗后] 300 秒未见结算信号，尝试继续扫描。")
        for _ in range(40):
            if not baas.flag_run:
                return
            try:
                img = dict(_TO_HARD_IMG_REACTIONS)
                img.update(picture.GAME_ONE_TIME_POP_UPS[baas.server])
                _cd(baas, ["event_normal", "event_hard"], _TO_HARD_RGB_REACTIONS,
                    None, img, True, time_out=4)
                return  # 回到普通/困难选关页：按钮一定在
            except picture.FunctionCallTimeout:
                pass
            # 活动/外传页没有普通页特征：看入场按钮是否已经重新出现
            if (_find_labeled_buttons(baas, with_label=False) or _find_blue_buttons(baas)
                    or _find_framed_buttons(baas)):
                time.sleep(1.2)  # 二次确认：残影会变，真实页面不变
                if (_find_labeled_buttons(baas, with_label=False) or _find_blue_buttons(baas)
                        or _find_framed_buttons(baas)):
                    return

    def _employ_and_fight(task_data):
        """编队（无数据 = 保持当前队伍）并开战。"""
        team = extract_first_team(task_data) if task_data and task_data.get("start") else {"start": []}
        # 每次新鲜转换：employ_units 会弹出 keep_current 标记，不能复用旧字典
        team_config = convert_team_config(baas)
        method = baas.config.choose_team_method
        if not any(team_config.get(a) for a in ("burst", "pierce", "mystic", "shock", "default")):
            # 一支预设都没配：直接按当前队伍打（order），跳过上游
            # "Insufficient presets" 的 ERROR/WARNING 误报
            method = "order"
        if not employ_units(baas, method, team or {"start": []}, team_config):
            return False
        auto_fight(baas)
        return True

    def _event_attribute():
        """当期活动数据里取一个任务属性（仅影响编队属性池选择）。"""
        try:
            activity = getattr(baas, "current_game_activity", None)
            if activity:
                sd = json.load(open("src/explore_task_data/activities/%s.json" % activity,
                                    encoding="utf-8"))
                mission = sd.get("mission") or []
                if mission:
                    return mission[0]
        except Exception:
            pass
        return "burst"


    while baas.flag_run:
        # 0) 用户已手动点过入场：接管战斗前弹窗 / 出击画面
        kind = _popup_kind(2.5)
        if kind is None:
            kind = _formation_detected(2.0)
        if kind:
            if kind == _TAKEOVER_FORMATION:
                sortie_rounds += 1
                if sortie_rounds > 20:
                    logger.error("出击处理次数异常，停止。")
                    _save_debug_shot(baas, "出击处理异常，已存调试截图。")
                    return False
                logger.info("[接管] 出击画面，点击出击开战。")
                ys = _find_yellow_buttons(baas)
                if ys:
                    baas.click(ys[0][0], ys[0][1], wait_over=True)
                else:
                    baas.click(1157, 651, wait_over=True)
                auto_fight(baas)
                pushed_any = True
                _wait_back_to_page()
            else:
                popup_rounds += 1
                if popup_rounds > 20:
                    logger.error("弹窗处理次数异常，停止。")
                    _save_debug_shot(baas, "弹窗处理异常，已存调试截图。")
                    return False
                logger.info("[接管] 战斗前弹窗：%s" % kind)
                if _fight_popup(kind) is True:
                    pushed_any = True
                    _wait_back_to_page()
                else:
                    _close_info_bounded()
            continue

        # 1) 扫描：点最上面的按钮
        cands = _buttons_all(baas)
        if not cands:
            idle += 1
            if idle == 1:
                logger.info("[扫描] 未命中，等 2 秒重扫（画面可能在刷新置顶）。")
                time.sleep(2)
                continue
            if not buttons_seen and not pushed_any:
                # 从始至终没见过任何入场按钮：这页面不对，直接停（用户标定：
                # 完全识别不到入场、窗口也点不开时就没必要再探索了）。
                logger.error("当前页面没有识别到任何入场按钮。")
                _save_debug_shot(baas, "请把游戏停在选关页/活动图等有入场按钮的页面后重试。")
                return False
            if idle == 2:
                logger.info("[扫描] 仍无按钮：点空白处关掉可能残留的说明窗。")
                baas.click(640, 360, wait_over=True)
                time.sleep(1)
                continue
            if not (buttons_seen or pushed_any):
                logger.error("当前页面没有识别到任何入场按钮。")
                _save_debug_shot(baas, "请把游戏停在选关页/活动图等有入场按钮的页面后重试。")
                return False
            if rows >= 12:
                if pushed_any:
                    logger.info("-- No more startable stages. Done. --")
                    return True
                logger.error("当前页面没有找到任何可点的战斗按钮。")
                _save_debug_shot(baas, "请把游戏停在选关页/活动图等有入场按钮的页面后重试。")
                return False
            rows += 1
            logger.info("[行探索] 往下拽一行继续找（第 %d 行）。" % rows)
            baas.swipe(907, 500, 907, 385, 0.4, post_sleep_time=1)
            continue
        idle = 0
        buttons_seen = True

        # 2) 点最上面的按钮并判定
        bx, by, label = cands[0]
        logger.info("[扫描] 点击 %s @ (%d, %d)" % (label or "按钮", bx, by))
        baas.click(bx, by, wait_over=True)
        try:
            kind = _cd(baas, None, None,
                       list(_POPUP_TAKEOVER_KINDS) + ["main_story_episode-info"],
                       None, True)
        except picture.FunctionCallTimeout:
            failed += 1
            logger.warning("%s 点击无反应（第 %d 次）。" % (label or "按钮", failed))
            if failed >= 3:
                _save_debug_shot(baas, "连续多次点击按钮失败，已存调试截图并停止。")
                return False
            continue
        failed = 0

        if kind == "main_story_episode-info":
            logger.info("剧情选话页，跳过（剧情请用「推当前页面剧情」）。")
            baas.click(56, 40, wait_over=True)
            continue
        if kind == _TAKEOVER_FORMATION:
            ys = _find_yellow_buttons(baas)
            if ys:
                logger.info("点击黄色出击按钮 @ (%d, %d)" % (ys[0][0], ys[0][1]))
                baas.click(ys[0][0], ys[0][1], wait_over=True)
            else:
                baas.click(1157, 651, wait_over=True)
            auto_fight(baas)
            pushed_any = True
            _wait_back_to_page()
            continue

        # 3) 弹窗判定：未通关开战；已通关 → 逐行往下试
        region, mission = _parse_label(label)
        task_data = task_data_name = None
        if region and mission:
            items = {k: v for k, v in _region_data(region).items()
                     if k.startswith("%d-%d" % (region, mission))}
            if items:
                task_data_name, task_data = next(iter(items.items()))
        if _handle_popup(kind, task_data_name, task_data) is True:
            pushed_any = True
            _wait_back_to_page()
            continue

        logger.info("[已通关] 往下拽一行，试下一个。")

        def _row_try(pos):
            """点击并判定，返回 'fought' / 'cleared'。"""
            baas.click(int(pos[0]), int(pos[1]), wait_over=True)
            try:
                kind = _cd(baas, None, None, list(_POPUP_TAKEOVER_KINDS), None, True)
            except picture.FunctionCallTimeout:
                return "cleared"  # 点了没弹窗 = 按钮无效
            return "fought" if _handle_popup(kind) is True else "cleared"

        py = by          # 上一次点击的坐标：保证坐标一路往下
        empty = 0        # 连续拽了但没有按钮的次数
        ended = False
        for row in range(18):
            baas.swipe(907, 500, 907, 385, 0.4, post_sleep_time=1)
            time.sleep(0.8)  # 等列表滚动停稳再扫
            cands = _buttons_all(baas)
            if not cands:
                empty += 1
                if empty >= 3:
                    logger.info("[终止] 连续拽行都没有按钮：走到头了。")
                    ended = True
                    break
                continue
            empty = 0
            nx, ny, nl = max(cands, key=lambda t: (t[1], t[0]))  # 最下面 = 坐标往下
            if ny <= py + 20:
                continue  # 这一屏没有更靠下的新行，继续拽
            logger.info("[行探索] 坐标往下 @ (%d, %d)" % (nx, ny))
            if ny >= 560:
                # 屏幕底部尽头：点了已通关 → 上拽 → 同一最下位置仍已通关 → 走到头
                if _row_try((nx, ny)) == "fought":
                    pushed_any = True
                    _wait_back_to_page()
                    break
                baas.swipe(907, 500, 907, 385, 0.4, post_sleep_time=1)
                time.sleep(0.8)
                below = [c for c in _buttons_all(baas) if c[1] >= 560]
                if not below:
                    logger.info("[终止] 底部尽头没有新按钮：走到头了。")
                    ended = True
                    break
                nx2, ny2, _nl = max(below, key=lambda t: (t[1], t[0]))
                if _row_try((nx2, ny2)) == "fought":
                    pushed_any = True
                    _wait_back_to_page()
                    break
                logger.info("[终止] 底部尽头仍已通关：走到头了。")
                ended = True
                break
            if _row_try((nx, ny)) == "fought":
                pushed_any = True
                _wait_back_to_page()
                break
            py = ny  # 已通关：坐标继续往下
        else:
            logger.info("[行探索] 行数用尽：走到头了。")
            ended = True
        if ended:
            if pushed_any:
                logger.info("-- No more startable stages. Done. --")
                return True
            logger.error("当前页面没有找到任何可点的战斗按钮。")
            _save_debug_shot(baas, "请把游戏停在选关页/活动图等有入场按钮的页面后重试。")
            return False
        # 行探索中开战了：回到循环顶部重扫（游戏已把未通关置顶）
    return False


# ---------------------------------------------------------------- 活动剧情分支

def _switch_to_story_tab(baas):
    """活动页当前不在"故事"页签时点过去；不在活动页则无操作。"""
    from core.image import compare_image
    for name, pos in (("activity_story-not-chosen-0", (844, 89)),
                      ("activity_story-not-chosen-1", (936, 89))):
        if compare_image(baas, name):
            baas.logger.info("Switch to activity story tab via " + name)
            baas.click(pos[0], pos[1], wait_over=True)
            return True
    return False


def _activity_story_available(baas):
    """当前画面是当期活动的"故事"列表页，且活动关卡数据 JSON 存在。"""
    try:
        from core.image import compare_image
        if not (compare_image(baas, "activity_story-chosen-0")
                or compare_image(baas, "activity_story-chosen-1")):
            return False
        activity = getattr(baas, "current_game_activity", None)
        if not activity:
            return False
        return os.path.exists("src/explore_task_data/activities/%s.json" % activity)
    except Exception:
        return False


def _push_activity_stories(baas):
    """复用上游活动推剧链路（to_story_task_info 的 OCR+右列滑动）逐话推完。

    与 explore_activity_story 的差别仅在：不做回主页导航（用户已在页面上）。
    """
    from module.activities import activity_utils
    logger = baas.logger
    stage_data = activity_utils.get_stage_data(baas)
    total = int(stage_data.get("total_story", 0) or 0)
    if total <= 0:
        logger.warning("Activity story data empty; skip activity branch.")
        return False
    logger.info("Activity story branch: total stories = %d" % total)
    for k in range(1, total + 1):
        if not baas.flag_run:
            return False
        try:
            plot = activity_utils.to_story_task_info(baas, k, total)
        except (picture.FunctionCallTimeout, TypeError):
            logger.warning("Story %02d not located on the list; treat as list end." % k)
            return True
        if not plot:
            return True
        res = activity_utils.check_sweep_availability(baas, plot)
        if res == "sss":
            logger.info("Story %02d already cleared, skip." % k)
            continue
        logger.info("Pushing activity story %02d." % k)
        activity_utils.start_story(baas)
        activity_utils.to_activity(baas, "story", True)
    logger.warning("-- Activity stories all done. --")
    return True


# ---------------------------------------------------------------- 通用兜底分支

def _story_window_kind(baas, timeout=5.0):
    """点击剧情行后分类弹出的窗口规格（用户要求：先识别再行动）。

    返回 'info'（常规剧情窗口，可推）/ 'notice'（解锁"通知"弹窗，未解锁
    行）/ 'none'（什么都没弹）。通知弹窗的识别特征：蓝色确认按钮块位于
    (640, 502) 附近（用户截图标定）。
    """
    deadline = time.time() + timeout
    while time.time() < deadline and baas.flag_run:
        baas.update_screenshot_array()
        for tpl in ("activity_task-info", "main_story_episode-info",
                    "normal_task_task-info"):
            if image.get_image_all_appear_position(baas, tpl, (0, 0, 1280, 720), 0.8):
                return "info"
        if (color.rgb_in_range(baas, 640, 502, 40, 195, 150, 240, 185, 255)
                and color.rgb_in_range(baas, 640, 490, 40, 195, 150, 240, 185, 255)):
            return "notice"
        time.sleep(getattr(baas, "screenshot_interval", 0.3) or 0.3)
    return "none"


def _generic_blue_loop(baas, btns):
    """无活动数据环境的兜底：点剧情列表最下方的蓝色按钮，逐话往下推。

    剧情模式没有"已完成"判定（弹窗不区分首通/重播），点最上面会反复
    重播已通关的话。列表里最下面的蓝色按钮就是当前解锁的最后一话（更
    下面是未解锁的锁行，深色按钮不进蓝色扫描）。点开若没有剧情窗口
    （点了未解锁的行，弹"通关上文解锁"提示），关掉提示并往上点一行。
    领奖清屏参考推关卡引擎：全量反应表逐个点，直到回到剧情列表。
    结束条件：清屏后连续两轮扫不到蓝色按钮，或连续 3 次点不开剧情窗口。
    """
    logger = baas.logger
    idle = 0
    no_info_streak = 0
    up_move = None   # 点了未解锁行后，要往上点的目标
    last_list = []   # 最近一次扫描的按钮列表（自上而下）
    bottom_plays = 0

    def _settle():
        """领奖善后：全量反应表逐个点，直到回到剧情列表（2 轮 × 4 秒）。"""
        for _ in range(2):
            try:
                img = dict(_TO_HARD_IMG_REACTIONS)
                img.update(picture.GAME_ONE_TIME_POP_UPS[baas.server])
                picture.co_detect(baas, None, None, _story_screen_ends(), img, True,
                                  time_out=4)
                return
            except picture.FunctionCallTimeout:
                continue

    while baas.flag_run:
        btns = sorted(find_blue_action_buttons(baas), key=lambda t: (t[1], t[0]))
        last_list = btns
        if up_move is not None:
            target, up_move = up_move, None
        elif btns:
            target = btns[-1]  # 最下面 = 当前解锁的最后一话
        else:
            target = None
        if target is None:
            idle += 1
            if idle >= 2:
                logger.info("-- No new startable buttons. Done. --")
                return True
            swipe_story_list(baas)
            continue
        idle = 0
        at_bottom = target[1] >= 560
        logger.info("Click startable button at (%d, %d)." % (target[0], target[1]))
        baas.click(int(target[0]), int(target[1]), wait_over=True)
        res = _story_window_kind(baas)
        if res == "info":
            # 常规剧情窗口：可推
            try:
                from module.activities import activity_utils
                activity_utils.start_story(baas)
            except picture.FunctionCallTimeout:
                logger.warning("Playback ended unexpectedly.")
            no_info_streak = 0
            # 领奖善后（参考推关卡引擎的领奖链）：start_story 在
            # reward_acquired 处原样返回，不清屏的话奖励界面会挡住后续。
            _settle()
            if at_bottom:
                # 底部的剧情推完故事就完了：最多再容忍一次（两话可能都挤在
                # 底部边缘），之后停止，防止完结跳页签后误点其他页。
                bottom_plays += 1
                if bottom_plays >= 2:
                    logger.info("[终止] 底部剧情已推完，停止。")
                    return True
            continue
        # 非常规窗口（解锁"通知"弹窗 / 什么都没弹）：点空白处关掉
        no_info_streak += 1
        if at_bottom and bottom_plays >= 1:
            # 底部尽头按钮已通关/未解锁：故事推完（用户标定）
            logger.info("[终止] 底部尽头按钮已通关/未解锁：故事推完。")
            return True
        if no_info_streak >= 3:
            logger.info("-- 按钮打不开剧情窗口，停止。 --")
            return True
        logger.info("非常规窗口（%s）：点空白处关掉，往上点一行。" % res)
        baas.click(640, 360, wait_over=True)
        time.sleep(0.6)
        above = [b for b in last_list if b[1] < target[1] - 20]
        up_move = above[-1] if above else None
        if up_move is None:
            logger.info("-- 上面没有可点的行：走到头了。 --")
            return True
    return False


# ---------------------------------------------------------------- 家族分发辅助

_REGION_CLICK_POS = ([352, 240], [931, 240], [352, 396], [931, 396], [352, 537], [931, 537])


def _clear_plot(baas, fam):
    if fam == "main_story":
        from module.main_story import clear_current_plot
        return clear_current_plot(baas, True)
    if fam == "mini_story":
        from module.mini_story import clear_current_plot
        return clear_current_plot(baas, True)
    from module.group_story import clear_current_plot
    return clear_current_plot(baas, True)


def _to_episode_info(baas, fam, pos):
    if fam == "main_story":
        from module.main_story import to_episode_info
        return to_episode_info(baas, pos, True)
    if fam == "mini_story":
        from module.mini_story import to_episode_info
        return to_episode_info(baas, pos, True)
    from module.group_story import to_episode_info
    return to_episode_info(baas, pos, True)


def _back_to_menu(baas, fam):
    # 从选话/完成页回菜单：mini/group 左上 (56,40)，主线 (60,36)
    baas.click(56, 40 if fam != "main_story" else 60, wait_over=True)


def push_current_story(baas):
    """公开入口：包一层输入自愈（INJECT_EVENTS 失效 → 重启服务 → 重试）。"""
    return _InputHealer(baas).run(_push_current_story_impl)


def push_current_stage(baas):
    """公开入口：同上。"""
    return _InputHealer(baas).run(_push_current_stage_impl)


def _save_debug_shot(baas, hint="请把游戏停在剧情选章/选话页后重试。"):
    try:
        baas.update_screenshot_array()
        os.makedirs("log", exist_ok=True)
        shot = os.path.join("log", "debug_story_page_%d.png" % int(time.time()))
        cv2.imwrite(shot, baas.latest_img_array)
        baas.logger.error("未识别剧情画面，已存调试截图: " + shot)
    except Exception as e:
        baas.logger.error("保存调试截图失败: %s" % e)
    baas.logger.error(hint)
