"""Closed AP source adapters with an observed amount and a source-state receipt.

A source receipt is separate from delivery: automation additionally verifies the
character AP change and the complete mailbox multiset. No source is inferred
from an unrelated AP parcel arriving while a legacy task returned True.
"""
from __future__ import annotations

import hashlib
import re

import cv2
import numpy as np

from .errors import PluginError, require


def check(baas):
    require(bool(baas.flag_run), 'AUTOMATION_STOPPED', 'Automation was stopped.')
    require(baas.server == 'CN', 'SOURCE_LAYOUT_UNSUPPORTED', 'Verified AP source recognition currently supports the CN layout.')


def frame(baas):
    check(baas)
    image = baas.get_screenshot_array()
    from .hoard_mail import _frame
    # Keep the raw frame for legacy helpers, which apply baas.ratio themselves.
    # Parsing uses normalized coordinates; host clicks already scale them.
    baas.latest_img_array = image
    return _frame(image)


def text(baas, image, region):
    check(baas)
    x1, y1, x2, y2 = region
    value = baas.ocr.ocr_for_single_line('zh-cn', log_info='AP-source', origin_image=image[y1:y2, x1:x2],
                                         pass_method=1, filter_score=.8)
    return re.sub(r'\s+', '', str(value))


def receipt(amount, kind, *, skipped=False):
    return {'verified': True, 'amount': amount, 'receipt': kind, 'skipped': skipped}


def free_available(baas):
    from module import collect_daily_free_power as free
    check(baas)
    baas.to_main_page()
    free.to_purchase_pyroxenes_menu(baas)
    check(baas)
    free.to_purchase_type(baas, 'package')
    return free.detect_free_power_availability(baas)


def collect_free(baas):
    from core import picture
    from module import collect_daily_free_power as free
    if not free_available(baas):
        return receipt(0, 'free_already_collected', skipped=True)
    check(baas)
    result = picture.co_detect(baas, 'reward_acquired', None, 'main_page_full-notice',
                              {'main_page_purchase-pyroxenes-menu': (385, 479),
                               'main_page_purchase-pyroxenes-confirm-purchase-notice': (749, 571)},
                              skip_first_screenshot=True)
    require(result == 'reward_acquired', 'SOURCE_NOT_VERIFIED', 'The free AP reward dialog was not observed.')
    check(baas)
    free.return_to_main_page(baas)
    return receipt(10, 'free_reward_dialog')


def collect_club(baas):
    from module.group import to_group
    check(baas)
    baas.to_main_page()
    result = to_group(baas)
    check(baas)
    if result == 'group_sign-up-reward':
        return receipt(10, 'club_sign_in_reward')
    require(result in {'group_menu', 'group_join-club'}, 'SOURCE_NOT_VERIFIED', 'The club sign-in state was not recognized.')
    return receipt(0, 'club_already_signed_in' if result == 'group_menu' else 'club_not_joined', skipped=True)


def daily_selected(image, read):
    require(read((691, 92, 758, 124)) == '每日', 'DAILY_TAB_UNVERIFIED', 'The daily task tab label could not be verified.')
    hsv = cv2.cvtColor(image[88:132, 665:789], cv2.COLOR_BGR2HSV)
    return cv2.countNonZero(cv2.inRange(hsv, (95, 100, 130), (115, 255, 255))) >= 2500


def daily_page(baas):
    from module.collect_daily_task_power import to_tasks
    check(baas)
    to_tasks(baas)
    image = frame(baas)
    if not daily_selected(image, lambda region: text(baas, image, region)):
        check(baas)
        baas.click(722, 109, wait_over=True)
        image = frame(baas)
    require(daily_selected(image, lambda region: text(baas, image, region)),
            'DAILY_TAB_UNVERIFIED', 'The daily task tab is not selected.')
    return image


