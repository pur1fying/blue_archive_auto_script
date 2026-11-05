"""Closed host adapters for shipped automation tools.

No entrypoint from an installed package is imported into the BAAS process.
Automation runs under the exact same owned-thread gate as single host tasks.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import importlib
import math
import re
import time

from .errors import PluginError, require
from .hoard_plan import HARD_CAP, MARGIN, build_hoard_plan, instant, public_hoard_plan, server_day, validate_mail_snapshot

HOST_ACTIONS = {
    'baas.hoard-ap': frozenset({'plan', 'scan_mail', 'start'}),
    'baas.auto-push': frozenset({'normal', 'hard', 'story', 'activity_mission',
                                'activity_story', 'activity_challenge', 'current_stage', 'current_story'}),
}
TASKS = {'normal': 'explore_normal_task', 'hard': 'explore_hard_task', 'story': 'main_story',
         'activity_mission': 'explore_activity_mission', 'activity_story': 'explore_activity_story',
         'activity_challenge': 'explore_activity_challenge'}


class ConfigOverlay:
    """Ephemeral task parameters; persistent inventory writes still reach disk."""
    def __init__(self, original, overrides):
        self._original = original
        self._overrides = deepcopy(overrides)
        self.config = deepcopy(original.config)
        for key, value in overrides.items():
            setattr(self.config, key, deepcopy(value))

    def __getattr__(self, name):
        return getattr(self._original, name)

    def get(self, key, default=None):
        return deepcopy(self._overrides[key]) if key in self._overrides else self._original.get(key, default)

    def set(self, key, value):
        if key in self._overrides:
            self._overrides[key] = deepcopy(value)
            setattr(self.config, key, deepcopy(value))
        else:
            self._original.set(key, value)
            setattr(self.config, key, deepcopy(value))

    update = set

    def __getitem__(self, key):
        return self.get(key)


@contextmanager
def configuration_overlay(baas, overrides):
    original_set, original_config = baas.config_set, baas.config
    overlay = ConfigOverlay(original_set, overrides)
    baas.config_set = overlay
    baas.config = deepcopy(original_config)
    for key, value in overrides.items():
        setattr(baas.config, key, deepcopy(value))
    try:
        yield
    finally:
        baas.config_set, baas.config = original_set, original_config


def validate_auto_settings(settings):
    for key, hard in (('normal_stages', False), ('hard_stages', True)):
        entries = settings[key].split(',')
        require(0 < len(entries) <= 100 and all(re.fullmatch(r'\s*\d{1,2}(?:-' + ('[1-3]' if hard else '[1-5A]') + r')?\s*', item)
                                                  for item in entries),
                'INVALID_MISSIONS', 'Use comma-separated chapters or missions, such as 12,13-1,13-2.')
    story = settings['story_episodes'].strip()
    require(not story or all(re.fullmatch(r'[1-9]\d?', item.strip()) for item in story.split(',')),
            'INVALID_EPISODES', 'Use a comma-separated ordered list of positive story episode numbers.')
    if settings['team_method'] != 'profile':
        require(bool(settings['team_plan']), 'TEAM_PLAN_REQUIRED', 'Supply a team attribute plan for the selected team source.')
        if settings['team_method'] == 'side':
            require(len(settings['team_plan']) == 1 and len(settings['team_plan'][0]) <= 4,
                    'INVALID_TEAMS', 'Side teams use exactly one group with at most four formation slots.')
        require(any(attribute != 'unused' for group in settings['team_plan'] for attribute in group),
                'INVALID_TEAMS', 'At least one formation must have a damage attribute.')


def _activity_supported(baas, action):
    require(bool(baas.current_game_activity), 'UNSUPPORTED_ACTIVITY', 'The backend has no supported current activity.')
    # current_game_activity is selected by the host, never a plugin module path.
    try:
        module = importlib.import_module('module.activities.' + baas.current_game_activity)
        function = 'explore_' + action.split('_', 1)[1] if action.startswith('activity_') else 'sweep'
        require(callable(getattr(module, function, None)), 'UNSUPPORTED_ACTIVITY', 'This activity does not implement the requested task.')
    except ImportError:
        raise PluginError('UNSUPPORTED_ACTIVITY', 'This activity has no installed automation route.') from None


def run_auto_push(baas, action, settings):
    validate_auto_settings(settings)
    overrides = {'explore_normal_task_list': settings['normal_stages'],
                 'explore_hard_task_list': settings['hard_stages'],
                 'main_story_regions': settings['story_episodes'],
                 'explore_task_use_simple_mode': settings['simple_mode'], 'manual_boss': settings['manual_boss']}
    if settings['team_method'] != 'profile':
        method = settings['team_method']
        overrides.update(choose_team_method=method,
                         **{('side_team_attribute' if method == 'side' else 'preset_team_attribute'): settings['team_plan']})
    with configuration_overlay(baas, overrides):
        if action.startswith('activity_'):
            _activity_supported(baas, action)
        if action.startswith('current_'):
            from .automation_current import push_current_stage, push_current_story
            function = push_current_stage if action == 'current_stage' else push_current_story
            completed = function(baas)
        else:
            completed = baas.solve(TASKS[action])
        require(completed is not False, 'DEVICE_TASK_FAILED', 'The host route did not finish successfully.')
    return {'completed': True, 'action': action, 'settings_applied_to_profile': False}


def _cn_ap_panel_clear(image):
    """The verified CN home AP plate is white; achievement toasts dim it."""
    import numpy as np
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        return False
    height, width = image.shape[:2]
    if not height or abs(width / height - 16 / 9) >= .02:
        return False
    def white_fraction(region):
        x1, y1, x2, y2 = region
        patch = image[int(y1 * height / 720):int(y2 * height / 720),
                      int(x1 * width / 1280):int(x2 * width / 1280)]
        return bool(patch.size) and float(np.mean(np.all(patch >= 200, axis=2)))
    return (white_fraction((485, 23, 586, 54)) >= .65
            and white_fraction((485, 20, 580, 25)) >= .8
            and white_fraction((485, 50, 580, 54)) >= .8)


def _read_ap(baas, *, clock=time.monotonic, sleep=time.sleep):
    """Read AP after transient overlays, without replaying any resource action."""
    _running(baas)
    baas.to_main_page()
    cn = baas.server == 'CN'
    region = (485, 23, 586, 54) if cn else (536, 26, 619, 44)
    deadline = clock() + 5
    for _ in range(20 if cn else 1):
        _running(baas)
        baas.update_screenshot_array()
        if not cn or _cn_ap_panel_clear(getattr(baas, 'latest_img_array', None)):
            text = baas.ocr.get_region_res(baas, region, 'en-us', 'AP', '0123456789/')
            match = re.fullmatch(r'\s*(\d{1,3})(?:\s*/\s*\d{1,3})?\s*', str(text))
            if match is not None and int(match[1]) <= 999:
                return int(match[1])
        remaining = deadline - clock()
        if not cn or remaining <= 0:
            break
        _running(baas)
        sleep(min(.25, remaining))
    raise PluginError('AP_OCR_FAILED', 'Current AP could not be verified; automation stopped.')



def _sweep_rows(baas, normal):
    priority = getattr(baas.config, 'mainlinePriority' if normal else 'hardPriority', None)
    if priority is None:
        # Compatibility for older host adapters; current Config always has the
        # authoritative priority list. Never refresh or consume its disk queue.
        return deepcopy(getattr(baas.config, 'unfinished_normal_tasks' if normal else 'unfinished_hard_tasks', []))
    entries = priority.split(',') if isinstance(priority, str) else priority
    require(isinstance(entries, list), 'CLEAR_ROUTE_REQUIRED', 'Configure a valid sweep priority list first.')
    maximum = getattr(baas.static_config, 'explore_normal_task_region_range' if normal else 'explore_hard_task_region_range')[1]
    rows = []
    for entry in entries:
        match = re.fullmatch(r'\s*([1-9]\d?)-([1-5])-([1-9]\d*|max)\s*', str(entry))
        require(match is not None and int(match[1]) <= maximum and (normal or int(match[2]) <= 3),
                'CLEAR_ROUTE_REQUIRED', 'The selected sweep priority contains an unsupported stage or count.')
        rows.append([int(match[1]), int(match[2]), match[3]])
    return rows


def _run_host_task_once(baas, task):
    """Resource actions must never replay the legacy solver's three retries."""
    from core.Baas_thread import func_dict
    from core.exception import FunctionCallTimeout, PackageIncorrect
    _running(baas)
    require(task in {'normal_task', 'hard_task', 'activity_sweep', 'clear_special_task_power', 'scrimmage', 'tactical_challenge_shop'},
            'UNSUPPORTED_TASK', 'This task is not a bounded AP resource route.')
    try:
        return func_dict[task](baas)
    except (FunctionCallTimeout, PackageIncorrect):
        raise PluginError('DEVICE_TASK_INTERRUPTED', 'The resource route was interrupted; its actions will not be replayed.') from None


