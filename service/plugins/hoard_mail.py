"""Verified, whole-letter AP mailbox operations for the host's CN layout.

No collect-all route is used. Identifiers are anonymous metadata digests, never
screen coordinates. Every withdrawal relocates its letter and verifies both the
complete mailbox multiset and character AP before reporting success.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
import time
import unicodedata

import cv2
import numpy as np

from .errors import PluginError, require

MAX_PAGES = 402  # Short overlapping gestures preserve even identical letters.
_VISUAL_CAPTURE_ERRORS = frozenset({
    'MAIL_SCREEN_UNREADABLE', 'MAIL_COUNT_UNREADABLE', 'MAIL_ITEM_UNCERTAIN',
    'MAIL_CLAIM_UNCERTAIN', 'MAIL_IDENTITY_UNREADABLE', 'MAIL_AMOUNT_UNREADABLE',
    'MAIL_EXPIRY_UNREADABLE', 'MAIL_LIST_UNREADABLE', 'AP_OCR_FAILED',
})


class _PrivateOcrLogger:
    """Mailbox text is sensitive and must never reach persistent host logs."""
    def info(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


_PRIVATE_OCR_LOGGER = _PrivateOcrLogger()


def _iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00', 'Z')


def _timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def _text(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(value)))


def expiry_bounds(text, observed_at):
    """Keep rounding uncertainty; a first '<1 hour' observation is urgent now."""
    text = _text(text)
    text = re.sub(r'^(?:领取期限|剩余时间|剩余)', '', text)
    if re.fullmatch(r'(?:不到|不足|少于|<)1小时|1小时以内', text):
        lower, upper, precision = 0, 3600, 'under-hour'
    else:
        match = re.fullmatch(r'(\d{1,3})(天|小时|分钟)', text)
        if match:
            value = int(match[1])
            unit = {'天': 86400, '小时': 3600, '分钟': 60}[match[2]]
            require(value <= 365, 'MAIL_EXPIRY_UNREADABLE', 'Mail expiry is outside the supported range.')
            # Client floor/ceil behavior is not established for every counter.
            lower, upper = max(0, value - 1) * unit, (value + 1) * unit
            precision = {'天': 'day', '小时': 'hour', '分钟': 'minute'}[match[2]]
        else:
            match = re.fullmatch(r'(\d{1,3}):(\d{2}):(\d{2})', text)
            require(match is not None and int(match[2]) < 60 and int(match[3]) < 60,
                    'MAIL_EXPIRY_UNREADABLE', 'Mail expiry could not be verified.')
            seconds = int(match[1]) * 3600 + int(match[2]) * 60 + int(match[3])
            lower, upper, precision = max(0, seconds - 1), seconds + 1, 'second'
    return {'expires_at': _iso(observed_at + lower), 'expires_before': _iso(observed_at + upper),
            'expiry_precision': precision, 'expiry_uncertain': True}


def _frame(image):
    require(isinstance(image, np.ndarray) and image.ndim == 3 and image.shape[2] == 3,
            'MAIL_SCREEN_UNREADABLE', 'Mailbox screenshot is unavailable.')
    height, width = image.shape[:2]
    require(abs(width / height - 16 / 9) < .02, 'MAIL_LAYOUT_UNSUPPORTED', 'Mailbox requires a landscape game frame.')
    return cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA) if (width, height) != (1280, 720) else image


def _green_shape(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (40, 90, 90), (80, 255, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    x, y, width, height = cv2.boundingRect(contour)
    if cv2.contourArea(contour) < 70 or not .35 <= width / height <= .85:
        return None
    silhouette = np.zeros((height, width), np.uint8)
    cv2.drawContours(silhouette, [contour - np.array([[[x, y]]])], 0, 255, -1)
    return contour, cv2.resize(silhouette, (64, 96), interpolation=cv2.INTER_NEAREST)


def _item_kind(image, y, reference):
    item = image[y:y + 50, 1000:1074]
    shape = _green_shape(item)
    if shape is None:
        hsv = cv2.cvtColor(item, cv2.COLOR_BGR2HSV)
        # A partly hidden/uncertain green item must not be silently excluded.
        require(cv2.countNonZero(cv2.inRange(hsv, (40, 90, 90), (80, 255, 255))) < 30,
                'MAIL_ITEM_UNCERTAIN', 'A mail attachment could not be distinguished from AP.')
        colored = cv2.cvtColor(image[y + 5:y + 45, 1018:1060], cv2.COLOR_BGR2HSV)
        # Loaded red books, gold credits and blue currencies all have strongly
        # saturated non-green ink. The pale attachment tile alone does not.
        ink = cv2.inRange(colored, (0, 120, 80), (179, 255, 255))
        ink = cv2.bitwise_and(ink, cv2.bitwise_not(cv2.inRange(colored, (40, 0, 0), (80, 255, 255))))
        components, _ = cv2.findContours(ink, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        require(cv2.countNonZero(ink) >= 200 and any(cv2.contourArea(component) >= 80 for component in components),
                'MAIL_ITEM_UNCERTAIN', 'A non-AP attachment is unsupported or has not finished loading.')
        return 'other'
    contour, mask = shape
    ref_contour, ref_mask = reference
    intersection = np.count_nonzero((mask > 0) & (ref_mask > 0))
    union = np.count_nonzero((mask > 0) | (ref_mask > 0))
    require(intersection / max(1, union) >= .70 and
            cv2.matchShapes(contour, ref_contour, cv2.CONTOURS_MATCH_I1, 0) <= .16,
            'MAIL_ITEM_UNCERTAIN', 'A green mail attachment does not match the AP icon.')
    return 'ap'


def parse_mail_frame(image, read_text, observed_at):
    """Parse full visible rows; OCR is region-bound and cannot supply click positions."""
    image = _frame(image)
    require(_text(read_text((100, 0, 190, 45), 'title')) == '邮箱',
            'MAIL_SCREEN_UNREADABLE', 'The mailbox screen could not be verified.')
    require(_text(read_text((20, 112, 180, 158), 'tab')) == '未领取',
            'MAIL_SCREEN_UNREADABLE', 'The unclaimed-mail tab could not be verified.')
    selected = cv2.cvtColor(image[113:157, 20:180], cv2.COLOR_BGR2HSV)
    require(cv2.countNonZero(cv2.inRange(selected, (18, 100, 130), (40, 255, 255))) > 80,
            'MAIL_SCREEN_UNREADABLE', 'The unclaimed-mail tab is not selected.')
    count = re.fullmatch(r'(\d{1,3})/200', _text(read_text((1158, 55, 1244, 91), 'count')))
    require(count is not None and int(count[1]) <= 200,
            'MAIL_COUNT_UNREADABLE', 'The full mailbox count could not be verified.')
    ap = re.fullmatch(r'(\d{1,3})/(\d{1,3})', _text(read_text((533, 5, 632, 45), 'ap')))
    require(ap is not None and int(ap[1]) <= 999, 'AP_OCR_FAILED', 'Mailbox character AP could not be verified.')
    reference = _green_shape(image[5:45, 499:532])
    require(reference is not None, 'MAIL_ITEM_UNCERTAIN', 'The header AP icon could not be verified.')
    hsv = cv2.cvtColor(image[100:610, 1076:1243], cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (75, 70, 145), (115, 255, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    buttons = sorted((100 + y, x, width, height) for contour in contours
                     for x, y, width, height in [cv2.boundingRect(contour)]
                     if 130 <= width <= 165 and 55 <= height <= 72 and cv2.contourArea(contour) >= 6500)
    rows = []
    for y, _x, _width, _height in buttons:
        if y - 60 < 102 or y + 72 > 610:
            continue  # Do not infer metadata from a clipped row.
        require(_text(read_text((1095, y + 12, 1215, y + 50), 'claim')) == '领取',
                'MAIL_CLAIM_UNCERTAIN', 'An individual mail claim button could not be verified.')
        title = _text(read_text((430, y - 56, 1005, y - 18), 'subject'))
        sender = _text(read_text((1110, y - 54, 1237, y - 20), 'sender'))
        received = _text(read_text((525, y + 1, 870, y + 29), 'received'))
        date = re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日', received)
        require(len(title) >= 4 and len(sender) >= 2 and date is not None,
                'MAIL_IDENTITY_UNREADABLE', 'A mail subject, sender or received date is unreadable.')
        try:
            received_at = datetime(int(date[1]), int(date[2]), int(date[3])).date().isoformat()
        except ValueError:
            raise PluginError('MAIL_IDENTITY_UNREADABLE', 'A mail received date is invalid.') from None
        kind = _item_kind(image, y, reference)
        # A faint multiplication mark on other currencies is immaterial to AP
        # recognition; AP still requires the icon and its complete xN label.
        pattern = r'[xX×](\d{1,7})' if kind == 'ap' else r'[xX×]?(\d{1,7})'
        quantity = re.fullmatch(pattern, _text(read_text((1025, y + 41, 1073, y + 66), 'amount')))
        require(quantity is not None and 0 < int(quantity[1]) <= 9999999,
                'MAIL_AMOUNT_UNREADABLE', 'A mail attachment quantity could not be verified.')
        amount = int(quantity[1])
        expiry_text = _text(read_text((520, y + 29, 875, y + 57), 'expiry'))
        expiry = expiry_bounds(expiry_text, observed_at)
        identity = _digest([title, sender, received_at, kind, amount])
        rows.append({'identity': identity, 'amount': amount, 'kind': kind, 'received_at': received_at,
                     **expiry, '_page_key': (identity, expiry_text), '_claim': (1155, y + 32)})
    require(int(count[1]) == 0 or rows, 'MAIL_LIST_UNREADABLE', 'No complete mail rows could be verified.')
    return {'count': int(count[1]), 'ap': int(ap[1]), 'rows': rows}


def _check(baas):
    require(bool(baas.flag_run), 'AUTOMATION_STOPPED', 'Automation was stopped.')


def _pause(baas, sleep, seconds=.2):
    _check(baas)
    sleep(seconds)
    _check(baas)


def _ocr_crop(image, field):
    if field == 'expiry':
        # The orange countdown is small and has little luminance contrast.
        # Isolate its ink instead of guessing a digit dropped by OCR scoring.
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 110, 120), (30, 255, 255))
        mask |= cv2.inRange(hsv, (170, 110, 120), (179, 255, 255))
        points = cv2.findNonZero(mask)
        if points is not None:
            x, y, width, height = cv2.boundingRect(points)
            ink = 255 - mask[y:y + height, x:x + width]
            image = cv2.copyMakeBorder(ink, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255)
            image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return image


def _capture(baas, clock):
    _check(baas)
    captured_at = clock()
    image = _frame(baas.get_screenshot_array())
    observed_count = None

    def read(region, field):
        nonlocal observed_count
        _check(baas)
        x1, y1, x2, y2 = region
        try:
            value = baas.ocr.ocr_for_single_line('zh-cn', log_info='mailbox', origin_image=_ocr_crop(image[y1:y2, x1:x2], field),
                                               pass_method=1, filter_score=.8, _logger=_PRIVATE_OCR_LOGGER)
        except Exception:
            raise PluginError('MAIL_OCR_UNAVAILABLE', 'The mailbox could not be recognized safely.') from None
        if field == 'count':
            match = re.fullmatch(r'(\d{1,3})/200', _text(value))
            if match is not None and int(match[1]) <= 200:
                observed_count = int(match[1])
        return value

    try:
        return parse_mail_frame(image, read, captured_at)
    except PluginError as error:
        # Preserve only the verified numeric count, even if a later row crop is
        # moving. A failed frame cannot conceal mail arriving or expiring.
        if observed_count is not None:
            error.mailbox_count = observed_count
        raise


def _same_row(first, second):
    if any(first[key] != second[key] for key in ('identity', 'kind', 'amount')):
        return False
    # Countdown labels can cross a second/hour/day boundary while OCR runs.
    # Their conservative time intervals must still describe the same deadline.
    return max(_timestamp(first['expires_at']), _timestamp(second['expires_at'])) <= min(
        _timestamp(first['expires_before']), _timestamp(second['expires_before']))


def _same_page(first, second):
    return (first['count'] == second['count'] and
            len(first['rows']) == len(second['rows']) and
            all(_same_row(a, b) and abs(a['_claim'][1] - b['_claim'][1]) <= 2
                for a, b in zip(first['rows'], second['rows'])))


def _stable_page(baas, clock, sleep):
    previous, count = None, None
    for index in range(5):
        if index:
            _pause(baas, sleep)
        _check(baas)
        try:
            current = _capture(baas, clock)
        except PluginError as error:
            if error.code not in _VISUAL_CAPTURE_ERRORS:
                raise
            observed_count = getattr(error, 'mailbox_count', None)
            if observed_count is not None:
                require(count is None or count == observed_count,
                        'MAIL_LIST_CHANGED', 'Mail arrived or expired during recognition; rescan before continuing.')
                count = observed_count
            previous = None
            continue
        require(count is None or count == current['count'],
                'MAIL_LIST_CHANGED', 'Mail arrived or expired during recognition; rescan before continuing.')
        count = current['count']
        if previous is not None and _same_page(previous, current):
            return current
        previous = current
    raise PluginError('MAIL_LIST_CHANGED', 'The mailbox did not settle during recognition; rescan before continuing.')


def _swipe(baas, down, sleep):
    _check(baas)
    # Less than the 150px row pitch, slowly: a repeated-looking page cannot skip
    # an entire identical row and masquerade as the same scroll boundary.
    baas.swipe(850, 260 if down else 470, 850, 360 if down else 370, duration=.75)
    _pause(baas, sleep, .35)


def _top(baas, clock, sleep):
    page = _stable_page(baas, clock, sleep)
    for _ in range(MAX_PAGES):
        _swipe(baas, True, sleep)
        next_page = _stable_page(baas, clock, sleep)
        require(page['count'] == next_page['count'], 'MAIL_LIST_CHANGED', 'Mail arrived or expired while scanning.')
        if _same_page(page, next_page):
            return next_page
        page = next_page
    raise PluginError('MAIL_LIST_INCOMPLETE', 'The top of the mailbox could not be established.')


def _merge_rows(rows, page, count):
    if not rows:
        return list(page)
    overlaps = [size for size in range(1, min(len(rows), len(page)) + 1)
                if all(_same_row(a, b) for a, b in zip(rows[-size:], page[:size]))
                and len(rows) + len(page) - size <= count]
    if len(overlaps) > 1:
        # Equal letters retain their multiplicity. A short upward drag moves
        # every overlapping row upward by the same sub-row distance.
        overlaps = [size for size in overlaps
                    for shifts in [[b['_claim'][1] - a['_claim'][1]
                                    for a, b in zip(rows[-size:], page[:size])]]
                    if all(-140 <= shift < -2 for shift in shifts) and max(shifts) - min(shifts) <= 3]
    require(len(overlaps) == 1, 'MAIL_LIST_AMBIGUOUS', 'Mailbox page overlap is ambiguous; no mail was claimed.')
    # Refresh overlap positions for the next page while preserving the earlier
    # conservative deadline; OCR processing never grants a letter extra time.
    size = overlaps[0]
    refreshed = [{**new, 'expires_at': min(old['expires_at'], new['expires_at'], key=_timestamp),
                  'expires_before': min(old['expires_before'], new['expires_before'], key=_timestamp)}
                 for old, new in zip(rows[-size:], page[:size])]
    return rows[:-size] + refreshed + page[size:]


def _snapshot(rows, observed_at, count):
    occurrences = Counter()
    identities = [{'identity': row['identity'], 'kind': row['kind'], 'amount': row['amount']} for row in rows]
    fingerprint = _digest(identities)
    parcels = []
    for row in rows:
        identity = row['identity']
        occurrence = occurrences[identity]
        occurrences[identity] += 1
        identifier = _digest([identity, occurrence, fingerprint])
        if row['kind'] == 'ap':
            parcels.append({key: value for key, value in row.items() if not key.startswith('_') and key != 'kind'} |
                           {'id': identifier, 'occurrence': occurrence, 'source': 'mailbox-ocr', 'verified': True})
    require(len(rows) == count, 'MAIL_LIST_INCOMPLETE', 'The mailbox count does not match all recognized letters.')
    return {'complete': True, 'observed_at': _iso(observed_at), 'mailbox_count': count,
            'parcels': parcels, 'total_ap': sum(row['amount'] for row in parcels),
            'rows': identities, 'fingerprint': fingerprint}


def _open(baas, sleep):
    _check(baas)
    require(baas.server == 'CN', 'MAIL_LAYOUT_UNSUPPORTED', 'Automatic mailbox recognition currently supports the verified CN layout.')
    from module.mail import to_mail
    baas.to_main_page()
    _check(baas)
    to_mail(baas)
    _check(baas)
    # The game remembers the history tab. Navigation has verified mail_menu;
    # select only the unclaimed tab before the parser verifies its active state.
    baas.click(100, 137, wait_over=True)
    _pause(baas, sleep, .4)


def scan_mailbox(baas, *, clock=time.time, sleep=time.sleep):
    _open(baas, sleep)
    page = _top(baas, clock, sleep)
    count, rows = page['count'], list(page['rows'])
    for _ in range(MAX_PAGES):
        _swipe(baas, False, sleep)
        next_page = _stable_page(baas, clock, sleep)
        require(next_page['count'] == count, 'MAIL_LIST_CHANGED', 'Mail arrived or expired while scanning.')
        if _same_page(page, next_page):
            return _snapshot(rows, clock(), count)
        rows = _merge_rows(rows, next_page['rows'], count)
        page = next_page
    raise PluginError('MAIL_LIST_INCOMPLETE', 'The end of the mailbox could not be established.')


def _row_counts(snapshot):
    require(snapshot.get('complete') is True and len(snapshot.get('rows', [])) == snapshot.get('mailbox_count'),
            'MAIL_LIST_INCOMPLETE', 'A complete verified mailbox is required.')
    return Counter(row['identity'] for row in snapshot['rows'])


def verify_mail_delivery(before, after, expected_amount):
    old, new = _row_counts(before), _row_counts(after)
    require(isinstance(expected_amount, int) and not isinstance(expected_amount, bool) and expected_amount >= 0,
            'MAIL_DELIVERY_UNVERIFIED', 'The expected delivered AP amount is invalid.')
    if expected_amount == 0:
        require(old == new, 'MAIL_DELIVERY_UNVERIFIED', 'Unexpected mail changed during a direct AP reward.')
        return []
    require(not old - new, 'MAIL_DELIVERY_UNVERIFIED', 'A previous mail disappeared while checking delivery.')
    added = new - old
    require(sum(added.values()) > 0, 'MAIL_DELIVERY_UNVERIFIED', 'No new mail was observed after the reward.')
    non_ap = {row['identity'] for row in after['rows'] if row['kind'] != 'ap'}
    require(not (set(added) & non_ap), 'MAIL_DELIVERY_UNVERIFIED', 'Unexpected non-AP mail arrived with the reward.')
    candidates = []
    remaining = Counter(added)
    for parcel in reversed(after['parcels']):
        if remaining[parcel['identity']]:
            candidates.append(parcel)
            remaining[parcel['identity']] -= 1
    require(sum(parcel['amount'] for parcel in candidates) == expected_amount and not +remaining,
            'MAIL_DELIVERY_UNVERIFIED', 'New AP mail does not match the expected reward amount.')
    return list(reversed(candidates))


def _locate(baas, target, snapshot, clock, sleep):
    page = _top(baas, clock, sleep)
    rows = []
    expected = [row['identity'] for row in snapshot['rows']]
    for _ in range(MAX_PAGES):
        require(page['count'] == snapshot['mailbox_count'], 'MAIL_LIST_CHANGED', 'The mailbox changed before claiming.')
        rows = _merge_rows(rows, page['rows'], page['count'])
        require([row['identity'] for row in rows] == expected[:len(rows)],
                'MAIL_LIST_CHANGED', 'Mail identities changed before claiming.')
        occurrences = Counter()
        for index, row in enumerate(rows):
            occurrence = occurrences[row['identity']]
            occurrences[row['identity']] += 1
            if _digest([row['identity'], occurrence, snapshot['fingerprint']]) == target['id']:
                visible_index = index - (len(rows) - len(page['rows']))
                require(0 <= visible_index < len(page['rows']) and
                        _same_row(row, page['rows'][visible_index]) and
                        row['amount'] == target['amount'] and row['kind'] == 'ap',
                        'MAIL_CLAIM_UNCERTAIN', 'The selected AP letter cannot be uniquely located.')
                return page['rows'][visible_index]['_claim'], page['ap']
        _swipe(baas, False, sleep)
        page = _stable_page(baas, clock, sleep)
    raise PluginError('MAIL_CLAIM_UNCERTAIN', 'The selected AP letter was not found.')


def claim_ap_mail(baas, parcel_id, *, read_ap, clock=time.time, sleep=time.sleep):
    _check(baas)
    before_ap = read_ap(baas)
    require(isinstance(before_ap, int) and not isinstance(before_ap, bool) and 0 <= before_ap <= 999,
            'AP_OCR_FAILED', 'Current AP must be verified before claiming a letter.')
    _check(baas)
    before = scan_mailbox(baas, clock=clock, sleep=sleep)
    target = next((parcel for parcel in before['parcels'] if parcel['id'] == parcel_id), None)
    require(target is not None, 'MAIL_LIST_CHANGED', 'The selected AP letter is no longer present.')
    require(0 < target['amount'] <= 999 and 0 <= before_ap <= 999 - target['amount'],
            'MAIL_HEADROOM_REQUIRED', 'Create enough AP headroom for this entire letter before claiming.')
    point, fresh_ap = _locate(baas, target, before, clock, sleep)
    require(fresh_ap == before_ap, 'AP_CHANGED', 'Character AP changed while locating the letter; rescan first.')
    require(datetime.fromisoformat(target['expires_before'].replace('Z', '+00:00')).timestamp() > clock(),
            'MAIL_EXPIRED', 'The selected letter may already have expired.')
    _check(baas)
    baas.click(*point, wait_over=True)
    _pause(baas, sleep, .4)
    # Host navigation dismisses reward/full-inventory notices without selecting
    # another letter. Cancellation propagates before any additional interaction.
    after_ap = read_ap(baas)
    require(isinstance(after_ap, int) and not isinstance(after_ap, bool) and 0 <= after_ap <= 999,
            'AP_OCR_FAILED', 'Character AP could not be verified after the claim.')
    _check(baas)
    after = scan_mailbox(baas, clock=clock, sleep=sleep)
    expected = _row_counts(before)
    expected[target['identity']] -= 1
    require(+expected == _row_counts(after) and after['mailbox_count'] == before['mailbox_count'] - 1,
            'MAIL_CLAIM_UNVERIFIED', 'The selected letter did not disappear, or other mail changed.')
    require(after_ap - before_ap == target['amount'], 'MAIL_CLAIM_UNVERIFIED', 'Character AP did not increase by the full letter amount.')
    return {'verified': True, 'claimed': True, 'id': parcel_id, 'amount': target['amount'],
            'before_ap': before_ap, 'after_ap': after_ap, 'before': before, 'after': after, 'mailbox': after}