def daily_ap_rows(image, read):
    """Only full, individually claimable AP cards; never the weekly/all button."""
    from .hoard_mail import _green_shape
    reference = _green_shape(image[5:45, 499:532])
    require(reference is not None, 'SOURCE_NOT_VERIFIED', 'The task header AP icon is unreadable.')
    ref_contour, ref_mask = reference
    mask = cv2.inRange(cv2.cvtColor(image[147:610, 1080:1240], cv2.COLOR_BGR2HSV), (18, 90, 130), (40, 255, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rows = []
    for contour in contours:
        _x, rel_y, width, height = cv2.boundingRect(contour)
        y = 147 + rel_y
        if not (110 <= width <= 160 and 48 <= height <= 70 and y >= 198 and y + 70 <= 610):
            continue
        shape = _green_shape(image[y:y + 52, 1005:1083])
        if shape is None:
            continue
        candidate, candidate_mask = shape
        overlap = np.count_nonzero((ref_mask > 0) & (candidate_mask > 0)) / max(1, np.count_nonzero((ref_mask > 0) | (candidate_mask > 0)))
        require(overlap >= .68 and cv2.matchShapes(ref_contour, candidate, cv2.CONTOURS_MATCH_I1, 0) <= .20,
                'SOURCE_NOT_VERIFIED', 'A green task reward does not match the AP icon.')
        require(read((1095, y + 10, 1223, y + 52)) == '领取', 'SOURCE_NOT_VERIFIED', 'The individual AP task claim button is unreadable.')
        match = re.fullmatch(r'[xX×](\d{1,3})', read((1024, y + 39, 1082, y + 67)))
        require(match is not None and 0 < int(match[1]) <= 150, 'SOURCE_NOT_VERIFIED', 'The claimable task AP amount is unreadable.')
        title = read((590, y - 53, 1001, y - 15))
        require(len(title) >= 2, 'SOURCE_NOT_VERIFIED', 'The AP task identity is unreadable.')
        rows.append({'amount': int(match[1]), 'key': hashlib.sha256((title + ':' + match[1]).encode()).hexdigest(),
                     'point': (1158, y + height // 2)})
    return sorted(rows, key=lambda row: row['point'][1])


def collect_daily(baas, *, max_ap=150, only_task_key=None):
    from core import picture
    check(baas)
    baas.to_main_page()
    require(type(max_ap) is int and 0 <= max_ap <= 150, 'INVALID_SETTINGS', 'The daily AP limit must be between zero and 150.')
    total, claimed = 0, set()
    for _ in range(4):
        if total >= max_ap:
            return receipt(total, 'daily_ap_limit', skipped=total == 0)
        image = daily_page(baas)
        rows = daily_ap_rows(image, lambda region: text(baas, image, region))
        if only_task_key is not None:
            rows = [row for row in rows if row['key'] == only_task_key]
        if not rows:
            if total:
                return receipt(total, 'daily_ap_task_state')
            # A disabled global claim button proves there is no claimable AP
            # below the viewport either. A yellow button plus no visible AP is
            # ambiguous: never call that an empty/complete daily inventory.
            from core import color
            require(color.rgb_in_range(baas, 1148, 691, 185, 227, 184, 227, 188, 228)
                    and color.rgb_in_range(baas, 1142, 649, 185, 227, 184, 227, 188, 228),
                    'DAILY_AP_UNVERIFIED', 'Claimable rewards remain outside the recognized AP cards; the daily AP state is unknown.')
            return receipt(0, 'daily_no_claimable_ap', skipped=True)
        target = rows[0]
        if total + target['amount'] > max_ap:
            return receipt(total, 'daily_ap_limit', skipped=total == 0)
        require(target['key'] not in claimed and total + target['amount'] <= 150,
                'SOURCE_NOT_VERIFIED', 'The daily AP task did not change after its claim.')
        check(baas)
        baas.click(*target['point'], wait_over=True)
        # A reward dialog or a full-inventory notice alone does not prove AP.
        # The task must also cease to be claimable and delivery must match its
        # exact pre-read amount in automation.source().
        picture.co_detect(baas, 'reward_acquired', None, 'main_page_full-notice', None,
                          skip_first_screenshot=False, time_out=15)
        check(baas)
        baas.to_main_page()
        after = daily_page(baas)
        remaining = daily_ap_rows(after, lambda region: text(baas, after, region))
        require(not any(row['key'] == target['key'] for row in remaining),
                'SOURCE_NOT_VERIFIED', 'The daily AP task is still claimable; its reward was not verified.')
        total += target['amount']
        claimed.add(target['key'])
    raise PluginError('SOURCE_NOT_VERIFIED', 'Too many daily AP rewards appeared during collection.')


def cafe_ap(image, read):
    from .hoard_mail import _green_shape
    require(read((526, 124, 756, 168)) == '咖啡厅收益情况' and read((572, 200, 713, 240)) == '1号店',
            'SOURCE_NOT_VERIFIED', 'The cafe AP storage panel is not recognized.')
    require(_green_shape(image[266:313, 621:664]) is not None,
            'SOURCE_NOT_VERIFIED', 'The cafe AP storage icon is unreadable.')
    match = re.fullmatch(r'(\d{1,3})/(\d{1,3})', read((561, 420, 721, 456)))
    require(match is not None and 0 <= int(match[1]) <= int(match[2]) <= 999,
            'SOURCE_NOT_VERIFIED', 'The cafe AP storage amount is unreadable.')
    return int(match[1])


def collect_cafe(baas):
    from module import cafe_reward
    check(baas)
    cafe_reward.to_cafe(baas, True)
    cafe_reward.to_cafe_earning_status(baas)
    image = frame(baas)
    before = cafe_ap(image, lambda region: text(baas, image, region))
    if not before:
        return receipt(0, 'cafe_empty', skipped=True)
    require(text(baas, image, (573, 501, 706, 552)) == '领取', 'SOURCE_NOT_VERIFIED', 'The cafe collect button could not be verified.')
    check(baas)
    baas.click(640, 529, wait_over=True)
    check(baas)
    baas.to_main_page()
    cafe_reward.to_cafe(baas, True)
    cafe_reward.to_cafe_earning_status(baas)
    after = frame(baas)
    require(cafe_ap(after, lambda region: text(baas, after, region)) == 0,
            'SOURCE_NOT_VERIFIED', 'Cafe AP storage did not clear after collection.')
    return receipt(before, 'cafe_storage_cleared')


def collect_jjc(baas, settings):
    from core import picture
    from module.shop import tactical_challenge_shop as shop
    from module.shop.shop_utils import get_purchase_state, to_common_shop, goto_shop_by_name, buy
    check(baas)
    prices = baas.static_config.tactical_challenge_shop_price_list[baas.server]
    goods = list(baas.config.TacticalChallengeShopList)
    expected_ap = 30 if settings['jjc_mode'] == '30' else 90
    price = sum(row[1] * count for row, count in zip(prices, goods))
    require(price > 0, 'UNSUPPORTED_SHOP', 'The AP goods price is unavailable.')
    baas.to_main_page()
    to_common_shop(baas, True)
    goto_shop_by_name(baas, 5)
    def coins():
        image = frame(baas)
        value = text(baas, image, (751, 68, 884, 98)).replace(',', '')
        require(re.fullmatch(r'\d{1,7}', value) is not None, 'SOURCE_NOT_VERIFIED', 'The tactical shop coin balance is unreadable.')
        return int(value)
    total = 0
    for index in range(settings['jjc_refreshes'] + 1):
        before = coins()
        if before < price:
            return receipt(total, 'jjc_coin_balance', skipped=total == 0)
        check(baas)
        buy(baas, np.array(goods), shop_type='tactical_challenge_shop')
        state = get_purchase_state(baas)
        if state == 'shop_purchase-available':
            picture.co_detect(baas, None, None, 'shop_purchase-notice1', {'shop_menu': (1163, 659)}, True)
            check(baas)
            result = picture.co_detect(baas, 'reward_acquired', None, 'main_page_full-notice', {'shop_purchase-notice1': (754, 581)}, True)
            require(result in {'reward_acquired', 'main_page_full-notice'}, 'SOURCE_NOT_VERIFIED', 'The AP shop purchase receipt is unrecognized.')
            shop.to_shop_menu(baas)
            require(before - coins() == price, 'SOURCE_NOT_VERIFIED', 'The AP shop coin payment does not match the selected AP goods.')
            total += expected_ap
        elif state == 'shop_purchase-unavailable':
            return receipt(total, 'jjc_coin_balance', skipped=total == 0)
        else:
            require(state == 'shop_refresh-button-appear', 'SOURCE_NOT_VERIFIED', 'The AP shop state is unrecognized.')
        if index == settings['jjc_refreshes']:
            break
        before_refresh = coins()
        if before_refresh < 10 + price:
            break
        check(baas)
        require(shop.to_refresh(baas), 'SOURCE_NOT_VERIFIED', 'The AP shop refresh is unavailable.')
        check(baas)
        shop.confirm_refresh(baas)
        require(shop.wait_refresh_complete(baas, before_refresh, 10) is not None,
                'SOURCE_NOT_VERIFIED', 'The AP shop refresh payment could not be verified.')
    return receipt(total, 'jjc_coin_balance', skipped=total == 0)