def _clear_ap(baas, task, target):
    """Consume bounded runs of the chosen profile route, measuring each pass."""
    current = _read_ap(baas)
    for _ in range(5):
        _running(baas)
        if current <= target:
            return current
        cost = 10 if task == 'normal_task' else 20 if task == 'hard_task' else 15 if task == 'scrimmage' else 40 if task == 'clear_special_task_power' else 10
        if task == 'activity_sweep':
            _activity_supported(baas, 'sweep')
            from module.activities.activity_utils import get_stage_data, preprocess_activity_region
            stages = preprocess_activity_region(baas.config.activity_sweep_task_number)
            require(len(stages) == 1, 'CLEAR_ROUTE_REQUIRED', 'Select exactly one activity mission for bounded AP spending.')
            data = get_stage_data(baas)
            costs = data.get('sweep_ap_cost_mission', [])
            require(0 <= stages[0] < len(costs) and 1 <= costs[stages[0]] <= 100,
                    'UNSUPPORTED_ACTIVITY', 'The activity has no declared AP cost for this mission.')
            cost = costs[stages[0]]
        count = math.ceil((current - target) / cost)
        overrides = {'purchase_scrimmage_ticket_times': 0}
        if task in {'normal_task', 'hard_task'}:
            key = 'unfinished_normal_tasks' if task == 'normal_task' else 'unfinished_hard_tasks'
            configured = _sweep_rows(baas, task == 'normal_task')
            require(bool(configured), 'CLEAR_ROUTE_REQUIRED', 'Configure a sweep stage for the selected spending task first.')
            rows, remaining = [], count
            for row in configured:
                take = min(remaining, 3 if task == 'hard_task' else remaining)
                rows.append([row[0], row[1], take])
                remaining -= take
                if remaining <= 0:
                    break
            overrides[key] = rows
        elif task == 'clear_special_task_power':
            values = str(baas.config.special_task_times).split(',')
            selected = next((i for i, value in enumerate(values) if value.strip() not in {'0', ''}), None)
            require(selected is not None, 'CLEAR_ROUTE_REQUIRED', 'Configure a commission type before spending AP.')
            overrides['special_task_times'] = ','.join(str(count if i == selected else 0) for i in range(2))
        elif task == 'scrimmage':
            values = str(baas.config.scrimmage_times).split(',')
            selected = next((i for i, value in enumerate(values) if value.strip() not in {'0', ''}), None)
            require(selected is not None, 'CLEAR_ROUTE_REQUIRED', 'Configure a scrimmage school before spending AP.')
            overrides['scrimmage_times'] = ','.join(str(count if i == selected else 0) for i in range(3))
        else:
            _activity_supported(baas, 'sweep')
            # Legacy activity_sweep interprets >50 as max/all current AP.
            # Keep each measured batch below that implicit mode switch.
            overrides['activity_sweep_times'] = str(min(50, count))
        with configuration_overlay(baas, overrides):
            _running(baas)
            require(_run_host_task_once(baas, task) is not False, 'DEVICE_TASK_FAILED', 'The selected spending route failed.')
        after = _read_ap(baas)
        require(after < current, 'CLEAR_NO_PROGRESS', 'The spending route did not reduce AP; automation stopped.')
        current = after
    require(current <= target, 'CLEAR_INCOMPLETE', 'The available sweep stages or tickets could not create enough AP headroom.')
    return current


