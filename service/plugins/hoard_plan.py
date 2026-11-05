"""Pure AP forecasts and indivisible mail scheduling, without game side effects.

Only a complete mailbox observation supplies verified mail. Future source delivery
and its lifetime are forecasts; the executor replaces them with fresh scans.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import heapq
import math
import re

from .errors import PluginError, require

HARD_CAP = 999
MAIL_LIFETIME = timedelta(hours=24)  # Forecast only; never an execution deadline.
MARGIN = timedelta(minutes=10)
MAX_MAIL_PARCELS = 200


def instant(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None and result.utcoffset() is not None,
                'INVALID_TIME', 'Times must include an explicit time zone.')
        return result
    except (TypeError, ValueError, AttributeError):
        raise PluginError('INVALID_TIME', 'Use an ISO 8601 date and time with an explicit time zone.') from None


def tube_cost(count: int, already_bought: int = 0) -> int:
    return sum(30 if index < 3 else 60 for index in range(already_bought, already_bought + count))


def validate_mail_snapshot(snapshot: dict) -> dict:
    """Validate the anonymous observation contract, without asserting freshness.

    A caller-provided snapshot is useful for a pure forecast, never permission to
    claim anything. Execution always reads a new observation from the device.
    """
    require(isinstance(snapshot, dict) and snapshot.get('complete') is True,
            'INCOMPLETE_MAILBOX', 'A complete mailbox observation is required.')
    observed = instant(snapshot.get('observed_at'))
    parcels = snapshot.get('parcels')
    count = snapshot.get('mailbox_count')
    require(isinstance(parcels, list) and len(parcels) <= MAX_MAIL_PARCELS
            and type(count) is int and len(parcels) <= count <= 200,
            'INVALID_MAILBOX', 'The mailbox observation is outside supported bounds.')
    require(isinstance(snapshot.get('fingerprint'), str)
            and re.fullmatch(r'[0-9a-f]{64}', snapshot['fingerprint']) is not None,
            'INVALID_MAILBOX', 'The mailbox fingerprint is invalid.')
    identities = set()
    for parcel in parcels:
        require(isinstance(parcel, dict), 'INVALID_MAILBOX', 'A mail observation is invalid.')
        for key in (('id', 'identity') if 'identity' in parcel else ('id',)):
            require(isinstance(parcel.get(key), str) and re.fullmatch(r'[0-9a-f]{32}(?:[0-9a-f]{32})?', parcel[key]) is not None,
                    'INVALID_MAILBOX', 'Mail identifiers must be anonymous digests.')
        require(parcel['id'] not in identities, 'INVALID_MAILBOX', 'Mail locators must be unique.')
        identities.add(parcel['id'])
        require(type(parcel.get('amount')) is int and 1 <= parcel['amount'] <= HARD_CAP,
                'INVALID_MAILBOX', 'Each AP parcel must fit into the character AP limit as a whole.')
        low, high = instant(parcel.get('expires_at')), instant(parcel.get('expires_before'))
        require(low < high and high > observed and parcel.get('expiry_precision') in {'day', 'hour', 'minute', 'second', 'under-hour'},
                'INVALID_MAILBOX', 'Mail expiry must be a conservative, nonempty interval.')
        require(parcel.get('source', 'mailbox-ocr') == 'mailbox-ocr' and type(parcel.get('occurrence')) is int
                and parcel['occurrence'] >= 0 and isinstance(parcel.get('received_at'), str)
                and re.fullmatch(r'\d{4}-\d{2}-\d{2}', parcel['received_at']) is not None,
                'INVALID_MAILBOX', 'Mail provenance is incomplete.')
        try:
            datetime.fromisoformat(parcel['received_at'])
        except ValueError:
            raise PluginError('INVALID_MAILBOX', 'The mail received date is invalid.') from None
    require(type(snapshot.get('total_ap')) is int
            and snapshot['total_ap'] == sum(parcel['amount'] for parcel in parcels),
            'INVALID_MAILBOX', 'The mailbox AP total does not match its parcels.')
    if 'character_ap' in snapshot:
        require(type(snapshot['character_ap']) is int and 0 <= snapshot['character_ap'] <= HARD_CAP,
                'INVALID_MAILBOX', 'The observed character AP is invalid.')
    return snapshot


def server_day(at: datetime, settings: dict) -> str:
    zone = timezone(timedelta(minutes=settings['server_utc_offset_minutes']))
    local = at.astimezone(zone) - timedelta(hours=settings['reset_hour'])
    return local.date().isoformat()


def build_hoard_plan(settings: dict, *, now: datetime | None = None,
                     mailbox_snapshot: dict | None = None,
                     snapshot_provenance: str = 'provided_snapshot') -> dict:
    zone = timezone(timedelta(minutes=settings['server_utc_offset_minutes']))
    target = instant(settings['target_at']).astimezone(zone)
    now = (now or datetime.now(timezone.utc)).astimezone(zone)
    require(now < target <= now + timedelta(days=7), 'INVALID_TARGET', 'Spend time must be in the next seven days.')
    require(settings['cafe_stock'] <= settings['cafe_capacity'], 'INVALID_SETTINGS', 'Cafe stock exceeds its capacity.')
    require(settings['purchases_today'] <= settings['tube_count'] or settings['tube_count'] == 0,
            'INVALID_SETTINGS', 'Purchases already made exceed the planned daily purchase count.')
    require(snapshot_provenance in {'provided_snapshot', 'live_scan'}, 'INVALID_MAILBOX', 'Invalid snapshot provenance.')
    if mailbox_snapshot is not None:
        validate_mail_snapshot(mailbox_snapshot)
    steps, warnings, mail, events = [], [], [], []
    sequence = 0
    initial_ap = mailbox_snapshot.get('character_ap', settings['current_ap']) if mailbox_snapshot else settings['current_ap']
    ap, cafe, clock = float(initial_ap), float(settings['cafe_stock']), now
    premium_cost, pending_mail_ap, estimated_overflow, discarded = 0, 0, 0, 0
    executable = True
    inventory = {'provenance': snapshot_provenance if mailbox_snapshot else 'estimate',
                 'verified_mail_ap': mailbox_snapshot['total_ap'] if mailbox_snapshot else 0,
                 'estimated_mail_ap': sum(row['amount'] for row in settings['mail']) if mailbox_snapshot is None else 0,
                 'estimated_overflow_ap': 0, 'pending_source_mail_ap': 0}
    if mailbox_snapshot:
        inventory['observed_at'] = mailbox_snapshot['observed_at']
        if snapshot_provenance == 'provided_snapshot':
            warnings.append('MAILBOX_SNAPSHOT_REVALIDATED_ON_START')
    else:
        warnings.append('MAILBOX_SCAN_REQUIRED')

    def enqueue(at, action, amount=0, **metadata):
        nonlocal sequence
        sequence += 1
        heapq.heappush(events, (at, sequence, action, amount, metadata))

    def add_mail(amount, low, *, mail_id, verified=False, high=None):
        if amount:
            require(0 < amount <= HARD_CAP, 'INVALID_MAILBOX', 'A single mail parcel cannot be split to fit AP.')
            parcel = {'id': mail_id, 'amount': int(amount), 'expires_at': low,
                      'expires_before': high or low + timedelta(seconds=1), 'verified': verified}
            mail.append(parcel)
            if low - MARGIN <= target:
                enqueue(max(clock, low - MARGIN), 'mail', amount,
                        mail_id=mail_id, verification='verified' if verified else 'estimated')

    if mailbox_snapshot:
        for parcel in mailbox_snapshot['parcels']:
            require(instant(parcel['expires_before']) > now, 'STALE_MAILBOX', 'Scan the mailbox again before forecasting expired intervals.')
            add_mail(parcel['amount'], instant(parcel['expires_at']), mail_id=parcel['id'],
                     high=instant(parcel['expires_before']), verified=True)
    else:
        for index, parcel in enumerate(settings['mail']):
            expires = instant(parcel['expires_at']).astimezone(zone)
            require(expires > now, 'EXPIRED_MAIL', 'Remove expired mail before building a plan.')
            add_mail(parcel['amount'], expires, mail_id='estimate:' + str(index))
        if settings['mail']:
            warnings.append('MAIL_EXPIRY_ESTIMATED')

    day_start = now.replace(hour=settings['reset_hour'], minute=0, second=0, microsecond=0)
    if day_start > now:
        day_start -= timedelta(days=1)
    days = []
    while day_start < target:
        days.append(day_start)
        day_start += timedelta(days=1)
    purchase_days = days[-settings['tube_days']:]
    for index, day in enumerate(days):
        claim_at = max(now, day, min(day + timedelta(days=1) - MARGIN, target - timedelta(minutes=2)))
        if day in purchase_days and settings['tube_count']:
            already = settings['purchases_today'] if index == 0 else 0
            count = max(0, settings['tube_count'] - already)
            if count:
                enqueue(max(now, claim_at - timedelta(seconds=1)), 'manual_purchase', count * 120,
                        count=count, pyroxene=tube_cost(count, already))
        daily = settings['daily_ap'] if index == 0 else 150
        club = settings['club_ap'] if index == 0 else 10
        for action, amount in [('free', 10 if settings['claim_free_ap'] else 0), ('daily', daily), ('club', club),
                               ('jjc', {'none': 0, '30': 30, '30_60': 90}[settings['jjc_mode']] * (settings['jjc_refreshes'] + 1))]:
            if amount:
                enqueue(claim_at, action, amount, source_key=server_day(claim_at, settings) + ':' + action)
        if day + timedelta(days=1) < target:
            enqueue(claim_at, 'cafe', source_key=server_day(claim_at, settings) + ':cafe')
        if settings['strategy'] == 'regeneration' and day < target - timedelta(hours=24):
            enqueue(max(now, day + timedelta(minutes=1)), 'regenerate')
    enqueue(target, 'ready')

    def advance(at):
        nonlocal clock, ap, cafe, discarded
        hours = (at - clock).total_seconds() / 3600
        if ap < settings['soft_cap']:
            ap = min(settings['soft_cap'], ap + hours * 10)
        produced = cafe + hours * settings['cafe_rate']
        discarded += max(0, produced - settings['cafe_capacity'])
        cafe = min(settings['cafe_capacity'], produced)
        clock = at

    def emit(action, before, amount=0, **metadata):
        steps.append({'at': clock.isoformat(), 'action': action, 'amount': int(amount),
                      'ap_before': math.floor(before), 'ap_after': math.floor(ap),
                      'mail_ap': sum(row['amount'] for row in mail), **metadata})

    def clear_to(limit, reason):
        nonlocal ap
        if ap > limit:
            before = ap
            ap = max(0, math.floor(limit / 10) * 10)
            emit('clear', before, before - ap, target_ap=math.floor(limit), reason=reason, task=settings['spend_task'])

    def gain(action, amount, direct=False, **metadata):
        nonlocal ap, estimated_overflow
        if direct:
            clear_to(HARD_CAP - amount, 'direct_purchase_headroom')
        before = ap
        overflow = max(0, math.floor(ap + amount - HARD_CAP))
        ap = min(HARD_CAP, ap + amount)
        if overflow:
            estimated_overflow += overflow
            warnings.extend(['SOURCE_DELIVERY_WILL_BE_VERIFIED', 'MAIL_EXPIRY_ESTIMATED'])
            add_mail(overflow, clock + MAIL_LIFETIME, mail_id='forecast:' + str(sequence) + ':' + str(len(steps)))
        emit(action, before, amount, overflow_ap=overflow, verification='scan_required', **metadata)

    def claim_one(parcel, reason):
        nonlocal ap
        clear_to(HARD_CAP - parcel['amount'], reason)
        before = ap
        ap += parcel['amount']
        mail.remove(parcel)
        emit('mail', before, parcel['amount'], mail_id=parcel['id'],
             verification='verified' if parcel['verified'] else 'estimated')

    while events:
        at, _, action, amount, metadata = heapq.heappop(events)
        if at > target:
            break
        advance(at)
        if action == 'mail':
            parcel = next((row for row in mail if row['id'] == metadata['mail_id']), None)
            if parcel:
                claim_one(parcel, 'expiring_mail_headroom')
        elif action == 'club':
            pending_mail_ap += amount
            warnings.append('CLUB_MAIL_WILL_BE_VERIFIED')
            emit(action, ap, amount, expected_mail_ap=amount, delivery='mail', verification='scan_required', **metadata)
        elif action == 'manual_purchase':
            premium_cost += metadata['pyroxene']
            gain(action, amount, direct=True, **metadata)
            executable = False
        elif action == 'regenerate':
            clear_to(max(0, settings['soft_cap'] - 120), 'natural_recovery')
        elif action == 'cafe':
            amount = math.floor(cafe)
            cafe -= amount
            if amount:
                gain(action, amount, **metadata)
        elif action == 'ready':
            available_at_target = {'character_ap': math.floor(ap), 'mail_ap': sum(row['amount'] for row in mail),
                                   'cafe_ap': math.floor(cafe),
                                   'total_ap': math.floor(ap) + math.floor(cafe) + sum(row['amount'] for row in mail)}
            emit('ready', ap)
            if settings['spend_at_target']:
                before, ap = ap, 0
                emit('spend', before, before, task=settings['spend_task'])
                if cafe >= 1:
                    amount = math.floor(cafe)
                    cafe -= amount
                    gain('cafe', amount, source_key=server_day(clock, settings) + ':cafe:target')
                    before, ap = ap, 0
                    emit('spend', before, before, task=settings['spend_task'])
                for parcel in sorted(list(mail), key=lambda row: (row['expires_at'], row['id'])):
                    claim_one(parcel, 'target_mail_headroom')
                    before, ap = ap, 0
                    emit('spend', before, before, task=settings['spend_task'])
        else:
            gain(action, amount, direct=action == 'free', **metadata)
    if premium_cost:
        warnings.append('PREMIUM_PURCHASES_ARE_MANUAL')
    if discarded:
        warnings.append('CAFE_CAPACITY_LOSS')
    inventory.update(estimated_overflow_ap=estimated_overflow, pending_source_mail_ap=pending_mail_ap)
    return {'generated_at': now.isoformat(), 'target_at': target.isoformat(), 'executable': executable,
            'steps': steps, 'pending_mail_ap': pending_mail_ap, 'inventory': inventory,
            'available_at_target': available_at_target,
            'summary': {'character_ap': math.floor(ap), 'mail_ap': sum(row['amount'] for row in mail),
                        'cafe_ap': math.floor(cafe), 'total_ap': math.floor(ap) + math.floor(cafe) + sum(row['amount'] for row in mail),
                        'manual_pyroxene_budget': premium_cost, 'cafe_capacity_loss': math.floor(discarded)},
            'warnings': list(dict.fromkeys(warnings))}


def public_hoard_plan(plan: dict, *, omit_steps=False) -> dict:
    """Bound history, never inventory; disclose exactly how much was omitted."""
    from .schema import json_size
    result = {**plan, 'steps_total': len(plan['steps']), 'steps_offset': 0,
              'history_truncated': omit_steps or len(plan['steps']) > 256,
              'steps': [] if omit_steps else plan['steps'][:256]}
    if omit_steps:
        result['steps_omitted'] = True
    while True:
        try:
            json_size(result)
            return result
        except PluginError as error:
            if error.code != 'PAYLOAD_TOO_LARGE' or not result['steps']:
                raise
            result['steps'] = result['steps'][:-1]
            result['history_truncated'] = True
