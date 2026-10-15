"""囤体执行器：scheduler 任务 `hoard_ap` 的 implement。

职责：
1. 若开启且无计划 → 生成计划并 Armed
2. 按 step_index 执行到期步骤（自动动作调现有 module / purchase_ap）
3. 手动步骤只推送提醒
4. 维护相位，供 scheduler 冲突过滤使用

注意：买管 UI 点击坐标在国服常见布局上给出合理默认，若识别失败会 notify 并跳过，不硬崩。
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Optional

from core.notification import notify

from module.hoard_ap.constants import (
    ACTION_BUY_TUBES,
    ACTION_CLAIM_CAFE,
    ACTION_CLAIM_MAIL,
    ACTION_CLAIM_GROUP,
    ACTION_CLAIM_JJC,
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
    CLEAR_MODE_MAINLINE,
    CLEAR_MODE_NOTIFY_ONLY,
    PHASE_ABORTED,
    PHASE_ARMED,
    PHASE_DONE,
    PHASE_IDLE,
    TUBE_AP,
)
from module.hoard_ap.data_service import (
    HoardDataService,
    InventoryService,
    config_dir_of,
)
from module.hoard_ap.planner import build_plan_from_user_config
from module.hoard_ap.state import (
    HoardRuntimeState,
    append_mail_ledger,
    is_active_phase,
    load_state,
    phase_from_step_action,
    save_state,
)


def _cfg_get(self, key: str, default=None):
    return getattr(self.config, key, default)


def _enabled(self) -> bool:
    return bool(_cfg_get(self, "hoard_ap_enabled", False))


def _notify(self, title: str, body: str) -> None:
    try:
        self.logger.info(f"[囤体] {title}: {body}")
    except Exception:
        pass
    try:
        notify(title=title, body=body)
    except Exception:
        pass
    # 可选接入 pushkit（完成/错误类由主循环处理；这里只 toast）
    try:
        if bool(_cfg_get(self, "push_after_completion", False)):
            from core.pushkit import push_json, push_serverchan, push_feishu

            data = {"title": title, "desp": body}
            if getattr(self.config, "push_json", ""):
                push_json(self.logger, self.config.push_json, data)
            if getattr(self.config, "push_serverchan", ""):
                push_serverchan(
                    self.logger,
                    f"https://sctapi.ftqq.com/{self.config.push_serverchan}.send",
                    data,
                )
            if getattr(self.config, "push_feishu", ""):
                push_feishu(self.logger, self.config.push_feishu, data)
    except Exception:
        pass


def _parse_step_when(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            return None


def arm_plan(self, state: HoardRuntimeState, force: bool = False) -> HoardRuntimeState:
    if state.plan and not force and is_active_phase(state.phase):
        return state
    plan = build_plan_from_user_config(self.config)
    # 硬拦：花体时刻已过期 → 不 arm 旧计划，需人工改期
    spend_at_dt = getattr(plan, "spend_at", None)
    if spend_at_dt is not None and spend_at_dt < datetime.now():
        state.phase = PHASE_ABORTED
        state.last_error = (
            f"花体时刻 {spend_at_dt.strftime('%Y-%m-%d %H:%M')} 已过期"
        )
        state.notes.append("expired_spend_at")
        self.logger.warning(
            f"[囤体] 花体时刻 {spend_at_dt} 已过期，拒绝 arm 旧计划"
        )
        _notify(
            self,
            "囤体花体时刻已过期",
            f"花体时刻 {spend_at_dt.strftime('%m-%d %H:%M')} 已过，"
            "请重新设置花体时刻后再启用囤体",
        )
        return state
    try:
        from module.hoard_ap.narrative import render_plan_narrative, first_actionable_when

        narrative = render_plan_narrative(plan)
        plan_dict = plan.to_dict()
        plan_dict["narrative"] = narrative
    except Exception as _n_e:
        try:
            self.logger.debug(f"[囤体] 计划文案降级为时间轴: {_n_e}")
        except Exception:
            pass
        narrative = plan.timeline_text()
        plan_dict = plan.to_dict()
        plan_dict["narrative"] = narrative
    state.plan = plan_dict
    state.step_index = 0
    state.phase = PHASE_ARMED
    state.armed_at = datetime.now().isoformat(sep=" ", timespec="seconds")
    state.notes.append(f"plan armed, steps={len(plan.steps)}")
    self.logger.info("[囤体] 计划已生成:\n" + narrative)
    # 调度 next_tick 对齐计划开始，避免 1970-01-01
    try:
        from module.hoard_ap.narrative import first_actionable_when
        import os, json, time as _time

        start_when = first_actionable_when(plan)
        delay = max(30, int((start_when - datetime.now()).total_seconds()))
        self.next_time = min(delay, 6 * 3600)
        cfg_dir = getattr(self, "config_path", None) or getattr(
            getattr(self, "config_set", None), "config_dir", None
        )
        if cfg_dir:
            event_path = os.path.join(cfg_dir, "event.json")
            if os.path.isfile(event_path):
                with open(event_path, "r", encoding="utf-8") as f:
                    events = json.load(f)
                ts = int(start_when.timestamp())
                if ts < int(_time.time()):
                    ts = int(_time.time()) + 30
                for ev in events:
                    if ev.get("func_name") == "hoard_ap" or ev.get("event_name") == "囤体":
                        ev["next_tick"] = ts
                # 原子写：调度线程每 tick 裸读 event.json（无容错），
                # 半截文件会直接把调度读崩。
                tmp = event_path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(events, f, ensure_ascii=False, indent=2)
                os.replace(tmp, event_path)
            try:
                with open(os.path.join(cfg_dir, "hoard_ap_plan.txt"), "w", encoding="utf-8") as f:
                    f.write(narrative)
            except Exception as _w_e:
                try:
                    self.logger.warning(f"[囤体] 计划文本写入失败: {_w_e}")
                except Exception:
                    pass
    except Exception as _e:
        try:
            self.logger.warning(f"[囤体] next_tick 对齐失败: {_e}")
        except Exception:
            pass
    # 不再弹又臭又长的日期框；日志已有全文
    return state


def _current_step(state: HoardRuntimeState) -> Optional[dict]:
    if not state.plan:
        return None
    steps = state.plan.get("steps") or []
    if state.step_index < 0 or state.step_index >= len(steps):
        return None
    return steps[state.step_index]


def _advance(state: HoardRuntimeState) -> None:
    state.step_index += 1
    if not state.plan:
        return
    steps = state.plan.get("steps") or []
    if state.step_index >= len(steps):
        # 花体窗口已到过：保持 SpendReady，继续压制自动扫荡清体
        # （若直接 Done，调度会放开 special/activity 把「花体」当成清体去向乱清）
        try:
            from module.hoard_ap.constants import PHASE_SPEND_READY

            had_spend = False
            for s in steps:
                if str(s.get("action") or "") == "spend_ready":
                    md = s.get("meta") or {}
                    # 只有花体步骤真的执行过才算「窗口已到过」；
                    # 旧写法带 `or True` 恒真，计划没跑到花体也会锁进
                    # SpendReady，长期压制日常清体。
                    if md.get("done_ok") or s.get("done_ok"):
                        had_spend = True
                        break
            state.phase = PHASE_SPEND_READY if had_spend else PHASE_DONE
        except Exception:
            state.phase = PHASE_DONE


def _read_ap_safe(self, fallback: int = -1, *, to_main: bool = False) -> int:
    """读当前体力；空 OCR / 活动页误读时回主页再读。

    返回 -1 表示彻底失败（调用方勿把 -1 当「已清到 0」）。
    """
    def _once() -> int:
        try:
            v = self.get_ap(True)
        except Exception:
            return -99999
        if v is None:
            return -99999
        try:
            n = int(v)
        except Exception:
            try:
                s = str(v).strip()
                # "869/2315" 误读 → 取 / 前
                if "/" in s:
                    s = s.split("/")[0].strip()
                s = s.replace(",", "").replace(" ", "")
                if not s:
                    return -99999
                n = int(float(s))
            except Exception:
                return -99999
        # 明显垃圾：空读常变成 0/1/5；主界面正常 0~999（或稍超）
        if n < 0 or n > 5000:
            return -99999
        return n

    n = _once()
    if n == -99999 or (to_main and n <= 5):
        try:
            self.to_main_page()
        except Exception:
            pass
        try:
            import time as _t
            _t.sleep(0.45)
        except Exception:
            pass
        n = _once()
    if n == -99999:
        return int(fallback) if fallback >= 0 else -1
    return n



def _sync_current_ap_to_inventory(self, ap: int) -> None:
    """清体/读体成功后回写「当前体力」到 inventory（事实来源）+ 镜像 config。"""
    try:
        ap = int(ap)
    except Exception:
        return
    if ap < 0:
        return
    try:
        cfg_dir = config_dir_of(self)
        InventoryService(str(cfg_dir)).set_current_ap(
            ap, cfg=getattr(self, "config", None)
        )
    except Exception:
        pass


def _resolve_clear_modes(self, clear_mode: str) -> list:
    """清体去向解析。

    多选去向**固定顺序**（与计划拆解一致）：交流会 → 特殊委托 → 活动 → 主线，
    不按配置字符串原始顺序（避免先点活动/主线）；主页「优先清体」覆盖默认去向。
    """
    raw = clear_mode or CLEAR_MODE_ACTIVITY
    try:
        multi = getattr(self.config, "hoard_ap_clear_modes", "") or ""
        if multi:
            raw = multi
    except Exception:
        pass
    prefer = ""
    try:
        prefer = str(
            getattr(self.config, "hoard_ap_prefer_clear", "") or ""
        ).strip().lower()
    except Exception:
        prefer = ""
    if prefer == "mainline":
        raw = "mainline"
    elif prefer == "special":
        raw = "special"
    elif prefer == "high_value":
        # 晚开活动 → 只提醒不扫
        try:
            from module.hoard_ap.scheduler_filter import _high_value_is_manual
            from module.hoard_ap.data_service import config_dir_of as _cd

            if _high_value_is_manual(_cd(self)):
                raw = CLEAR_MODE_NOTIFY_ONLY
            else:
                raw = "activity"
        except Exception:
            raw = "activity"
    configured = [m.strip() for m in str(raw).split(",") if m.strip()]
    if not configured:
        configured = [CLEAR_MODE_ACTIVITY]

    # 固定优先级
    preferred = ["scrimmage", "special", "activity", "mainline", CLEAR_MODE_ACTIVITY, CLEAR_MODE_MAINLINE]
    modes: list = []
    seen = set()
    for p in preferred:
        for m in configured:
            ml = m.lower() if isinstance(m, str) else m
            if m in (p, CLEAR_MODE_ACTIVITY if p == "activity" else p) or ml == p:
                if m not in seen and m not in ("notify_only", CLEAR_MODE_NOTIFY_ONLY):
                    modes.append(m if m in configured else p)
                    seen.add(m)
                    seen.add(p)
    for m in configured:
        if m not in seen and m not in ("notify_only", CLEAR_MODE_NOTIFY_ONLY):
            modes.append(m)
            seen.add(m)
    if not modes:
        if configured == ["notify_only"] or (
            len(configured) == 1 and configured[0] == CLEAR_MODE_NOTIFY_ONLY
        ):
            modes = configured
        else:
            # 只保留用户配置的去向，禁止默默塞进主线
            modes = [m for m in configured if m not in ("notify_only", CLEAR_MODE_NOTIFY_ONLY)]
            if not modes:
                modes = ["activity"]
    return modes


def _read_ap_with_fallback(self) -> int:
    """读体力：失败时优先用库存/配置里的已知值，禁止默认当成 999 去狂清。

    全部失败返回 -1（已打错误日志并通知）。
    """
    cur = _read_ap_safe(self, fallback=-1, to_main=True)
    if cur < 0:
        self.logger.warning("[囤体] 读体力失败，回主页后再读")
        try:
            self.to_main_page()
        except Exception:
            pass
        try:
            import time as _t
            _t.sleep(0.6)
        except Exception:
            pass
        cur = _read_ap_safe(self, fallback=-1, to_main=True)
    if cur >= 0:
        return cur
    known = -1
    try:
        from module.hoard_ap.inventory import project_display

        cfg_dir = config_dir_of(self)
        inv = InventoryService(str(cfg_dir)).load()
        disp = project_display(inv)
        known = int(disp.get("current_ap") or inv.current_ap or -1)
    except Exception:
        known = -1
    if known < 0:
        try:
            cfg = getattr(self, "config", None)
            raw = None
            if cfg is not None:
                raw = getattr(cfg, "hoard_ap_current_ap", None)
                if raw is None and hasattr(cfg, "config"):
                    raw = getattr(cfg.config, "hoard_ap_current_ap", None)
            if raw is not None and str(raw).strip() != "":
                known = int(float(str(raw).strip()))
        except Exception:
            known = -1
    if known >= 0:
        self.logger.warning(f"[囤体] OCR 仍失败，沿用已知体力≈{known}（不用 999 瞎清）")
        return known
    self.logger.error("[囤体] 读体力连续失败且无已知值，中止本次清体（请回主界面后重试）")
    _notify(self, "囤体读体力失败", "主界面 OCR 读不到体力，已中止清体，避免按 999 误清")
    return -1


def _normalize_activity_sweep_times(self) -> None:
    """确保活动次数配置是数字列表（-1=扫到没体），避免字符串比较。"""
    try:
        cfg = getattr(self, "config", None)
        if cfg is not None:
            raw_t = getattr(cfg, "activity_sweep_times", None)
            if isinstance(raw_t, str):
                parts = [p.strip() for p in raw_t.replace("，", ",").split(",") if p.strip()]
                nums = []
                for p in parts:
                    try:
                        nums.append(float(p))
                    except Exception:
                        nums.append(-1.0)
                if nums:
                    try:
                        if hasattr(cfg, "set"):
                            cfg.set("activity_sweep_times", nums)
                        else:
                            setattr(cfg, "activity_sweep_times", nums)
                    except Exception:
                        pass
    except Exception:
        pass


def _clear_mode_dispatch(self, mode: str, target_ap: int) -> bool:
    """单去向实际扫荡；异常抛给调用方换下一个去向。"""
    if mode in (CLEAR_MODE_ACTIVITY, "activity"):
        import module.sweep_activity as sweep_activity
        _normalize_activity_sweep_times(self)
        return bool(sweep_activity.implement(self))
    if mode in (CLEAR_MODE_MAINLINE, "mainline"):
        import module.explore_tasks.sweep_task as sweep_task
        # 困难优先于普通（少量消耗时更接近交流会后的补量）
        ok = True
        if getattr(self, "flag_run", True):
            try:
                ok = bool(sweep_task.sweep_hard_task(self)) and ok
            except Exception as e:
                # 异常必须失真：旧写法吞掉异常保持 ok=True，
                # 会把没扫成的困难记成扫过
                self.logger.warning(f"[囤体] 困难扫荡异常: {e}")
                ok = False
        if getattr(self, "flag_run", True):
            cur_m = _read_ap_safe(self, fallback=target_ap + 1, to_main=True)
            if cur_m < 0:
                cur_m = target_ap + 1
            if cur_m > target_ap:
                ok = bool(sweep_task.sweep_normal_task(self)) and ok
        return ok
    if mode == "special":
        import module.clear_special_task_power as special
        return bool(special.implement(self))
    if mode == "scrimmage":
        import module.scrimmage as scrimmage
        return bool(scrimmage.implement(self))
    return False


def _finish_clear(self, target_ap: int, cur: int) -> bool:
    """全部去向跑完后的清体结果判定。

    目标 0 = 尽量花光：整次消耗后常剩个位数～十几，≤20 即成功，
    不要卡死在「必须 =0」；非 0 目标允许 +5 宽限。
    """
    cur_end = _read_ap_safe(self, fallback=-1, to_main=True)
    if cur_end < 0:
        cur_end = cur
    soft_ok = 20
    if int(target_ap) <= 0:
        thresh = soft_ok
    else:
        thresh = int(target_ap) + 5
    if cur_end > thresh:
        self.logger.error(
            f"[囤体] 清体未达标：结束 AP≈{cur_end} 仍 > 目标 {target_ap}（阈值≤{thresh}）"
        )
        _notify(
            self,
            "囤体清体未完成",
            f"体力仍≈{cur_end}，目标≤{target_ap}（允许≤{thresh}）。请检查清体去向或重试。",
        )
        return False
    if int(target_ap) <= 0 and cur_end > 0:
        self.logger.info(
            f"[囤体] 清体完成：AP≈{cur_end}≤{soft_ok}（目标0，余数不足一次扫荡，算成功）"
        )
    if cur_end >= 0:
        _sync_current_ap_to_inventory(self, cur_end)
    return True


def _run_clear(self, target_ap: int, clear_mode: str) -> bool:
    """清体到 target_ap。

    多选去向**固定顺序**（与计划拆解一致）：
    交流会 → 特殊委托 → 活动 → 主线
    不按配置字符串原始顺序（避免先点活动/主线）。
    """
    modes = _resolve_clear_modes(self, clear_mode)

    cur = _read_ap_with_fallback(self)
    if cur < 0:
        return False
    # 目标 0：≤20 即够（不足一次扫荡）
    if int(target_ap) <= 0 and cur <= 20:
        self.logger.info(f"[囤体] AP={cur}≤20（目标0），视为清体完成")
        _sync_current_ap_to_inventory(self, cur)
        return True
    if cur <= target_ap:
        self.logger.info(f"[囤体] AP={cur} 已 <= 目标 {target_ap}，无需清体")
        _sync_current_ap_to_inventory(self, cur)
        return True

    if modes == ["notify_only"] or (len(modes) == 1 and modes[0] == CLEAR_MODE_NOTIFY_ONLY):
        _notify(
            self,
            "囤体需要清体",
            f"当前体力≈{cur}，请清到 ≤{target_ap} 后，囤体会自动继续",
        )
        # 未真正清体不得记成功：停轮等待用户手动清，清完下一轮自然通过；
        # 拉长重试间隔，避免频繁重复提醒。
        try:
            self.next_time = 1800
        except Exception:
            pass
        return False

    self.logger.info(f"[囤体] 清体顺序={modes}, {cur} → ≤{target_ap}")
    ok_any = False
    try:
        from module.hoard_ap.scheduler_filter import begin_hoard_internal, end_hoard_internal
        begin_hoard_internal(self)
    except Exception as _g_e:
        try:
            self.logger.debug(f"[囤体] 调度闸门不可用，清体期间不拦截其它任务: {_g_e}")
        except Exception:
            pass
        begin_hoard_internal = None  # type: ignore
        end_hoard_internal = None  # type: ignore
    try:
        for mode in modes:
            if mode in ("notify_only", CLEAR_MODE_NOTIFY_ONLY):
                continue
            if not getattr(self, "flag_run", True):
                break
            cur_before = _read_ap_safe(self, fallback=cur, to_main=True)
            if cur_before < 0:
                cur_before = cur
            if int(target_ap) <= 0 and cur_before <= 20:
                return True
            if cur_before <= target_ap:
                return True
            # 活动扫荡前强制回主页，避免在商店/邮箱残留页读 AP 失败后误退
            if mode in (CLEAR_MODE_ACTIVITY, "activity", "scrimmage", "special", CLEAR_MODE_MAINLINE, "mainline"):
                try:
                    self.to_main_page()
                except Exception:
                    pass
            self.logger.info(f"[囤体] 清体去向 → {mode}（当前≈{cur_before}）")
            try:
                ok_any = _clear_mode_dispatch(self, mode, target_ap) or ok_any
            except Exception as e:
                # 单去向失败不整段崩死，换下一个去向
                msg = str(e)
                self.logger.error(f"[囤体] 清体去向 {mode} 失败: {msg}")
                if "Human Take Over" in msg or "Request Human" in msg:
                    _notify(self, "囤体清体需接手", f"{mode}: {msg}")
                    # 不中断其它去向；若用户停脚本 flag_run 会 false
                continue
            # 扫荡后必须回主页再读体（活动页 OCR 常空/读成 1）
            try:
                self.to_main_page()
            except Exception:
                pass
            cur2 = _read_ap_safe(self, fallback=-1, to_main=True)
            if cur2 < 0:
                self.logger.warning("[囤体] 清体后读体失败，不据此判定已清完")
            else:
                self.logger.info(f"[囤体] 清体后 AP≈{cur2}（目标≤{target_ap}）")
                cur = cur2
                _sync_current_ap_to_inventory(self, cur2)
                if cur2 <= target_ap:
                    return True
        return _finish_clear(self, target_ap, cur)
    except Exception as e:
        self.logger.error(f"[囤体] 清体失败: {e}")
        _notify(self, "囤体清体失败", str(e))
        return False
    finally:
        try:
            if end_hoard_internal:
                end_hoard_internal(self)
        except Exception:
            pass


def _run_buy_tubes(self, tubes: int) -> bool:
    import module.purchase_ap as purchase_ap

    tubes = max(0, min(6, int(tubes)))
    if tubes <= 0:
        return True
    need = tubes * TUBE_AP
    try:
        cur = int(self.get_ap(True))
    except Exception:
        cur = -1
    if cur < 0:
        # 读体失败不得当成 0 继续买（真实体力可能已近满）；
        # 交给 purchase_ap 内部再读一次，那里失败会自行返回 False。
        self.logger.warning("[囤体] 买管前读体失败，交由购买流程内部复核")
        cur = 0
    try:
        hard_cap = int(getattr(self.config, "hoard_ap_hard_cap", AP_HARD_CAP) or AP_HARD_CAP)
    except Exception:
        hard_cap = AP_HARD_CAP
    if cur + need > hard_cap:
        self.logger.warning(
            f"[囤体] 买管 headroom 不足: ap={cur}, need={need}"
        )
        return False
    # purchase_ap.implement(self, tubes=...)
    if hasattr(purchase_ap, "implement"):
        return bool(purchase_ap.implement(self, tubes=tubes))
    if hasattr(purchase_ap, "start"):
        # 兼容旧签名
        return bool(purchase_ap.start(self))
    return False


def _run_existing(self, func_name: str) -> bool:
    from core.Baas_thread import func_dict

    fn = func_dict.get(func_name)
    if not fn:
        self.logger.warning(f"[囤体] 未找到模块 {func_name}")
        return False
    from module.hoard_ap.scheduler_filter import (
        begin_hoard_internal,
        end_hoard_internal,
    )

    begin_hoard_internal(self)
    try:
        return bool(fn(self))
    except Exception as e:
        # 第一次执行可能已部分生效（页面跳转/部分领取），
        # 绝不盲目整段重跑——如实报失败，交给上层停轮重试。
        self.logger.warning(f"[囤体] {func_name} 执行异常，按失败处理: {e}")
        return False
    finally:
        end_hoard_internal(self)


def _execute_step(self, state: HoardRuntimeState, step: dict) -> bool:
    """动作分发：真正逻辑在 action_handlers.py（命令模式）。"""
    from module.hoard_ap.action_handlers import execute_step

    return execute_step(self, state, step)


def _rewrite_plan_txt_from_state(config_dir: str, state, logger=None) -> None:
    """执行成功后立刻把时间轴✓与实际完成时间写入 hoard_ap_plan.txt。"""
    import os
    from datetime import datetime as _dt

    def _log(level: str, msg: str) -> None:
        try:
            if logger is not None:
                getattr(logger, level)(msg)
        except Exception:
            pass

    try:
        from module.hoard_ap.execution_log import format_log_section, done_actions, load_log
        from module.hoard_ap.replan import apply_replan_to_state_plan, _compute_done_key
        from module.hoard_ap.narrative import render_plan_narrative
        from module.hoard_ap.planner import HoardPlan, HoardConfig
    except Exception as _imp_e:
        _log("warning", f"[囤体] 刷新计划文本所需模块导入失败，跳过: {_imp_e}")
        return
    plan_dict = dict(state.plan or {})
    if not plan_dict.get("steps"):
        return
    done = list(done_actions(config_dir) or [])
    done_at_map = {}
    try:
        for e in load_log(config_dir):
            if not e.ok:
                continue
            k = str((e.meta or {}).get("done_key") or "").strip()
            if k and e.when:
                done_at_map[k] = e.when
    except Exception as _lm_e:
        _log("debug", f"[囤体] 读执行日志时间戳失败，完成时间展示回退: {_lm_e}")
    plan_dict, _, rep_notes, duty = apply_replan_to_state_plan(
        plan_dict, now=_dt.now(), done_actions=done, step_index=0
    )
    for s in plan_dict.get("steps") or []:
        try:
            k = _compute_done_key(s)
            md = dict(s.get("meta") or {})
            if k in set(done) or md.get("done_ok"):
                md["done_ok"] = True
                md["done_key"] = k
                if k in done_at_map:
                    md["done_at"] = done_at_map[k]
                    md["display_when"] = done_at_map[k]
                s["meta"] = md
                s["done_ok"] = True
        except Exception as _st_e:
            _log("debug", f"[囤体] 单步完成标记刷新失败: {_st_e}")
    try:
        state.plan = plan_dict
    except Exception as _sp_e:
        _log("warning", f"[囤体] 计划回写 state 失败: {_sp_e}")
    cfg = HoardConfig()
    try:
        raw_cfg = plan_dict.get("config") or {}
        if isinstance(raw_cfg, dict):
            for k, v in raw_cfg.items():
                if hasattr(cfg, k):
                    try:
                        setattr(cfg, k, v)
                    except Exception:
                        pass
    except Exception:
        pass
    from module.hoard_ap.narrative import _parse_when

    spend_dt = _parse_when(plan_dict.get("spend_at")) or _dt.now()
    plan_obj = HoardPlan(
        config=cfg,
        generated_at=_dt.now(),
        spend_at=spend_dt,
        steps=list(plan_dict.get("steps") or []),
        summary=dict(plan_dict.get("summary") or {}),
        warnings=list(plan_dict.get("warnings") or []),
    )
    try:
        plan_obj.summary["done_keys"] = list(done)
        plan_obj.summary["compact_head"] = True
    except Exception:
        pass
    body = render_plan_narrative(plan_obj)
    head = []
    for line in (duty.get("summary") or [])[:6]:
        head.append("· " + line)
    log = format_log_section(config_dir, limit=16)
    head.append("【已完成清单，✓为已完成项目】")
    if log and "尚无" not in log and "还没有" not in log:
        head.append(log)
    else:
        head.append("  （还没有成功执行记录）")
    narrative = ("\n".join(head) + "\n\n" if head else "") + body
    plan_dict["narrative"] = narrative
    try:
        state.plan = plan_dict
    except Exception as _sp_e:
        _log("warning", f"[囤体] 计划回写 state 失败: {_sp_e}")
    try:
        path = os.path.join(config_dir or ".", "hoard_ap_plan.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(narrative)
    except Exception as _w_e:
        _log("warning", f"[囤体] 计划文本写入失败: {_w_e}")


def _impl_disabled(self, ds, state) -> bool:
    """囤体未开启：相位立刻 idle，调度过滤不再占用日常。

    返回 True 表示本轮已处理完（调用方直接 return True）。
    """
    if _enabled(self):
        return False
    if state.phase not in (PHASE_IDLE,):
        state.phase = PHASE_IDLE
        try:
            state.notes = (state.notes or [])[-20:] + [
                "hoard disabled on tick → phase idle"
            ]
        except Exception:
            pass
        ds.state.save(state)
    self.logger.info("[囤体] 未开启，已释放调度占用")
    self.next_time = 3600
    return True


def _impl_day_restart_guard(self, config_dir) -> bool:
    """日界重启闸门：贴 04:00 必须先关开游戏，再跑任何囤体步骤。

    否则日界弹窗会卡死后续操作。即使调度 restart 被挤掉也在此兜底。
    返回 True 表示本轮只做重启（next_time 已设好，调用方直接 return True）。
    """
    try:
        now_r = datetime.now()
        if now_r.hour == 4 and now_r.minute == 0 and now_r.second <= 90:
            self.logger.info("[囤体] 贴 04:00：先执行游戏重启，再继续囤体")
            restart_done = False
            try:
                from module.hoard_ap.scheduler_filter import (
                    begin_hoard_internal,
                    end_hoard_internal,
                )

                begin_hoard_internal(self, str(config_dir or "."))
                try:
                    import module.restart as _restart

                    _restart.implement(self)
                    restart_done = True
                finally:
                    end_hoard_internal(self)
            except Exception as _re:
                self.logger.warning(f"[囤体] 04:00 重启失败: {_re}")
                try:
                    # 强制 stop+start
                    if getattr(self, "u2", None) and getattr(self, "package_name", None):
                        self.u2.app_stop(self.package_name)
                        import time as _t

                        _t.sleep(2)
                        self.u2.app_start(self.package_name, None)
                        self.to_main_page()
                        restart_done = True
                except Exception as _re2:
                    self.logger.error(f"[囤体] 强制重启仍失败: {_re2}")
            if restart_done:
                # 确认重启成功才写当日旗标：04:00~04:02 补重启分支据此跳过，
                # 单日幂等；失败不写旗标，下一轮继续重试。
                try:
                    flag_p = os.path.join(
                        str(config_dir or "."), "hoard_ap_day_restart.flag"
                    )
                    with open(flag_p, "w", encoding="utf-8") as f:
                        f.write(now_r.strftime("%Y-%m-%d"))
                except Exception as _fl_e:
                    # 旗标写失败=下一轮会再重启一次，行为安全但要知道
                    self.logger.warning(f"[囤体] 日界重启旗标写入失败: {_fl_e}")
            # 重启后再过 60s 回来，给日界弹窗消化时间
            self.next_time = 60
            return True
        # 04:00:00~04:02 若未确认重启过，也强制一次（防 03:59 任务拖过点）
        if now_r.hour == 4 and now_r.minute <= 2:
            flag_p = os.path.join(str(config_dir or "."), "hoard_ap_day_restart.flag")
            day_key = now_r.strftime("%Y-%m-%d")
            need = True
            try:
                if os.path.isfile(flag_p):
                    with open(flag_p, "r", encoding="utf-8") as f:
                        need = f.read().strip() != day_key
            except Exception:
                need = True
            if need:
                self.logger.info("[囤体] 04:00 窗口内尚未日界重启，补做 restart")
                restart_ok = False
                try:
                    import module.restart as _restart

                    _restart.implement(self)
                    restart_ok = True
                except Exception as _re:
                    self.logger.warning(f"[囤体] 补做 restart 失败: {_re}")
                if restart_ok:
                    # 只有确认成功才写「今天已重启」；失败保持未写，下一轮重试
                    try:
                        with open(flag_p, "w", encoding="utf-8") as f:
                            f.write(day_key)
                    except Exception as _fl_e:
                        # 旗标写失败=下一轮会再重启一次，行为安全但要知道
                        self.logger.warning(f"[囤体] 日界重启旗标写入失败: {_fl_e}")
                self.next_time = 45
                return True
    except Exception as _rr:
        try:
            self.logger.debug(f"[囤体] 日界重启检查跳过: {_rr}")
        except Exception:
            pass
    return False


def _impl_release_spend_phase(self, ds, state) -> None:
    """花体相位只压到「花体时刻后的下一个 04:00」；过日界后放回 Done，恢复日常清体。"""
    try:
        from datetime import timedelta as _td
        from module.hoard_ap.constants import PHASE_SPEND_READY
        from module.hoard_ap.planner import server_day_start

        if state.phase == PHASE_SPEND_READY and state.plan:
            spend_at = None
            try:
                sa = (state.plan or {}).get("spend_at")
                if sa:
                    spend_at = _parse_step_when(str(sa))
            except Exception:
                spend_at = None
            if spend_at is None:
                for s in (state.plan or {}).get("steps") or []:
                    if str(s.get("action") or "") == "spend_ready":
                        spend_at = _parse_step_when(s.get("when") or "")
                        break
            if spend_at is not None:
                # 花体之后的下一个游戏日 04:00
                release = server_day_start(spend_at + _td(hours=1)) + _td(days=1)
                if datetime.now() >= release:
                    state.phase = PHASE_DONE
                    ds.state.save(state)
                    self.logger.info(
                        "[囤体] 花体日已过次日 04:00，解除花体后清体压制"
                    )
    except Exception as _sp_e:
        try:
            self.logger.debug(f"[囤体] 花体解除检查跳过: {_sp_e}")
        except Exception:
            pass


def _impl_hold_aborted(self, ds, state) -> bool:
    """异常停止不得自愈：绝不自动重建计划（重建会清掉失败现场，

    把未完成步骤当新计划重跑）。保持停止，等用户在囤体页重新启用。
    返回 True 表示处于异常停止保持中（调用方直接 return True）。
    """
    if state.phase != PHASE_ABORTED:
        return False
    self.logger.warning(
        "[囤体] 处于异常停止（Aborted）：保持停止，不自动重建计划；"
        "请在囤体页面检查后重新启用"
    )
    marker = "aborted_hold"
    if not state.notes or state.notes[-1] != marker:
        state.notes = (state.notes or [])[-20:] + [marker]
        ds.state.save(state)
        _notify(
            self,
            "囤体已异常停止",
            "上一轮执行出错，囤体已安全停止，不会自动重跑；"
            "请在囤体页面检查后重新启用",
        )
    self.next_time = 1800
    return True


def _impl_arm_and_replan(self, ds, state) -> HoardRuntimeState:
    """arm_plan + 迟到启动：按执行账本把过点步骤挪到现在之后。"""
    # 跨天：plan 是日界前生成的 → 清掉重 build，否则领任务等 done_ok 沿用、新一天漏领
    try:
        from module.hoard_ap.planner import server_day_start
        _gen = (state.plan or {}).get("generated_at")
        if _gen:
            try:
                _gen_dt = datetime.fromisoformat(str(_gen)) if isinstance(_gen, str) else _gen
            except Exception:
                _gen_dt = None
            if _gen_dt is not None and _gen_dt < server_day_start(datetime.now()):
                try:
                    from module.hoard_ap.data_service import _mirror_config
                    for _k in ("hoard_ap_task_claimed", "hoard_ap_lesson_claimed",
                               "hoard_ap_jjc_claimed", "hoard_ap_group_claimed",
                               "hoard_ap_free_buy_claimed"):
                        try:
                            _mirror_config(self.config, _k, False)
                        except Exception:
                            pass
                except Exception:
                    pass
                state.plan = None
                state.step_index = 0
                self.logger.info("[囤体] 跨天：旧 plan 已过期，清已领重规划")
    except Exception:
        pass
    state = arm_plan(self, state, force=False)
    try:
        from module.hoard_ap.replan import apply_replan_to_state_plan

        if state.plan and is_active_phase(state.phase):
            new_plan, new_idx, notes, _duty = apply_replan_to_state_plan(
                state.plan,
                now=datetime.now(),
                done_actions=ds.log.done_actions(),
                step_index=int(state.step_index or 0),
            )
            state.plan = new_plan
            state.step_index = new_idx
            if notes:
                self.logger.info("[囤体] 迟到重算: " + "；".join(notes[:12]))
                ds.state.mark_replanned(state)
            # 打印即将补做的前几步，避免「直接跳清体」看不懂
            try:
                steps_l = list((state.plan or {}).get("steps") or [])
                idx0 = int(state.step_index or 0)
                preview = []
                for s in steps_l[idx0 : idx0 + 8]:
                    preview.append(
                        f"{s.get('when','?')} {s.get('action')}"
                    )
                if preview:
                    self.logger.info("[囤体] 待执行顺序: " + " → ".join(preview))
            except Exception:
                pass
    except Exception as _re:
        try:
            self.logger.warning(f"[囤体] replan 跳过: {_re}")
        except Exception:
            pass
    ds.state.save(state)
    return state


def _impl_pre_mail_steps(self, ds, state, config_dir) -> None:
    """进入执行前：有邮无步骤也先补排（避免只空等 04:00 日常）。"""
    try:
        from module.hoard_ap.replan import (
            ensure_mail_claim_steps_from_inventory,
            reproject_mail_steps_from_inventory,
        )

        if state.plan and is_active_phase(state.phase):
            now0 = datetime.now().replace(second=0, microsecond=0)
            inv0 = ds.inventory.load()
            p0, n0 = reproject_mail_steps_from_inventory(state.plan, inv0, now=now0)
            if p0:
                state.plan = p0
            try:
                hard0 = int(getattr(self.config, "hoard_ap_hard_cap", 999) or 999)
            except Exception:
                hard0 = 999
            # 补排是否需要先清体：优先现场读体，避免库存停在旧 180
            ap_for_ens = int(getattr(inv0, "current_ap", 0) or 0)
            try:
                live_ap = _read_ap_safe(self, fallback=-1, to_main=False)
                if live_ap >= 0:
                    ap_for_ens = int(live_ap)
                    if abs(live_ap - int(getattr(inv0, "current_ap", 0) or 0)) >= 5:
                        _sync_current_ap_to_inventory(self, live_ap)
                        inv0 = ds.inventory.load()
            except Exception:
                pass
            p1, n1 = ensure_mail_claim_steps_from_inventory(
                state.plan,
                inv0,
                now=now0,
                current_ap=ap_for_ens,
                hard_cap=hard0,
            )
            if p1:
                state.plan = p1
            if n0 or n1:
                ds.state.mark_replanned(state, when=now0)
                self.logger.info(
                    "[囤体] 动态重算: "
                    + "；".join((list(n0 or []) + list(n1 or []))[:6])
                )
                try:
                    _rewrite_plan_txt_from_state(config_dir, state, logger=self.logger)
                except Exception:
                    pass
                # 补排后 step_index 指到第一条未完成
                try:
                    steps_x = list((state.plan or {}).get("steps") or [])
                    for i, sx in enumerate(steps_x):
                        md = sx.get("meta") or {}
                        if md.get("done_ok") or sx.get("done_ok"):
                            continue
                        if str(sx.get("action") or "") in (
                            "notify",
                            "wait",
                            "hold",
                        ):
                            continue
                        state.step_index = i
                        break
                except Exception:
                    pass
                ds.state.save(state)
    except Exception as _pre_e:
        try:
            self.logger.debug(f"[囤体] 进场邮补排跳过: {_pre_e}")
        except Exception:
            pass


def _log_step_result(self, ds, state, step: dict, ok: bool, config_dir) -> None:
    """步骤执行后记账：写执行账本 + 回写 step meta 供 UI 打勾。

    清体特判：目标0且实际≤20 时强制记成功（即使上层 ok 被误标）。
    注意：不修改外层 ok，软成功判定另走 _clear_ap_soft_pass。
    """
    try:
        from datetime import datetime as _dt

        meta_w = dict(step.get("meta") or {})
        act = str(step.get("action") or "")
        note_s = str(step.get("note") or "")
        # 与 replan 共用同一 done_key，避免补做改 when 后对不上账本
        try:
            from module.hoard_ap.replan import _compute_done_key
            step_for_key = dict(step)
            step_for_key["meta"] = meta_w
            meta_w["done_key"] = _compute_done_key(step_for_key)
        except Exception:
            meta_w["done_key"] = f"{act}|{_dt.now().strftime('%Y-%m-%d')}"
        ok_log = bool(ok)
        # 被保护跳过的步骤（guard 拦截旧邮）：推进但不记成功
        if meta_w.get("_blocked_skip"):
            ok_log = False
        if act == "clear_ap" and ok_log is False:
            try:
                ap_now = _read_ap_safe(self, fallback=-1, to_main=True)
                tgt = meta_w.get("target_ap")
                if tgt is None and "主堆收工" in note_s:
                    tgt = 0
                if ap_now >= 0 and int(tgt if tgt is not None else 999) <= 0 and ap_now <= 20:
                    ok_log = True
                    self.logger.info(f"[囤体] 清体余AP={ap_now}≤20，记入已完成")
                    _sync_current_ap_to_inventory(self, ap_now)
            except Exception as _sc_e:
                try:
                    self.logger.debug(f"[囤体] 清体软成功判定跳过: {_sc_e}")
                except Exception:
                    pass
        ds.log.append(
            action=act,
            note=note_s,
            ok=ok_log,
            step_index=int(state.step_index or 0),
            meta=meta_w,
        )
        # 写回 step meta 供 UI 打勾
        try:
            done_at = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(step.get("meta"), dict):
                step["meta"]["done_key"] = meta_w.get("done_key")
                step["meta"]["done_ok"] = ok_log
                if ok_log:
                    step["meta"]["done_at"] = done_at
                    step["meta"]["display_when"] = done_at
            if ok_log and state.plan and isinstance(state.plan.get("steps"), list):
                idx = int(state.step_index or 0)
                if 0 <= idx < len(state.plan["steps"]):
                    st = dict(state.plan["steps"][idx])
                    md = dict(st.get("meta") or {})
                    md["done_key"] = meta_w.get("done_key")
                    md["done_ok"] = True
                    md["done_at"] = done_at
                    md["display_when"] = done_at
                    # 保留原定 when 在 meta，展示用 display_when
                    if not md.get("planned_when"):
                        md["planned_when"] = st.get("when")
                    st["meta"] = md
                    state.plan["steps"][idx] = st
                # 立即重写 hoard_ap_plan.txt，打开页就能看到✓与实际完成时间
                try:
                    _rewrite_plan_txt_from_state(config_dir, state, logger=self.logger)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass


def _post_step_replan(self, ds, state, config_dir) -> None:
    """每次执行后：重投影领邮 → 残余邮补排步骤 → 迟到重排。"""
    try:
        from module.hoard_ap.replan import (
            apply_replan_to_state_plan,
            ensure_mail_claim_steps_from_inventory,
            reproject_mail_steps_from_inventory,
        )

        step = _current_step(state) or {}
        if state.plan and not (step.get("meta") or {}).get("_watch_pending"):
            now_r = datetime.now().replace(second=0, microsecond=0)
            inv_snap = ds.inventory.load()
            proj_plan, proj_notes = reproject_mail_steps_from_inventory(
                state.plan, inv_snap, now=now_r
            )
            if proj_plan:
                state.plan = proj_plan

            # 有邮无步骤（主堆领完后残余）→ 自动插入领取
            try:
                hard = int(
                    getattr(self.config, "hoard_ap_hard_cap", 999) or 999
                )
            except Exception:
                hard = 999
            ens_plan, ens_notes = ensure_mail_claim_steps_from_inventory(
                state.plan,
                inv_snap,
                now=now_r,
                current_ap=int(getattr(inv_snap, "current_ap", 0) or 0),
                hard_cap=hard,
            )
            if ens_plan:
                state.plan = ens_plan

            # 迟到补做 / 已完成跳过；不强制改当前 step_index（由 _advance 推进）
            new_plan, _new_idx, replan_notes, _ = apply_replan_to_state_plan(
                state.plan,
                now=now_r,
                done_actions=ds.log.done_actions(),
                step_index=int(state.step_index or 0),
            )
            if new_plan:
                state.plan = new_plan
            ds.state.mark_replanned(state, when=now_r)
            all_notes = (
                list(proj_notes or [])
                + list(ens_notes or [])
                + list(replan_notes or [])
            )
            if all_notes:
                self.logger.info(
                    "[囤体] 动态重算: " + "；".join(all_notes[:6])
                )
            try:
                _rewrite_plan_txt_from_state(config_dir, state, logger=self.logger)
            except Exception:
                pass
    except Exception as _replan_e:
        try:
            self.logger.debug(f"[囤体] 动态重算跳过: {_replan_e}")
        except Exception:
            pass


def _clear_ap_soft_pass(self, step: dict) -> bool:
    """清体软成功：目标0且实际体≤20 → 不中断，记完成并继续。"""
    try:
        if str(step.get("action") or "") != "clear_ap":
            return False
        ap_n = _read_ap_safe(self, fallback=-1, to_main=True)
        tgt = (step.get("meta") or {}).get("target_ap")
        note_x = str(step.get("note") or "")
        if tgt is None and "主堆收工" in note_x:
            tgt = 0
        if ap_n >= 0 and int(tgt if tgt is not None else 999) <= 0 and ap_n <= 20:
            self.logger.info(f"[囤体] 清体软成功 AP≈{ap_n}≤20，继续下一步")
            return True
    except Exception:
        pass
    return False


def _claim_task_soft_pass(self, step: dict) -> bool:
    """领任务软跳过：领不到（按钮非高亮 / 日程未完成 / 未到点）不罢工，
    推进 step_index 继续后续步骤。账本已记 ok=False 不勾已领，下次 replan
    若检测到可领会重排重试；handler 已 notify，这里不再重复打扰。"""
    try:
        act = str(step.get("action") or "")
        if act not in (ACTION_CLAIM_TASK, ACTION_CLAIM_TASK_DAILY_ONLY, "claim_task_daily_only"):
            return False
        self.logger.info(
            "[囤体] 领任务软跳过（无可领 / 未到点），不罢工，继续后续步骤"
        )
        return True
    except Exception:
        return False


def _impl_run_due_steps(self, ds, state, config_dir) -> bool:
    """连续执行所有「已到期 / 即将到期」的 auto 步骤（同批清体+买管一次跑完）。"""
    from datetime import timedelta as _td

    safety = 0
    while safety < 30:
        safety += 1
        step = _current_step(state)
        if not step:
            state.phase = PHASE_DONE
            ds.state.save(state)
            self.logger.info("[囤体] 计划步骤已全部走完")
            self.next_time = 86400
            return True

        # 账本已打✓：直接推进，不重做
        try:
            md_done = step.get("meta") or {}
            if (isinstance(md_done, dict) and md_done.get("done_ok")) or step.get("done_ok"):
                self.logger.info(
                    f"[囤体] step#{state.step_index} 已完成✓，跳过 {step.get('action')}"
                )
                state.step_index = int(state.step_index or 0) + 1
                ds.state.save(state)
                continue
        except Exception:
            pass

        when = _parse_step_when(step.get("when") or "")
        now = datetime.now()
        action = step.get("action") or ""
        # 准点：最多提前 90 秒开跑（03:48 不能当 03:50）。
        # 同秒批次靠 replan 挤在同一分钟，不再用 5 分钟宽限提前整批。
        grace = _td(seconds=90)
        if when and when > now + grace:
            delay = int((when - now).total_seconds())
            self.next_time = max(30, min(delay, 6 * 3600))
            state.phase = phase_from_step_action(action)
            ds.state.save(state)
            self.logger.info(
                f"[囤体] 下一步 {action} 于 {step.get('when')}，"
                f"{self.next_time}s 后再检"
            )
            return True

        ok = _execute_step(self, state, step)
        _log_step_result(self, ds, state, step, ok, config_dir)
        _post_step_replan(self, ds, state, config_dir)
        # 清体软成功：目标0且体≤20 → 不中断，记完成并继续
        if not ok:
            if _clear_ap_soft_pass(self, step):
                ok = True
            elif _claim_task_soft_pass(self, step):
                # 领不到任务不罢工：推进 step_index 继续后续（领邮/花体等），
                # 不勾已领，下次 replan 检测到可领会重排重试
                ok = True
            else:
                state.last_error = f"step {state.step_index} failed"
                ds.state.save(state)
                return False

        # 临期邮监视未完成：不推进 step_index，按 next_time 再来
        if (step.get("meta") or {}).get("_watch_pending"):
            ds.state.save(state)
            if not getattr(self, "next_time", None):
                self.next_time = 120
            self.logger.info(
                f"[囤体] 临期邮监视中，{int(self.next_time)}s 后再识别"
            )
            return True

        # 记录溢出 meta
        meta = step.get("meta") or {}
        overflow = int(meta.get("overflow") or 0)
        if overflow > 0:
            from datetime import timedelta

            from module.hoard_ap.constants import MAIL_TTL_SECONDS

            ov_at = datetime.now()
            append_mail_ledger(
                state,
                overflow,
                ov_at,
                ov_at + timedelta(seconds=MAIL_TTL_SECONDS),
                source=step.get("action") or "",
            )

        _advance(state)
        ds.state.save(state)

        act = step.get("action") or ""
        md = step.get("mode") or "auto"
        # 自动日标说明：不交还调度，立刻跑同批清体/买管
        if act == ACTION_NOTIFY and md != "manual":
            continue
        # wait/hold/花体窗口/人手 才交还调度器
        if act in (
            ACTION_WAIT,
            ACTION_HOLD,
            ACTION_SPEND_READY,
            ACTION_USE_AP_CARD,
        ) or (act == ACTION_NOTIFY and md == "manual"):
            if not getattr(self, "next_time", 0):
                self.next_time = 300
            return True

        # 小憩避免连点过猛
        time.sleep(0.5)

    self.next_time = 300
    return True


def implement(self) -> bool:
    """Scheduler 入口。"""
    # 插件级守卫：非启用/删除（工具启用与修改）→ 整插件不参与任何执行
    try:
        from module.tools.registry import tool_available

        if not tool_available("hoard_ap"):
            try:
                self.logger.info("[囤体] 插件已停用或删除，跳过调度")
            except Exception:
                pass
            return True
    except Exception:
        pass
    config_dir = config_dir_of(self)
    ds = HoardDataService(config_dir)
    state = ds.state.load()

    if _impl_disabled(self, ds, state):
        return True

    # 铁律：贴 04:00（±90s）必须先关开游戏，再跑任何囤体步骤。
    if _impl_day_restart_guard(self, config_dir):
        return True

    try:
        _impl_release_spend_phase(self, ds, state)

        if _impl_hold_aborted(self, ds, state):
            return True

        state = _impl_arm_and_replan(self, ds, state)

        _impl_pre_mail_steps(self, ds, state, config_dir)

        return _impl_run_due_steps(self, ds, state, config_dir)
    except Exception as e:
        self.logger.error(f"[囤体] executor error: {e}")
        state.last_error = str(e)
        state.phase = PHASE_ABORTED
        ds.state.save(state)
        _notify(self, "囤体异常", str(e))
        return False


def get_phase(config_dir: str) -> str:
    return load_state(config_dir).phase