_PUBLIC_MAIL_FIELDS = ('complete', 'observed_at', 'mailbox_count', 'parcels', 'total_ap', 'fingerprint')


def _public_mail(snapshot):
    # The internal roster includes anonymous non-AP attachments for verification;
    # it is not needed in the client forecast or job history.
    result = {key: deepcopy(snapshot[key]) for key in _PUBLIC_MAIL_FIELDS if key != 'parcels'}
    result['parcels'] = [{**{key: row[key] for key in ('amount', 'expires_at', 'expires_before', 'expiry_precision', 'received_at', 'occurrence')},
                          'id': row['id'][:32]} for row in snapshot['parcels']]
    return result


def _mail_adapter(mail_api):
    if mail_api is None:
        from . import hoard_mail
        return hoard_mail
    return mail_api


def _running(baas):
    require(bool(baas.flag_run), 'AUTOMATION_STOPPED', 'Automation was stopped.')


def scan_hoard_mail(baas, settings=None, *, clock=time.time, sleep=time.sleep, mail_api=None):
    """A fresh anonymous inventory; called only inside the host ownership gate."""
    _running(baas)
    snapshot = _mail_adapter(mail_api).scan_mailbox(baas, clock=clock, sleep=sleep)
    validate_mail_snapshot(snapshot)
    actual = _read_ap(baas)
    _running(baas)
    return {'kind': 'hoard_mail_scan', 'inventory_kind': 'verified', 'character_ap': actual,
            **_public_mail(snapshot)}


