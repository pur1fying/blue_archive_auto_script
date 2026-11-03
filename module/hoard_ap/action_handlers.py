"""动作处理器：把 executor 中巨型 if-else 拆成按 action 分发。

用法：
    from module.hoard_ap.action_handlers import execute_step
    ok = execute_step(executor, state, step)

主入口 execute_step 负责 begin/end_hoard_internal 包裹与分发。
各 handler 内部仍调用 executor 上的 _run_clear / _run_buy_tubes / _run_existing 等。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from module.hoard_ap.constants import (
    ACTION_BUY_TUBES,
    ACTION_CLAIM_CAFE,
    ACTION_CLAIM_GROUP,
    ACTION_CLAIM_JJC,
    ACTION_CLAIM_MAIL,
    ACTION_CLAIM_TASK,
    ACTION_CLAIM_TASK_DAILY_ONLY,
    ACTION_CLEAR_AP,
    ACTION_ENSURE_HEADROOM,
    ACTION_FREE_BUY,
    ACTION_HOLD,
    ACTION_NOTIFY,
    ACTION_SPEND_READY,
    ACTION_USE_AP_CARD,
    ACTION_WAIT,
    AP_HARD_CAP,
    CLEAR_MODE_ACTIVITY,
    PHASE_ABORTED,
)
from module.hoard_ap.data_service import InventoryService, config_dir_of
from module.hoard_ap.state import HoardRuntimeState, phase_from_step_action


def _cfg_get(executor, key: str, default=None):
    return getattr(executor.config, key, default)


def _notify(executor, title: str, body: str) -> None:
    try:
        from module.hoard_ap import executor as ex_mod

        ex_mod._notify(executor, title, body)
    except Exception:
        try:
            executor.logger.info(f"[囤体] {title}: {body}")
        except Exception:
            pass


def _run_clear(executor, target, clear_mode):
    from module.hoard_ap import executor as ex_mod

    return ex_mod._run_clear(executor, target, clear_mode)


def _run_buy_tubes(executor, tubes):
    from module.hoard_ap import executor as ex_mod

    return ex_mod._run_buy_tubes(executor, tubes)


def _run_existing(executor, name):
    from module.hoard_ap import executor as ex_mod

    return ex_mod._run_existing(executor, name)


def _parse_step_when(value: str):
    from module.hoard_ap import executor as ex_mod

    return ex_mod._parse_step_when(value)


def _claim_amounts_from_step(step: dict) -> List[int]:
    """从步骤 meta / note 解析本批计划领取的面额列表。"""
    meta = step.get("meta") or {}
    out: List[int] = []
    raw = meta.get("claim_amounts")
    if isinstance(raw, (list, tuple)):
        for x in raw:
            try:
                v = int(x)
            except Exception:
                continue
            if v > 0:
                out.append(v)
    if out:
        return out
    note = str(step.get("note") or "")
    # 50@0.1h、663@1小时 / +713（50、663）
    for m in re.finditer(r"(?<![.\d])(\d{1,4})\s*@", note):
        try:
            v = int(m.group(1))
        except Exception:
            continue
        if 1 <= v <= 999:
            out.append(v)
    if out:
        return out
    m = re.search(r"[+＋]\s*(\d{1,4})", note)
    if m:
        try:
            v = int(m.group(1))
            if 1 <= v <= 9999:
                return [v]
        except Exception:
            pass
    return out


def _remove_claimed_bags(bags: List[Dict[str, Any]], amounts: List[int]) -> List[Dict[str, Any]]:
    """按面额从邮箱明细里扣掉已领的包（同面额先扣剩余时间更短的）。"""
    if not amounts:
        return list(bags or [])
    remain = list(bags or [])
    for amt in amounts:
        best_i = -1
        best_rh = 1e9
        for i, b in enumerate(remain):
            try:
                ba = int(b.get("amount") or 0)
            except Exception:
                continue
            if ba != int(amt):
                continue
            try:
                rh = float(b.get("remain_hours"))
            except Exception:
                rh = 99.0
            if b.get("under_1h"):
                rh = min(rh, 0.99)
            if rh < best_rh:
                best_rh = rh
                best_i = i
        if best_i >= 0:
            remain.pop(best_i)
    return remain


def _refresh_ap_after_gain(
    executor,
    *,
    reason: str = "",
    rescan_mail: bool = False,
    claimed_amounts: Optional[List[int]] = None,
    fallback_add: int = 0,
) -> Dict[str, Any]:
    """领取/买管后回写当前体力；可选重扫邮箱或按面额扣邮。

    返回 {"ap": int| -1, "mail_ap": int|None, "notes": [...]}
    """
    notes: List[str] = []
    cfg_dir = config_dir_of(executor)
    inv_srv = InventoryService(cfg_dir)
    cfg = getattr(executor, "config", None)
    ap = -1
    try:
        from module.hoard_ap import executor as ex_mod

        try:
            executor.to_main_page()
        except Exception:
            pass
        ap = int(ex_mod._read_ap_safe(executor, fallback=-1, to_main=True))
    except Exception:
        ap = -1

    if ap < 0 and fallback_add > 0:
        try:
            prev = int(inv_srv.load().current_ap or 0)
        except Exception:
            prev = 0
        hard = int(_cfg_get(executor, "hoard_ap_hard_cap", AP_HARD_CAP) or AP_HARD_CAP)
        ap = min(hard, max(0, prev + int(fallback_add)))
        notes.append(f"读体失败，按计划 +{fallback_add} 估算体={ap}")
        try:
            executor.logger.warning(
                f"[囤体] {reason or '领取'}后读体失败，估算 current_ap={ap} (prev+{fallback_add})"
            )
        except Exception:
            pass

    if ap >= 0:
        try:
            inv_srv.set_current_ap(ap, cfg=cfg)
            notes.append(f"current_ap={ap}")
            try:
                executor.logger.info(
                    f"[囤体] {reason or '领取'}后回写当前体力={ap}"
                )
            except Exception:
                pass
        except Exception as e:
            notes.append(f"写体力失败:{e}")

    mail_ap_out: Optional[int] = None
    if rescan_mail:
        try:
            from module.hoard_ap.mail_ocr import scan_mail_ap, apply_scan_to_inventory

            scan = scan_mail_ap(executor)
            if scan.get("ok") and (scan.get("bags") or []):
                total = apply_scan_to_inventory(cfg_dir, scan)
                inv_srv.set_mail(
                    mail_ap=int(total),
                    mail_bags=list(scan.get("bags") or []),
                    cfg=cfg,
                )
                mail_ap_out = int(total)
                notes.append(f"mail_ap={mail_ap_out}")
                try:
                    executor.logger.info(
                        f"[囤体] {reason or '领邮'}后重扫邮箱 total={mail_ap_out} "
                        f"bags={len(scan.get('bags') or [])}"
                    )
                except Exception:
                    pass
            elif scan.get("ok"):
                # 零识别≠邮箱为空：不覆盖明细（尤其人工纠正），走扣减兜底
                raise RuntimeError("scan ok but zero bags (keep existing ledger)")
            else:
                raise RuntimeError(str(scan.get("error") or "scan failed"))
        except Exception as e:
            # 扫失败：按本批面额从明细扣
            amts = list(claimed_amounts or [])
            if amts:
                try:
                    inv = inv_srv.load()
                    left = _remove_claimed_bags(list(inv.mail_bags or []), amts)
                    total = sum(int(b.get("amount") or 0) for b in left)
                    inv_srv.set_mail(mail_ap=int(total), mail_bags=left, cfg=cfg)
                    mail_ap_out = int(total)
                    notes.append(f"扫邮失败，按面额扣后 mail_ap={mail_ap_out}")
                    try:
                        executor.logger.warning(
                            f"[囤体] {reason or '领邮'}后重扫失败({e})，"
                            f"按 claim_amounts 扣邮 → {mail_ap_out}"
                        )
                    except Exception:
                        pass
                except Exception as e2:
                    notes.append(f"扣邮失败:{e2}")
            else:
                notes.append(f"重扫邮箱失败:{e}")
    elif claimed_amounts:
        try:
            inv = inv_srv.load()
            left = _remove_claimed_bags(list(inv.mail_bags or []), list(claimed_amounts))
            total = sum(int(b.get("amount") or 0) for b in left)
            inv_srv.set_mail(mail_ap=int(total), mail_bags=left, cfg=cfg)
            mail_ap_out = int(total)
            notes.append(f"mail_ap={mail_ap_out}")
        except Exception as e:
            notes.append(f"扣邮失败:{e}")

    return {"ap": ap, "mail_ap": mail_ap_out, "notes": notes}


class ActionHandler:
    action: str = ""

    @classmethod
    def can_handle(cls, action: str) -> bool:
        return bool(cls.action) and action == cls.action

    def handle(self, executor, state: HoardRuntimeState, step: dict) -> bool:
        raise NotImplementedError


class GuardMixin:
    """过「原定时间之后的 04:00」后禁止掏空主堆囤货。

    边界必须以步骤的原定时间为基准：03:50 主堆批次属于前一游戏日，
    它的保护点是紧随其后的那个 04:00 日界。旧实现写
    `now >= server_day_start(now)`，而 server_day_start(now) 永远是
    「不超过 now 的最近 04:00」，比较恒为真——导致正常的 03:50 批次
    也被误拦，且被拦步骤还会被记成成功。
    """

    @staticmethod
    def _parse_when(value) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        s = str(value).strip().replace("T", " ")
        for n, fmt in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M")):
            try:
                return datetime.strptime(s[:n], fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    @staticmethod
    def block_after_reset(executor, action: str, note: str, meta: dict, when=None) -> bool:
        try:
            note_g = str(note or "")
            meta_g = meta or {}
            is_old_mail_claim = (
                action == ACTION_CLAIM_MAIL
                and not meta_g.get("scan_only")
                and ("旧邮" in note_g or "主堆前领取" in note_g)
            )
            is_old_mail_clear = action == ACTION_CLEAR_AP and (
                ("旧邮" in note_g and "清到" in note_g)
                or ("空出" in note_g and "旧邮" in note_g)
            )
            if not (is_old_mail_claim or is_old_mail_clear):
                return False

            when_dt = GuardMixin._parse_when(when) or GuardMixin._parse_when(
                meta_g.get("planned_when")
            )
            if when_dt is None:
                # 拿不到原定时间就无法证明过点：放行，交给执行台账兜底，
                # 绝不凭恒真比较误杀正常的 03:50 批次。
                executor.logger.debug("[囤体] guard：步骤缺原定时间，放行")
                return False

            from datetime import timedelta

            from module.hoard_ap.planner import server_day_start as _sds

            boundary = _sds(when_dt) + timedelta(days=1)  # 原定时间之后的 04:00
            if datetime.now() < boundary:
                return False
            if is_old_mail_claim:
                executor.logger.warning(
                    "[囤体] 已过原定 %s 之后的 04:00，拒绝领取旧邮（邮箱是主堆囤货）: %s"
                    % (when_dt.strftime("%m-%d %H:%M"), note_g[:80])
                )
            else:
                executor.logger.warning(
                    "[囤体] 已过原定 %s 之后的 04:00，拒绝为领旧邮清体: %s"
                    % (when_dt.strftime("%m-%d %H:%M"), note_g[:80])
                )
            return True
        except Exception as ge:
            try:
                executor.logger.debug("[囤体] guard skip: %s" % ge)
            except Exception:
                pass
        return False


class UrgentMailWatchHandler(ActionHandler):
    """临期邮监视（meta.urgent_mail_watch）。"""

    @classmethod
    def can_handle(cls, action: str) -> bool:
        return False  # 由 meta 特判，不走 action 名

    def handle(self, executor, state, step) -> bool:
        meta = step.get("meta") or {}
        try:
            poll_coarse = int(meta.get("poll_seconds") or 600)
        except Exception:
            poll_coarse = 600
        try:
            poll_fine = int(meta.get("poll_seconds_under_1h") or 120)
        except Exception:
            poll_fine = 120
        thr = float(meta.get("refresh_when_remain_h") or 0.2)
        skip_stack = bool(meta.get("skip_stack_mail", True))
        try:
            from module.hoard_ap.mail_ocr import scan_mail_ap, apply_scan_to_inventory
            from module.hoard_ap.inventory import project_display

            cfg_dir = config_dir_of(executor)
            inv_srv = InventoryService(cfg_dir)
            scan = scan_mail_ap(executor)
            if scan.get("ok"):
                apply_scan_to_inventory(cfg_dir, scan)
            inv = inv_srv.load()
            disp = project_display(inv)
            bags = list(disp.get("mail_bags") or [])

            def _is_stack(b: dict) -> bool:
                if not skip_stack:
                    return False
                try:
                    rh = float(b.get("remain_hours"))
                except Exception:
                    rh = 99.0
                if b.get("under_1h") or str(b.get("timer_mode") or "") == "under_1h_internal":
                    return False
                if rh <= 1.0:
                    return False
                if str(b.get("role") or "") == "stack_for_claim":
                    return True
                try:
                    amt = int(b.get("amount") or 0)
                except Exception:
                    amt = 0
                if rh >= 12.0:
                    return True
                if amt >= 200 and rh >= 2.0:
                    return True
                if rh >= 2.0:
                    return True
                return False

            rescue = [b for b in bags if not _is_stack(b)]
            min_h = None
            any_under = False
            for b in rescue:
                try:
                    rh = float(b.get("remain_hours"))
                except Exception:
                    continue
                if b.get("under_1h") or str(b.get("timer_mode") or "") == "under_1h_internal":
                    any_under = True
                if min_h is None or rh < min_h:
                    min_h = rh
            executor.logger.info(
                f"[囤体] 临期巡检 min_remain_h={min_h} under1h={any_under} "
                f"rescue={len(rescue)} all={len(bags)} (跳过主堆囤货={skip_stack})"
            )
            ocr_still_coarse = False
            for b in bags:
                try:
                    rh = float(b.get("remain_hours"))
                except Exception:
                    continue
                txt = str(b.get("remain_text") or "")
                if b.get("under_1h"):
                    continue
                if (
                    rh <= 1.0
                    and re.search(r"\d+\s*小?时", txt)
                    and "不到" not in txt
                    and "不足" not in txt
                ):
                    ocr_still_coarse = True
                    break

            if ocr_still_coarse and (any_under or (min_h is not None and min_h < 1.0)):
                executor.logger.info(
                    "[囤体] OCR 仍显示整点小时，内计时作废重计；5 分钟后再识别"
                )
                try:
                    inv2 = inv_srv.load()
                    nb = []
                    for b in list(inv2.mail_bags or []):
                        bb = dict(b)
                        bb.pop("under_1h_since", None)
                        bb["under_1h"] = False
                        if bb.get("timer_mode") == "under_1h_internal":
                            bb["timer_mode"] = "coarse_hours"
                        nb.append(bb)
                    inv2.mail_bags = nb
                    inv_srv.save(inv2)
                except Exception as _me:
                    try:
                        executor.logger.warning(f"[囤体] 邮包计时合并落盘失败: {_me}")
                    except Exception:
                        pass
                executor.next_time = 300
                if isinstance(step.get("meta"), dict):
                    step["meta"]["_watch_pending"] = True
                else:
                    step["meta"] = dict(meta or {}, _watch_pending=True)
                return True

            if min_h is not None and min_h <= thr + 1e-6 and rescue:
                need = sum(int(b.get("amount") or 0) for b in rescue)
                try:
                    cur = int(executor.get_ap(True))
                except Exception:
                    cur = 999
                hard = int(_cfg_get(executor, "hoard_ap_hard_cap", 999) or 999)
                need = min(need, hard)
                target = max(0, hard - need)
                if cur > target:
                    _run_clear(
                        executor,
                        target,
                        meta.get("clear_mode")
                        or _cfg_get(executor, "hoard_ap_clear_mode", CLEAR_MODE_ACTIVITY),
                    )
                _run_existing(executor, "mail")
                if isinstance(step.get("meta"), dict):
                    step["meta"]["_watch_pending"] = False
                return True
            if any_under or (min_h is not None and min_h <= 1.0):
                executor.next_time = max(60, min(poll_fine, 180))
            else:
                executor.next_time = max(120, min(poll_coarse, 900))
            if isinstance(step.get("meta"), dict):
                step["meta"]["_watch_pending"] = True
            else:
                step["meta"] = dict(meta or {}, _watch_pending=True)
            return True
        except Exception as e:
            executor.logger.warning(f"[囤体] 临期邮监视失败: {e}")
            executor.next_time = 600
            if isinstance(step.get("meta"), dict):
                step["meta"]["_watch_pending"] = True
            return True


class ClearApHandler(ActionHandler):
    action = ACTION_CLEAR_AP

    def handle(self, executor, state, step) -> bool:
        meta = step.get("meta") or {}
        amount = int(step.get("amount") or 0)
        target = int(meta.get("target_ap", max(0, AP_HARD_CAP - amount)))
        clear_mode = meta.get("clear_mode") or _cfg_get(
            executor, "hoard_ap_clear_mode", CLEAR_MODE_ACTIVITY
        )
        return _run_clear(executor, target, clear_mode)


class EnsureHeadroomHandler(ActionHandler):
    action = ACTION_ENSURE_HEADROOM

    def handle(self, executor, state, step) -> bool:
        return ClearApHandler().handle(executor, state, step)


class BuyTubesHandler(ActionHandler):
    action = ACTION_BUY_TUBES

    def handle(self, executor, state, step) -> bool:
        meta = step.get("meta") or {}
        tubes = int(meta.get("tubes") or _cfg_get(executor, "hoard_ap_tubes", 3) or 3)
        ok = _run_buy_tubes(executor, tubes)
        if not ok:
            executor.logger.warning(
                "[囤体] 买管失败：不记完成、不估算体力，保持可重试"
            )
            _notify(executor, "囤体买管未完成", "请检查体力空位/钻石；下一轮会自动重试")
            return False
        # 买管成功后只认真实读体；读不到就保留旧快照，
        # 绝不按计划值 +120/管 虚增库存。
        _refresh_ap_after_gain(executor, reason="买管", fallback_add=0)
        return True


class FreeBuyHandler(ActionHandler):
    action = ACTION_FREE_BUY

    def handle(self, executor, state, step) -> bool:
        ok = _run_existing(executor, "collect_daily_free_power")
        if not ok:
            executor.logger.warning("[囤体] 免费买体未完成：不勾已领，保持可重试")
            return False
        try:
            InventoryService(config_dir_of(executor)).set_claimed(
                free_buy=True, cfg=getattr(executor, "config", None)
            )
        except Exception as _ce:
            try:
                executor.logger.warning(f"[囤体] 已领标记写入失败（不影响本次结果）: {_ce}")
            except Exception:
                pass
        _refresh_ap_after_gain(executor, reason="免费买体", fallback_add=0)
        return True


class ClaimTaskHandler(ActionHandler):
    actions = {ACTION_CLAIM_TASK, ACTION_CLAIM_TASK_DAILY_ONLY, "claim_task_daily_only"}

    @classmethod
    def can_handle(cls, action: str) -> bool:
        return action in cls.actions

    def handle(self, executor, state, step) -> bool:
        meta = step.get("meta") or {}
        note = step.get("note") or ""
        try:
            from module.hoard_ap.task_daily import collect_daily_except_weekly

            ok = bool(collect_daily_except_weekly(executor, allow_default_xy=True))
            if not ok:
                executor.logger.warning(
                    "[囤体] 每日任务未领成（按钮非高亮或失败）：不勾已领、不记完成"
                )
                _notify(
                    executor,
                    "囤体：每日任务体未领到",
                    "领取按钮未高亮或失败，请手动打开任务→每日→领取；下一轮自动重试",
                )
                return False
            try:
                part = str(meta.get("task_part") or "")
                note_l = str(note or "")
                is_lesson = (
                    part == "lesson"
                    or bool(meta.get("mark_lesson_claimed"))
                    or ("日程" in note_l)
                )
                is_login = part in ("", "login", "task") and not is_lesson
                if "登录" in note_l or "登陆" in note_l:
                    is_login = True
                cfg_dir = config_dir_of(executor)
                inv_srv = InventoryService(cfg_dir)
                cfg = getattr(executor, "config", None)
                if is_lesson:
                    inv_srv.set_claimed(lesson=True, cfg=cfg)
                    executor.logger.info("[囤体] 已勾选：日程50体已领")
                if is_login:
                    inv_srv.set_claimed(task=True, cfg=cfg)
                    executor.logger.info("[囤体] 已勾选：登陆任务体已领")
            except Exception as e:
                executor.logger.warning(f"[囤体] 勾已领失败: {e}")
            # 任务体进角色栏：只认真实读体；读不到保留旧快照，不按计划值估算
            _refresh_ap_after_gain(executor, reason="领任务", fallback_add=0)
            return True
        except Exception as e:
            executor.logger.warning(f"[囤体] 领任务体异常: {e}")
            _notify(executor, "囤体领任务体", str(e))
            return False


class ClaimGroupHandler(ActionHandler):
    action = ACTION_CLAIM_GROUP

    def handle(self, executor, state, step) -> bool:
        ok = _run_existing(executor, "group")
        if not ok:
            executor.logger.warning("[囤体] 小组体未完成：不勾已领，保持可重试")
            return False
        try:
            InventoryService(config_dir_of(executor)).set_claimed(
                group=True, cfg=getattr(executor, "config", None)
            )
        except Exception as _ce:
            try:
                executor.logger.warning(f"[囤体] 已领标记写入失败（不影响本次结果）: {_ce}")
            except Exception:
                pass
        # 只认真实读体，不按计划值估算
        _refresh_ap_after_gain(executor, reason="领小组", fallback_add=0)
        return True


def _jjc_ap_goods_indices(cfg_obj, default=(6, 7)):
    """按当前服务器的竞技场价格表定位 30/60 体力商品索引。

    各服商品顺序不同（CN/Global 的 30/60AP 在 6/7，JP 在 0/1），
    写死索引会在其它服买错商品。找不到时回退旧索引并告警。
    """
    try:
        server = str(getattr(cfg_obj, "server_mode", "CN") or "CN")
        static = getattr(cfg_obj, "static_config", None)
        table = getattr(static, "tactical_challenge_shop_price_list", None)
        goods = []
        if isinstance(table, dict):
            goods = table.get(server) or table.get("CN") or []
        i30 = i60 = -1
        for i, item in enumerate(goods or []):
            try:
                name = str(item[0] or "").strip().upper().replace(" ", "")
            except Exception:
                continue
            if "30AP" in name and i30 < 0:
                i30 = i
            elif "60AP" in name and i60 < 0:
                i60 = i
        if i30 >= 0 and i60 >= 0:
            return i30, i60
    except Exception:
        pass
    return default


class ClaimJjcHandler(ActionHandler):
    action = ACTION_CLAIM_JJC

    def handle(self, executor, state, step) -> bool:
        meta = step.get("meta") or {}
        try:
            from module.hoard_ap.planner import (
                plan_jjc_under_mail_cap,
                MAIL_STACK_TARGET,
                MAIL_STACK_HARD,
                apply_jjc_to_shop_config,
            )
            from module.hoard_ap.constants import JJC_BUY_30_60

            cfg_dir = config_dir_of(executor)
            inv_srv = InventoryService(cfg_dir)
            base_mail = None
            if meta.get("mail_after_cafe") is not None:
                base_mail = int(meta.get("mail_after_cafe"))
            if base_mail is None:
                try:
                    base_mail = int(
                        _cfg_get(executor, "hoard_ap_mail_after_cafe", "") or 0
                    ) or None
                except Exception:
                    base_mail = None
            if base_mail is None:
                try:
                    base_mail = int(inv_srv.load().mail_ap or 0)
                except Exception:
                    base_mail = None
            if base_mail is not None and int(base_mail) >= 0:
                prefer = str(
                    _cfg_get(executor, "hoard_ap_jjc_buy_mode", JJC_BUY_30_60)
                    or JJC_BUY_30_60
                )
                # 体力卡排在 JJC 之后 → 领邮时还未执行，溢出未进 base_mail
                # 需预估体力卡溢出量，从 JJC 可用空位扣除，避免超 999
                ap_card_overflow = 0
                use_card = bool(
                    meta.get("use_ap_card")
                    or _cfg_get(executor, "hoard_ap_use_ap_card", False)
                )
                card_amt = int(
                    meta.get("ap_card_amount")
                    or _cfg_get(executor, "hoard_ap_ap_card_amount", 0)
                    or 0
                )
                if use_card and card_amt > 0:
                    ap_card_overflow = card_amt
                jp = plan_jjc_under_mail_cap(
                    int(base_mail),
                    ap_card_overflow=ap_card_overflow,
                    target=int(meta.get("mail_target") or MAIL_STACK_TARGET),
                    hard_cap=int(meta.get("mail_hard") or MAIL_STACK_HARD),
                    prefer_mode=prefer,
                )
                executor.logger.info(
                    f"[囤体] 动态竞技场 邮底座={base_mail} → {jp.get('note')}"
                )
                try:
                    cfg_obj = getattr(executor, "config", None) or getattr(
                        executor, "config_set", None
                    )
                    mode = str(jp.get("mode") or prefer)
                    if jp.get("buy_30") is False and jp.get("buy_60") is True:
                        mode = "30_60"
                    apply_jjc_to_shop_config(
                        cfg_obj, mode, int(jp.get("refresh") or 0)
                    )

                    def _gset(k, v):
                        if cfg_obj is None:
                            return
                        if hasattr(cfg_obj, "set"):
                            cfg_obj.set(k, v)
                        elif isinstance(cfg_obj, dict):
                            cfg_obj[k] = v
                        else:
                            setattr(cfg_obj, k, v)

                    def _gget(k, d=None):
                        if cfg_obj is None:
                            return d
                        if hasattr(cfg_obj, "get"):
                            try:
                                return cfg_obj.get(k, d)
                            except Exception:
                                return getattr(cfg_obj, k, d)
                        return getattr(cfg_obj, k, d)

                    goods = list(_gget("TacticalChallengeShopList") or [])
                    goods = [int(x) for x in goods]
                    while len(goods) < 16:
                        goods.append(0)
                    i30, i60 = _jjc_ap_goods_indices(cfg_obj)
                    if (i30, i60) == (6, 7):
                        try:
                            executor.logger.warning(
                                "[囤体] 未按价格表定位到 30/60AP 商品，回退默认位 6/7"
                            )
                        except Exception:
                            pass
                    b30 = bool(jp.get("buy_30"))
                    b60 = bool(jp.get("buy_60"))
                    if jp.get("buy_30") is None and jp.get("buy_60") is None:
                        b30 = mode != "none"
                        b60 = mode == "30_60"
                    goods[i30] = 1 if b30 else 0
                    goods[i60] = 1 if b60 else 0
                    _gset("TacticalChallengeShopList", goods)
                    _gset(
                        "TacticalChallengeShopRefreshTime",
                        int(jp.get("refresh") or 0),
                    )
                    if int(jp.get("amount") or 0) <= 0:
                        executor.logger.info("[囤体] 邮箱已近顶，跳过竞技场")
                        return True
                except Exception as e:
                    executor.logger.warning(f"[囤体] 写竞技场配置失败: {e}")
        except Exception as e:
            executor.logger.warning(f"[囤体] 动态竞技场跳过: {e}")
        ok = _run_existing(executor, "tactical_challenge_shop")
        if not ok:
            executor.logger.warning(
                "[囤体] 竞技场商店未完成：不勾已领，保持可重试"
            )
            _notify(
                executor,
                "囤体：竞技场商店未完成",
                "购买/领取未确认成功；下一轮自动重试，也可手动进竞技场商店检查",
            )
            return False
        try:
            InventoryService(config_dir_of(executor)).set_claimed(
                jjc=True, cfg=getattr(executor, "config", None)
            )
        except Exception as _ce:
            try:
                executor.logger.warning(f"[囤体] 已领标记写入失败（不影响本次结果）: {_ce}")
            except Exception:
                pass
        # 竞技场体通常进邮/背包；重扫邮箱 + 读当前体，避免页面数字停旧值
        _refresh_ap_after_gain(
            executor, reason="竞技场", rescan_mail=True, fallback_add=0
        )
        return True


def _claim_mail_scan_only(executor, step, cfg_dir, inv_srv) -> bool:
    """scan_only 步骤：识别邮箱并写入库存明细；零识别不覆盖、留待重扫。"""
    from module.hoard_ap.mail_ocr import scan_mail_ap, apply_scan_to_inventory

    try:
        from module.hoard_ap.scheduler_filter import (
            begin_hoard_internal,
            end_hoard_internal,
        )

        begin_hoard_internal(executor)
        try:
            scan = scan_mail_ap(executor)
        finally:
            end_hoard_internal(executor)
    except Exception:
        scan = scan_mail_ap(executor)
    if scan.get("ok") and (scan.get("bags") or []):
        total = apply_scan_to_inventory(cfg_dir, scan)
        executor.logger.info(
            f"[囤体] 邮箱识别完成 total={total} bags={len(scan.get('bags') or [])} → 已写入明细"
        )
        try:
            inv_srv.set_mail(
                mail_ap=int(total),
                mail_bags=list(scan.get("bags") or []),
                cfg=getattr(executor, "config", None),
                also_after_cafe=True,
            )
        except Exception as e:
            executor.logger.warning(f"[囤体] 回写邮箱配置失败: {e}")
        if isinstance(step.get("meta"), dict):
            step["meta"]["mail_after_cafe"] = int(total)
            step["meta"]["scanned_total"] = int(total)
        return True
    if scan.get("ok"):
        # 零识别：页面打开≠识别可信。绝不覆盖（尤其人工明细），
        # 不记成功，下一轮重扫。
        executor.logger.warning(
            "[囤体] 邮箱识别到 0 包：不覆盖现有明细，保持未完成待重扫"
        )
        _notify(
            executor,
            "囤体：邮箱识别未确认",
            "本次未识别到任何体力包；已保留现有邮箱明细，下一轮自动重扫。"
            "若邮箱确实为空，请在囤体页面手动清空明细。",
        )
        return False
    executor.logger.warning(f"[囤体] 邮箱识别失败: {scan.get('error')}")
    return False


def _pre_scan_bags_before_claim(executor, cfg_dir, inv_srv) -> List[Dict[str, Any]]:
    """领前扫一次：知道现在有哪些包（也给失败回退用）。

    零识别不覆盖：沿用现有明细（含人工纠正）。
    """
    from module.hoard_ap.mail_ocr import scan_mail_ap, apply_scan_to_inventory

    pre_bags: List[Dict[str, Any]] = []
    try:
        scan = scan_mail_ap(executor)
        if scan.get("ok") and (scan.get("bags") or []):
            apply_scan_to_inventory(cfg_dir, scan)
            pre_bags = list(scan.get("bags") or [])
        else:
            try:
                pre_bags = list(inv_srv.load().mail_bags or [])
            except Exception:
                pre_bags = []
    except Exception:
        try:
            pre_bags = list(inv_srv.load().mail_bags or [])
        except Exception:
            pre_bags = []
    return pre_bags


def _bundle_short_mail_claims(
    executor, pre_bags: List[Dict[str, Any]], claim_amts: List[int]
) -> List[int]:
    """一旦开干领邮：本批 + 所有撑不过「下一个 04:00」的短邮一并领，
    避免 05:xx 再单独跑一趟。长倒计时主堆邮（≥到重置+1h 且 ≥12h）保留。"""
    try:
        from datetime import timedelta as _td
        from module.hoard_ap.planner import server_day_start

        now_m = datetime.now()
        day0 = server_day_start(now_m)
        next_reset = day0 if now_m < day0 else day0 + _td(days=1)
        hours_to_reset = max(
            0.0, (next_reset - now_m).total_seconds() / 3600.0
        )
        # 过不了 4 点：剩余 ≤ 距重置；再并上 ≤6h 的短邮，减少同日二次进邮
        thr = max(hours_to_reset + 0.05, 6.0)
        from collections import Counter

        need_c: Counter = Counter()
        for b in pre_bags:
            try:
                rh = float(b.get("remain_hours"))
                amt = int(b.get("amount") or 0)
            except Exception:
                continue
            if amt <= 0 or rh < 0:
                continue
            is_short = bool(b.get("under_1h")) or rh <= thr
            # 明确长囤：剩余远超重置且 ≥12h → 不并
            if (not b.get("under_1h")) and rh >= 12.0 and rh > hours_to_reset + 1.0:
                is_short = False
            if is_short:
                need_c[amt] += 1
        # 计划面额也算要领
        for a in claim_amts or []:
            need_c[int(a)] = max(need_c.get(int(a), 0), (claim_amts or []).count(int(a)))
        bundle = []
        for amt, n in need_c.items():
            bundle.extend([int(amt)] * int(n))
        if bundle:
            executor.logger.info(
                f"[囤体] 领邮并包 short/过4点 amounts={bundle} "
                f"(距重置≈{hours_to_reset:.2f}h thr={thr:.2f}h)"
            )
            return bundle
        return claim_amts
    except Exception as _be:
        try:
            executor.logger.debug(f"[囤体] 领邮并包跳过: {_be}")
        except Exception:
            pass
        return claim_amts


class ClaimMailHandler(ActionHandler):
    action = ACTION_CLAIM_MAIL

    def handle(self, executor, state, step) -> bool:
        meta = step.get("meta") or {}
        try:
            cfg_dir = config_dir_of(executor)
            inv_srv = InventoryService(cfg_dir)

            if bool(meta.get("scan_only")):
                return _claim_mail_scan_only(executor, step, cfg_dir, inv_srv)

            claim_amts = _claim_amounts_from_step(step)

            # 领前扫一次，拿现有包（也给失败回退用）
            pre_bags = _pre_scan_bags_before_claim(executor, cfg_dir, inv_srv)

            # 本批 + 撑不过下一个 04:00 的短邮一并领
            claim_amts = _bundle_short_mail_claims(executor, pre_bags, claim_amts)

            # 游戏 mail 实现是「一键领取」全领；若只想短邮，仍只能全领或手选。
            # 囤体策略：到点领邮 = 进邮箱一键领（短+本批），长邮若也被领到由回扫修正库存。
            # 执行前明示差异：计划面额只是估算口径，设备端实际是一键全领。
            _notify(
                executor,
                "囤体：即将一键领取邮箱",
                "游戏侧只支持一键全领：本次会把邮箱内所有邮件一并领走（含长时囤货邮），"
                "计划里的面额只是估算口径；领完将重扫邮箱按实况修正库存。"
                "如需逐封精确领取，请在本步执行前手动处理邮箱。",
            )
            ok = _run_existing(executor, "mail")
            if not ok:
                # 结果未知（可能部分领取）：重扫邮箱按实况回写，
                # 但不按面额扣台账、不估算体力，也不把本步记成成功。
                executor.logger.warning(
                    "[囤体] 一键领邮未确认成功：重扫核对实况，本步保持未完成"
                )
                _notify(
                    executor,
                    "囤体：领邮未确认",
                    "邮箱领取未确认成功，将重扫核对；下一轮自动重试",
                )
                _refresh_ap_after_gain(
                    executor,
                    reason="领邮",
                    rescan_mail=True,
                    claimed_amounts=None,
                    fallback_add=0,
                )
                return False
            # 关键：领邮后读主界面体力 + 重扫剩余邮箱
            info = _refresh_ap_after_gain(
                executor,
                reason="领邮",
                rescan_mail=True,
                claimed_amounts=claim_amts or None,
                fallback_add=0,
            )
            if isinstance(step.get("meta"), dict):
                if info.get("ap") is not None and int(info.get("ap") or -1) >= 0:
                    step["meta"]["ap_after"] = int(info["ap"])
                if info.get("mail_ap") is not None:
                    step["meta"]["mail_after"] = int(info["mail_ap"])
                if claim_amts:
                    step["meta"]["claim_amounts"] = list(claim_amts)
            return True
        except Exception as e:
            executor.logger.error(f"[囤体] 领邮/识别异常: {e}")
            _notify(executor, "囤体领邮", str(e))
            return False


class ClaimCafeHandler(ActionHandler):
    action = ACTION_CLAIM_CAFE

    def handle(self, executor, state, step) -> bool:
        note = step.get("note") or ""
        try:
            # 咖啡厅只管"领过且过 24h"：用时间戳而非游戏日字符串，
            # 避免 04:00 重置后过 1 分钟又能再领
            claimed_at = str(_cfg_get(executor, "hoard_ap_cafe_claimed_at", "") or "")
            if claimed_at:
                try:
                    last = datetime.fromisoformat(claimed_at.replace("T", " ")[:19])
                    if (datetime.now() - last).total_seconds() < 24 * 3600:
                        executor.logger.info("[囤体] 咖啡厅领过不足 24h，跳过")
                        return True
                except Exception:
                    pass
            if "补做" in str(note) and str(
                _cfg_get(executor, "hoard_ap_mail_after_cafe", "") or ""
            ).strip():
                executor.logger.info("[囤体] 补做咖啡但已有咖啡后邮量记录，跳过")
                return True
        except Exception:
            pass
        claimed_ok = False
        try:
            import module.hoard_ap.cafe_claim as cafe_claim
            from module.hoard_ap.scheduler_filter import (
                begin_hoard_internal,
                end_hoard_internal,
            )

            begin_hoard_internal(executor)
            try:
                claimed_ok = bool(cafe_claim.implement(executor))
            finally:
                end_hoard_internal(executor)
        except Exception as e:
            executor.logger.warning(f"[囤体] cafe_reward_claim 异常: {e}")
            claimed_ok = False
        if not claimed_ok:
            # 不确定是否领到：不记当日已领、不推进计划，下一轮重试
            executor.logger.warning(
                "[囤体] 咖啡领奖未确认：不记当日已领，保持可重试"
            )
            _notify(
                executor,
                "囤体咖啡领奖未完成",
                "咖啡厅奖励未确认领到；下一轮自动重试，也可手动进咖啡厅领取",
            )
            return False
        try:
            cfg_set = getattr(executor, "config", None)
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if cfg_set is not None and hasattr(cfg_set, "set"):
                cfg_set.set("hoard_ap_cafe_claimed_at", now_iso)
            elif cfg_set is not None:
                setattr(getattr(cfg_set, "config", cfg_set), "hoard_ap_cafe_claimed_at", now_iso)
        except Exception as _ce:
            try:
                executor.logger.warning(f"[囤体] 咖啡已领标记写入失败: {_ce}")
            except Exception:
                pass
        try:
            executor.to_main_page()
        except Exception:
            pass
        # 咖啡体进邮：重扫邮箱；角色体也可能被顶满，读一次当前体
        _refresh_ap_after_gain(
            executor, reason="领咖啡", rescan_mail=True, fallback_add=0
        )
        return True


class UseApCardHandler(ActionHandler):
    action = ACTION_USE_AP_CARD

    def handle(self, executor, state, step) -> bool:
        amount = int(step.get("amount") or 0)
        note = step.get("note") or ""
        _notify(
            executor,
            "囤体：请使用体力卡",
            note or f"请使用体力卡 +{amount}（可在满 999 时进邮）",
        )
        return True


class NotifyHandler(ActionHandler):
    action = ACTION_NOTIFY

    def handle(self, executor, state, step) -> bool:
        mode = step.get("mode") or "auto"
        note = step.get("note") or ""
        action = step.get("action") or ACTION_NOTIFY
        if mode != "manual":
            executor.logger.info(f"[囤体] {note or action}")
            return True
        _notify(executor, "囤体需要你操作", note or action)
        return True


class WaitHandler(ActionHandler):
    action = ACTION_WAIT

    def handle(self, executor, state, step) -> bool:
        deadline = step.get("deadline")
        dt = _parse_step_when(deadline) if deadline else None
        if dt:
            delay = max(0, int((dt - datetime.now()).total_seconds()))
            executor.next_time = min(delay, 6 * 3600)
        else:
            executor.next_time = 600
        return True


class HoldHandler(ActionHandler):
    action = ACTION_HOLD

    def handle(self, executor, state, step) -> bool:
        executor.next_time = 1800
        return True


class SpendReadyHandler(ActionHandler):
    action = ACTION_SPEND_READY

    def handle(self, executor, state, step) -> bool:
        note = step.get("note") or ""
        meta = step.get("meta") or {}
        # 过点且标 expired：只提示，绝不自动清
        if meta.get("expired"):
            _notify(
                executor,
                "囤体：已超过花体时刻",
                note or "请本人自行花体；系统不再自动清体",
            )
            try:
                from module.hoard_ap.constants import PHASE_SPEND_READY

                state.phase = PHASE_SPEND_READY
            except Exception:
                pass
            return True

        # 到点花体自动清体：prefer_clear（主页三选一）非空时自动清，
        # 不再仅靠独立的 spend_auto_clear 开关（默认关=用户没选清体去向）
        auto_clear = False
        try:
            prefer_val = str(_cfg_get(executor, "hoard_ap_prefer_clear", "") or "").strip()
            spend_auto = bool(_cfg_get(executor, "hoard_ap_spend_auto_clear", False))
            auto_clear = bool(prefer_val) or spend_auto
        except Exception:
            auto_clear = False
        # 去向：优先 clear_modes（与清体去向同一套），再 clear_mode；主页 prefer 由 _run_clear 覆盖
        clear_mode = (
            meta.get("clear_modes")
            or meta.get("clear_mode")
            or _cfg_get(executor, "hoard_ap_clear_modes", "")
            or _cfg_get(executor, "hoard_ap_clear_mode", CLEAR_MODE_ACTIVITY)
        )
        prefer = ""
        try:
            prefer = str(_cfg_get(executor, "hoard_ap_prefer_clear", "") or "").strip()
        except Exception:
            prefer = ""
        prefer_cn = {
            "normal": "普通多倍",
            "hard": "困难多倍",
            "mainline": "普通多倍",  # 旧兼容
            "special": "特别委托3倍",
            "high_value": "高价值活动",
        }.get(prefer, "")
        if auto_clear:
            ok = _run_clear(executor, 0, clear_mode)
            if not ok:
                _notify(
                    executor,
                    "囤体：到点花体清体未完成",
                    (note or "请本人接手花体/清体")
                    + (f"（优先：{prefer_cn}）" if prefer_cn else ""),
                )
            else:
                executor.logger.info(
                    "[囤体] 到点花体已按清体去向自动清到≈0"
                    + (f"（优先：{prefer_cn}）" if prefer_cn else "")
                )
        else:
            tip = note or "请上线花体"
            if prefer_cn:
                tip = f"{tip}｜主页优先：{prefer_cn}（拦截其它耗体）"
            else:
                tip = f"{tip}｜清体去向与主页三选一共用，可开「到点花体-自动清体」"
            _notify(executor, "囤体：到点花体", tip)
        try:
            from module.hoard_ap.constants import PHASE_SPEND_READY

            state.phase = PHASE_SPEND_READY
        except Exception:
            pass
        # 花体后短间隔再检（不立刻放开日常清体）
        executor.next_time = 600
        return True


_HANDLERS: List[Type[ActionHandler]] = [
    ClearApHandler,
    EnsureHeadroomHandler,
    BuyTubesHandler,
    FreeBuyHandler,
    ClaimTaskHandler,
    ClaimGroupHandler,
    ClaimJjcHandler,
    ClaimMailHandler,
    ClaimCafeHandler,
    UseApCardHandler,
    NotifyHandler,
    WaitHandler,
    HoldHandler,
    SpendReadyHandler,
]


def _find_handler(action: str) -> Optional[ActionHandler]:
    for cls in _HANDLERS:
        if cls.can_handle(action):
            return cls()
    return None


def execute_step(executor, state: HoardRuntimeState, step: dict) -> bool:
    """动作分发入口：临时包裹内部旗标，保证不误拦自己。"""
    from module.hoard_ap.scheduler_filter import begin_hoard_internal, end_hoard_internal

    cfg_dir = config_dir_of(executor)
    begin_hoard_internal(executor, str(cfg_dir or "."))
    try:
        action = step.get("action") or ""
        mode = step.get("mode") or "auto"
        note = step.get("note") or ""
        meta = step.get("meta") or {}
        state.phase = phase_from_step_action(action)
        executor.logger.info(
            f"[囤体] step#{state.step_index} {action} ({mode}) {note}"
        )

        if GuardMixin.block_after_reset(
            executor, action, note, meta, step.get("when")
        ):
            # 被保护正确阻止：推进计划（不重试），但不记成功
            if isinstance(step.get("meta"), dict):
                step["meta"]["_blocked_skip"] = True
            return True

        # 临期邮监视优先
        if action == ACTION_NOTIFY and meta.get("urgent_mail_watch"):
            return UrgentMailWatchHandler().handle(executor, state, step)

        # 日标/阶段说明：只写日志
        if action == ACTION_NOTIFY and mode != "manual":
            executor.logger.info(f"[囤体] {note or action}")
            return True

        if action == ACTION_SPEND_READY:
            return SpendReadyHandler().handle(executor, state, step)

        if mode == "manual":
            _notify(executor, "囤体需要你操作", note or action)
            return True

        handler = _find_handler(action)
        if handler is None:
            executor.logger.error(f"[囤体] 未知动作 {action}，中止计划")
            state.phase = PHASE_ABORTED
            state.last_error = f"未知动作: {action}"
            return False
        return handler.handle(executor, state, step)
    finally:
        end_hoard_internal(executor)