def _collect_hoard_source(baas, action, settings):
    from . import hoard_sources
    _running(baas)
    if action == 'daily':
        return _collect_daily_ap(baas, max_ap=settings['daily_ap'])
    if action == 'free':
        return hoard_sources.collect_free(baas)
    if action == 'club':
        return hoard_sources.collect_club(baas)
    if action == 'cafe':
        return hoard_sources.collect_cafe(baas)
    prices = baas.static_config.tactical_challenge_shop_price_list[baas.server]
    goods = [0] * len(prices)
    indices = {str(row[0]).upper().replace(' ', ''): index for index, row in enumerate(prices)}
    require('30AP' in indices and '60AP' in indices, 'UNSUPPORTED_SHOP', 'This server shop has no identifiable AP goods.')
    goods[indices['30AP']] = 1
    goods[indices['60AP']] = int(settings['jjc_mode'] == '30_60')
    with configuration_overlay(baas, {'TacticalChallengeShopList': goods, 'TacticalChallengeShopRefreshTime': settings['jjc_refreshes']}):
        return hoard_sources.collect_jjc(baas, settings)


def _collect_daily_ap(baas, *, max_ap=150):
    from .hoard_sources import collect_daily
    return collect_daily(baas, max_ap=max_ap)


def _free_ap_available(baas):
    from .hoard_sources import free_available
    return free_available(baas)


def run_hoard(baas, settings, *, clock=time.time, sleep=time.sleep, mail_api=None):
    """Run a forecast using fresh whole-parcel inventory after every delivery.

    Forecast 24-hour overflow lifetimes never drive live mail actions. Only a
    scanned expiry interval can schedule a withdrawal, and source-day receipts
    prevent new mail or a rescan from replaying an already collected source.
    """
    api = _mail_adapter(mail_api)
    actual = _read_ap(baas)
    # Reject premium before scanning or claiming any source, even when called
    # directly rather than via ServiceRuntime's preflight.
    preflight = build_hoard_plan({**settings, 'current_ap': actual, 'mail': []},
                                now=datetime.fromtimestamp(clock(), timezone.utc))
    require(preflight['executable'], 'MANUAL_STEP_REQUIRED', 'Complete the explicitly manual premium purchases before starting.')
    snapshot = None
    historical_deadlines, historical_upper = {}, {}
    completed, completed_sources, blocked_source_days = [], set(), set()

    def observe():
        _running(baas)
        fresh = api.scan_mailbox(baas, clock=clock, sleep=sleep)
        adopt(fresh)
        return fresh

    def adopt(fresh, *, removed_id=None):
        nonlocal snapshot, historical_deadlines, historical_upper
        validate_mail_snapshot(fresh)
        old = [row for row in snapshot['parcels'] if row['id'] != removed_id] if snapshot else []
        previous = Counter(row['identity'] for row in old)
        current = Counter(row['identity'] for row in fresh['parcels'])
        require(not previous - current, 'MAIL_LIST_CHANGED', 'An AP parcel disappeared without a verified withdrawal.')
        deadlines, uppers = {}, {}
        for identity in current:
            old_rows = sorted((row for row in old if row['identity'] == identity), key=lambda row: row['occurrence'])
            new_rows = sorted((row for row in fresh['parcels'] if row['identity'] == identity), key=lambda row: row['occurrence'])
            for index, row in enumerate(new_rows):
                lower, upper = instant(row['expires_at']).timestamp(), instant(row['expires_before']).timestamp()
                if len(old_rows) == len(new_rows):
                    # After a verified single removal, occurrence shifts are
                    # known. Keep each surviving letter's own expiry history.
                    candidates = old_rows[index:index + 1]
                else:
                    # Newly inserted identical mail cannot always be assigned
                    # uniquely. Only overlapping expiry intervals share a
                    # conservative bound; a distant long-lived copy does not.
                    candidates = [item for item in old_rows
                                  if historical_deadlines[item['id']] < upper
                                  and lower < historical_upper[item['id']]]
                if candidates:
                    prior_low = min(historical_deadlines[item['id']] for item in candidates)
                    prior_high = max(historical_upper[item['id']] for item in candidates)
                    require(prior_low < upper and lower < prior_high, 'MAIL_LIST_CHANGED', 'An existing mail expiry changed incompatibly.')
                    lower, upper = min(lower, prior_low), min(upper, prior_high)
                deadlines[row['id']], uppers[row['id']] = lower, upper
        historical_deadlines, historical_upper, snapshot = deadlines, uppers, fresh

    def record(action, before, after, amount=0, **metadata):
        _running(baas)
        completed.append({'action': action, 'at': datetime.fromtimestamp(clock(), timezone.utc).isoformat(),
                          'verified': True, 'ap': after, 'ap_before': before, 'ap_after': after,
                          'amount': int(amount), 'mail_ap': snapshot['total_ap'], **metadata})

    def clear(limit, reason):
        before = _read_ap(baas)
        if before <= limit:
            return before
        _running(baas)
        after = _clear_ap(baas, settings['spend_task'], limit)
        observe()  # A route may cross a day reset or allow new mail to arrive.
        record('clear', before, after, before - after, reason=reason)
        return after

    def parcel_deadline(row):
        return min(instant(row['expires_at']).timestamp(), historical_deadlines[row['id']]) - MARGIN.total_seconds()

    def claim_one(row):
        identity, amount = row['identity'], row['amount']
        clear(HARD_CAP - amount, 'mail_headroom')
        # Clearing can change the whole mailbox roster and invalidate locators.
        fresh = observe()
        candidates = [item for item in fresh['parcels'] if item['identity'] == identity and item['amount'] == amount]
        require(bool(candidates), 'MAIL_LIST_CHANGED', 'The selected parcel disappeared before claiming.')
        current = min(candidates, key=lambda item: (parcel_deadline(item), item['occurrence']))
        _running(baas)
        receipt = api.claim_ap_mail(baas, current['id'], read_ap=_read_ap, clock=clock, sleep=sleep)
        require(receipt.get('verified') is True and receipt.get('claimed') is True
                and receipt.get('id') == current['id'] and receipt.get('amount') == amount
                and type(receipt.get('before_ap')) is int and type(receipt.get('after_ap')) is int
                and receipt['after_ap'] - receipt['before_ap'] == amount and receipt['after_ap'] <= HARD_CAP,
                'MAIL_CLAIM_UNVERIFIED', 'The whole parcel receipt could not be verified.')
        adopt(receipt['after'], removed_id=current['id'])
        record('mail', receipt['before_ap'], receipt['after_ap'], amount, mail_id=current['id'])

    def urgent():
        # Recompute after every single withdrawal. No all-claim and no deadline
        # from the initial user-entered inventory participates in execution.
        for _ in range(200):
            rows = [row for row in snapshot['parcels'] if parcel_deadline(row) <= clock()]
            if not rows:
                return
            claim_one(min(rows, key=lambda row: (parcel_deadline(row), instant(row['expires_before']), row['id'])))
        require(not any(parcel_deadline(row) <= clock() for row in snapshot['parcels']),
                'MAIL_LIST_CHANGED', 'Too many urgent letters arrived during execution.')

    def wait_until(deadline):
        last_scan = clock()
        while clock() < deadline:
            _running(baas)
            urgent()
            wake = min(deadline, last_scan + 60,
                       min((parcel_deadline(row) for row in snapshot['parcels']), default=deadline))
            while clock() < wake:
                _running(baas)
                sleep(min(.25, wake - clock()))
            if clock() < deadline:
                observe()
                last_scan = clock()
        observe()
        urgent()

    def source(action, estimated_amount):
        _running(baas)
        now = datetime.fromtimestamp(clock(), timezone.utc)
        key = server_day(now, settings) + ':' + action
        # Cafe's target withdrawal is an additional explicit user request, not a
        # replay of the daily source, and can legitimately collect fresh stock.
        if key in blocked_source_days:
            return
        if action == 'free' and _free_ap_available(baas):
            clear(HARD_CAP - 10, 'free_ap_headroom')
        before_mail = observe()
        before_ap = _read_ap(baas)
        key = server_day(datetime.fromtimestamp(clock(), timezone.utc), settings) + ':' + action
        if key in blocked_source_days:
            return
        receipt = _collect_hoard_source(baas, action, {**settings, 'daily_ap': estimated_amount} if action == 'daily' else settings)
        require(isinstance(receipt, dict) and receipt.get('verified') is True
                and type(receipt.get('amount')) is int and receipt['amount'] >= 0
                and isinstance(receipt.get('receipt'), str),
                'SOURCE_NOT_VERIFIED', 'The AP source did not provide an exact amount and a recognized source-state receipt.')
        _running(baas)
        after_ap = _read_ap(baas)
        after_mail = observe()
        require(after_ap >= before_ap, 'SOURCE_NOT_VERIFIED', 'An AP source unexpectedly reduced character AP.')
        added = after_mail['total_ap'] - before_mail['total_ap']
        require(added >= 0, 'MAIL_DELIVERY_UNVERIFIED', 'Mail disappeared while checking the AP source.')
        delivered = api.verify_mail_delivery(before_mail, after_mail, added)
        require(sum(row['amount'] for row in delivered) == added,
                'MAIL_DELIVERY_UNVERIFIED', 'The source mail amount could not be verified.')
        gained = after_ap - before_ap + added
        maximum = {'daily': estimated_amount, 'free': 10, 'club': 10, 'jjc': 90 * (settings['jjc_refreshes'] + 1), 'cafe': HARD_CAP}[action]
        require(gained == receipt['amount'] and 0 <= gained <= maximum, 'SOURCE_NOT_VERIFIED',
                'The actual AP delivery does not match the observed source receipt; the source will not be retried.')
        if action in {'free', 'club'}:
            require(gained in {0, 10}, 'SOURCE_NOT_VERIFIED', 'The free or club AP receipt must be exactly ten AP, or an explicit no-op.')
        if action == 'club':
            require(after_ap == before_ap and added == gained, 'SOURCE_NOT_VERIFIED', 'Club AP must be observed as a new whole mail parcel.')
        final_key = server_day(datetime.fromtimestamp(clock(), timezone.utc), settings) + ':' + action
        # A route spanning reset has an ambiguous reward day. Never replay it
        # on either adjacent day, but report only the verified receipt once.
        blocked_source_days.update((key, final_key))
        completed_sources.add(final_key)
        record(action, before_ap, after_ap, gained, source_key=final_key, estimated_amount=estimated_amount,
               source_receipt=receipt['receipt'], skipped=receipt.get('skipped', gained == 0),
               delivery='mail' if added and after_ap == before_ap else 'mixed' if added else 'character')
        urgent()

    initial = observe()
    actual = _read_ap(baas)
    plan = build_hoard_plan({**settings, 'current_ap': actual}, now=datetime.fromtimestamp(clock(), timezone.utc),
                            mailbox_snapshot={**initial, 'character_ap': actual}, snapshot_provenance='live_scan')
    # Mail and headroom generated by a forecast are deliberately excluded.
    # Actual new parcel expiries are scheduled from subsequent observations.
    events = [step for step in plan['steps'] if step['action'] in {'daily', 'free', 'club', 'jjc', 'ready'}
              or (step['action'] == 'cafe' and instant(step['at']) < instant(plan['target_at']))
              or (step['action'] == 'clear' and step.get('reason') == 'natural_recovery')]
    urgent()
    for step in events:
        wait_until(instant(step['at']).timestamp())
        if step['action'] == 'clear':
            clear(step['target_ap'], 'natural_recovery')
        elif step['action'] == 'ready':
            value = _read_ap(baas)
            record('ready', value, value)
        else:
            source(step['action'], step['amount'])
    if settings['spend_at_target']:
        clear(9, 'target_spend')
        cafe_amount = plan['available_at_target']['cafe_ap']
        if cafe_amount:
            # Earlier days use a different server-day key. The target-day cafe
            # has no earlier scheduled claim, so no daily source is replayed.
            source('cafe', cafe_amount)
            clear(9, 'target_spend')
        for _ in range(200):
            if not snapshot['parcels']:
                break
            row = min(snapshot['parcels'], key=lambda item: (parcel_deadline(item), item['id']))
            claim_one(row)
            clear(9, 'target_spend')
        require(not snapshot['parcels'], 'MAIL_LIST_CHANGED', 'New mail kept arriving during target spending.')
    final = observe()
    actual = _read_ap(baas)
    result = {'kind': 'hoard_execution', 'inventory_kind': 'verified', 'completed': True,
            'actual_ap': actual, 'actual_mail_ap': final['total_ap'], 'actual_total_ap': actual + final['total_ap'],
            'mailbox': {'kind': 'hoard_mail_scan', 'inventory_kind': 'verified', 'character_ap': actual, **_public_mail(final)}, 'completed_sources': sorted(completed_sources),
            'steps': completed[-64:], 'steps_total': len(completed), 'steps_offset': max(0, len(completed) - 64),
            'history_truncated': len(completed) > 64, 'plan': public_hoard_plan(plan, omit_steps=True)}
    from .schema import json_size
    while True:
        try:
            json_size(result)
            return result
        except PluginError as error:
            if error.code != 'PAYLOAD_TOO_LARGE' or not result['steps']:
                raise
            result['steps'] = result['steps'][1:]
            result['steps_offset'] += 1
            result['history_truncated'] = True
