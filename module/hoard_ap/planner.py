"""囤体纯计划器：无截图、无侧效，只产出时间轴。

核心不变量：
- 自然回复只到软顶（默认 160），绝不因自然回复进邮
- buy_tubes：ap + gain 必须 ≤ 999（永不进邮）
- free_buy/礼包：可进邮（与任务/JJC 相同）
- 可囤来源（任务/小组/JJC/咖啡/体力卡）在满栏时领取 → 溢出进邮（约 24h）
- 目标不只是角色 999，而是花体点附近「999 + 尽量多的近过期邮箱体」
- 国服日界 04:00
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _parse_card_amount(v) -> int:
    """解析体力礼包数量串：'0'/'130'/'130+150' → 0/130/280。"""
    s = str(v or "0").strip()
    if not s:
        return 0
    total = 0
    s = s.replace("＋", "+").replace("，", ",").replace(" ", "")
    for part in s.split("+"):
        for p in part.split(","):
            try:
                total += int(p)
            except Exception:
                pass
    return total


from module.hoard_ap.mail_pad import (
    MailBag,
    bags_from_total_estimate,
    build_pad_plan,
)

from module.hoard_ap.constants import (
    ACTION_BUY_TUBES,
    ACTION_CLAIM_CAFE,
    ACTION_CLAIM_MAIL,
    ACTION_CLAIM_GROUP,
    ACTION_CLAIM_JJC,
    ACTION_CLAIM_TASK,
    ACTION_CLEAR_AP,
    ACTION_ENSURE_HEADROOM,
    ACTION_FREE_BUY,
    ACTION_HOLD,
    ACTION_NOTIFY,
    ACTION_SPEND_READY,
    ACTION_USE_AP_CARD,
    ACTION_WAIT,
    AP_HARD_CAP,
    AP_PER_HOUR,
    AP_SOFT_NATURAL_CAP,
    CAFE_AP_FULL_CAP,
    CAFE_AP_PER_HOUR,
    CLEAR_MODE_ACTIVITY,
    CLEAR_MODE_MAINLINE,
    CLEAR_MODE_NOTIFY_ONLY,
    FREE_BUY_AP,
    GROUP_AP,
    JJC_AP_30,
    JJC_AP_60,
    JJC_BUY_30,
    JJC_BUY_30_60,
    JJC_BUY_NONE,
    MAIL_HANDLE_MARGIN_SECONDS,
    MAIL_TTL_SECONDS,
    SERVER_DAY_RESET_HOUR,
    STRATEGY_SIMPLE,
    STRATEGY_SIMPLE_PLUS,
    STRATEGY_XIUXIAN,
    TASK_LESSON_AP,
    TASK_LOGIN_AP,
    TUBE_AP,
    TUBE_PRICE_TIER1,
    TUBE_PRICE_TIER2,
)


def tube_gain_ap(tubes: int) -> int:
    return int(tubes) * TUBE_AP


def tube_cost_pyroxene(tubes: int) -> int:
    """1-3 管 30/管，4-6 管 60/管。"""
    tubes = int(tubes)
    if tubes <= 0:
        return 0
    if tubes > 6:
        raise ValueError("tubes must be 0..6")
    cost = 0
    for i in range(1, tubes + 1):
        cost += TUBE_PRICE_TIER1 if i <= 3 else TUBE_PRICE_TIER2
    return cost


def jjc_ap_per_day(buy_mode: str, refresh_times: int) -> int:
    """JJC 店每日可买体力 = 单轮 (30 与/或 60) × (刷新次数+1)。"""
    mode = str(buy_mode or JJC_BUY_NONE)
    refresh = max(0, min(3, int(refresh_times or 0)))
    per_round = 0
    if mode == JJC_BUY_30:
        per_round = JJC_AP_30
    elif mode == JJC_BUY_30_60:
        per_round = JJC_AP_30 + JJC_AP_60
    elif mode == JJC_BUY_NONE:
        per_round = 0
    else:
        # 兼容旧：直接给了数字面额
        try:
            return max(0, int(mode))
        except (TypeError, ValueError):
            return 0
    return per_round * (refresh + 1)


# 主堆日邮箱目标：次日 03:50 要「清低后一次领进 999 栏」，故临期邮宜 ≤999，甜区约 950–980
MAIL_STACK_TARGET = 980
MAIL_STACK_HARD = 999


def plan_jjc_under_mail_cap(
    base_mail: int,
    *,
    ap_card_overflow: int = 0,
    target: int = MAIL_STACK_TARGET,
    hard_cap: int = MAIL_STACK_HARD,
    prefer_mode: str = JJC_BUY_30_60,
) -> Dict[str, Any]:
    """在 base_mail 之上选 JJC 买法，使邮箱总量尽量接近 target 且不超过 hard_cap。

    ap_card_overflow：体力卡会让 AP 超过 999 的溢出量（进邮），需从可用空位扣除。
    枚举：刷新 0..3 × 是否买30 × 是否买60。
    返回 {amount, refresh, buy_30, buy_60, mode, note}。
    """
    base_mail = max(0, int(base_mail))
    ap_card_overflow = max(0, int(ap_card_overflow))
    # 体力卡溢出会进邮 → 占用邮箱空位 → JJC 可用空位扣除
    effective_mail = base_mail + ap_card_overflow
    target = max(0, int(target))
    hard_cap = max(0, int(hard_cap))
    room = hard_cap - effective_mail
    if room <= 0 or prefer_mode == JJC_BUY_NONE:
        return {
            "amount": 0,
            "refresh": 0,
            "buy_30": False,
            "buy_60": False,
            "mode": JJC_BUY_NONE,
            "note": (
                f"邮箱已有 {base_mail}+体力卡溢出{ap_card_overflow}"
                f"={effective_mail}，不再买竞技场（硬顶 {hard_cap}）"
            ),
        }

    candidates = []
    for refresh in range(0, 4):
        rounds = refresh + 1
        opts = []
        if prefer_mode == JJC_BUY_30:
            opts = [(True, False)]
        elif prefer_mode == JJC_BUY_NONE:
            opts = [(False, False)]
        else:
            # 30_60：允许只30 / 只60 / 30+60
            opts = [(True, False), (False, True), (True, True)]
        for b30, b60 in opts:
            per = (JJC_AP_30 if b30 else 0) + (JJC_AP_60 if b60 else 0)
            if per <= 0:
                continue
            amt = per * rounds
            if amt <= 0 or amt > room:
                continue
            total = effective_mail + amt
            # 评分：靠近 target；不超过 hard；略偏好少刷新
            score = -abs(total - target) * 10 - refresh
            if total > target:
                score -= (total - target)  # 略罚超 target
            candidates.append((score, amt, refresh, b30, b60, total))

    if not candidates:
        return {
            "amount": 0,
            "refresh": 0,
            "buy_30": False,
            "buy_60": False,
            "mode": JJC_BUY_NONE,
            "note": (
                f"邮箱已有 {base_mail}+体力卡溢出{ap_card_overflow}"
                f"={effective_mail}，剩余空位 {room} 放不下任何竞技场组合"
            ),
        }
    candidates.sort(key=lambda x: (-x[0], x[2], -x[1]))
    _score, amt, refresh, b30, b60, total = candidates[0]
    if b30 and b60:
        mode = JJC_BUY_30_60
        part = "30+60"
    elif b30:
        mode = JJC_BUY_30
        part = "仅30"
    else:
        mode = JJC_BUY_30_60
        part = "仅60"
    return {
        "amount": int(amt),
        "refresh": int(refresh),
        "buy_30": bool(b30),
        "buy_60": bool(b60),
        "mode": mode,
        "note": (
            f"竞技场 +{amt}（{part}，刷新{refresh}次）→ 邮约 {total}"
            f"（目标≈{target}，硬顶{hard_cap}；底座{base_mail}"
            f"{f'+体力卡{ap_card_overflow}' if ap_card_overflow else ''}）"
        ),
    }


def sim_jjc_amount(sim_mail_total: int, cfg: "HoardConfig") -> int:
    """规划侧竞技场估算与执行端对齐。

    执行端（ClaimJjcHandler）会按当时邮箱底座用 plan_jjc_under_mail_cap
    动态选 30/60/刷新组合（邮箱近顶时可能只买 60，甚至不买）；
    规划若恒按满配计，会高估进账、少买管。此处用同一函数估算。
    """
    full = cfg.resolved_jjc_ap()
    if full <= 0 or str(cfg.jjc_buy_mode or "") == JJC_BUY_NONE:
        return full
    try:
        # 体力卡在满 999 时会溢出进邮 → 占用邮箱空位 → JJC 需减去溢出量
        ap_card_overflow = 0
        if getattr(cfg, "use_ap_card", False) and int(getattr(cfg, "ap_card_amount", 0) or 0) > 0:
            ap_card_overflow = int(cfg.ap_card_amount)
        jp = plan_jjc_under_mail_cap(
            int(sim_mail_total or 0),
            ap_card_overflow=ap_card_overflow,
            prefer_mode=str(cfg.jjc_buy_mode),
        )
        return int(jp.get("amount") or 0)
    except Exception:
        return full


def task_ap_amount(include_lesson: bool = True) -> int:
    return TASK_LOGIN_AP + (TASK_LESSON_AP if include_lesson else 0)


def parse_hhmm(value: str) -> Tuple[int, int]:
    parts = str(value).strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"invalid time '{value}', expect HH:MM")
    return int(parts[0]), int(parts[1])


def server_day_start(dt: datetime) -> datetime:
    """国服：当天 04:00 起算的「游戏日」起点。"""
    boundary = dt.replace(hour=SERVER_DAY_RESET_HOUR, minute=0, second=0, microsecond=0)
    if dt < boundary:
        boundary -= timedelta(days=1)
    return boundary


def combine_server_date_and_time(day_start: datetime, hhmm: str) -> datetime:
    """day_start 是某游戏日 04:00；hhmm 是墙上钟点。

    若钟点 < 04:00，落在该游戏日的「次日凌晨」段。
    """
    h, m = parse_hhmm(hhmm)
    candidate = day_start.replace(hour=h, minute=m, second=0, microsecond=0)
    if h < SERVER_DAY_RESET_HOUR:
        candidate += timedelta(days=1)
    return candidate


def estimate_cafe_claimable(
    hours_since_claim: float,
    per_hour: float = CAFE_AP_PER_HOUR,
    full_cap: float = CAFE_AP_FULL_CAP,
    manual_amount: Optional[float] = None,
) -> int:
    if manual_amount is not None:
        return max(0, int(round(manual_amount)))
    raw = max(0.0, float(hours_since_claim)) * float(per_hour)
    return int(round(min(raw, float(full_cap))))


def cafe_after_hours(
    hours: float,
    per_hour: float = CAFE_AP_PER_HOUR,
    full_cap: float = CAFE_AP_FULL_CAP,
) -> int:
    return int(round(min(max(0.0, hours) * per_hour, full_cap)))


@dataclass
class HoardConfig:
    enabled: bool = False
    target_date: str = ""  # YYYY-MM-DD，消费日
    spend_time: str = "20:00"
    tubes: int = 3
    tube_days: int = 2  # 买体力天数 1..3（勤奋默认 2）
    strategy: str = STRATEGY_SIMPLE_PLUS
    clear_mode: str = CLEAR_MODE_ACTIVITY
    clear_modes: str = ""  # 逗号分隔多选，空则用 clear_mode
    use_ap_card: bool = False
    ap_card_amount: int = 150
    cafe_ap_per_hour: float = CAFE_AP_PER_HOUR
    cafe_ap_full_cap: float = CAFE_AP_FULL_CAP
    cafe_claimable_manual: Optional[float] = None
    cafe_hours_since_claim: float = 24.0
    # JJC：模式 + 刷新，替代手填面额
    jjc_buy_mode: str = JJC_BUY_30_60  # none / 30 / 30_60
    jjc_refresh: int = 3  # 0..3
    jjc_ap: int = 0  # 派生；0 表示按 mode/refresh 算
    # 固定面额（不可配，仅兼容）
    task_ap: int = TASK_LOGIN_AP + TASK_LESSON_AP
    group_ap: int = GROUP_AP
    free_buy_ap: int = FREE_BUY_AP
    natural_ap_per_hour: float = AP_PER_HOUR
    natural_soft_cap: int = AP_SOFT_NATURAL_CAP
    hard_cap: int = AP_HARD_CAP
    auto_tubes: bool = False  # tubes 由日期距离自动估
    hold_cafe_until_spend: bool = True  # 花体时咖啡厅仍可领
    xiuxian_clear_time: str = "02:00"
    prefer_overflow_claims: bool = True
    # 现状
    current_ap: Optional[int] = None
    existing_mail_ap: int = 0
    task_claimed: bool = False  # 登陆100已领
    lesson_ready: bool = True  # True=日程50未领/会领；False=日程已领或不要
    lesson_claimed: bool = False  # True=日程50已领（与 UI 开关一致；优先于 lesson_ready）
    jjc_claimed: bool = False
    group_claimed: bool = False
    free_buy_claimed: bool = False
    # 清体去向（计划拆解 / 执行顺序）
    activity_sweep_task_number: str = "1"
    activity_sweep_times: str = "0"
    special_task_times: str = "0,0"
    scrimmage_times: str = "0,0,0"
    mainline_priority: str = ""
    hard_priority: str = ""
    # 原始邮箱明细（计算时注入）
    mail_bags: Optional[List[Dict[str, Any]]] = None

    def resolved_jjc_ap(self) -> int:
        if int(self.jjc_ap or 0) > 0 and self.jjc_buy_mode not in (
            JJC_BUY_NONE,
            JJC_BUY_30,
            JJC_BUY_30_60,
        ):
            return int(self.jjc_ap)
        return jjc_ap_per_day(self.jjc_buy_mode, self.jjc_refresh)

    def lesson_include(self) -> bool:
        """日程 +50 是否计入/去领。UI「已领」→ lesson_claimed=True → 不计入。"""
        if bool(getattr(self, "lesson_claimed", False)):
            return False
        return bool(self.lesson_ready)

    def resolved_task_ap(self) -> int:
        return task_ap_amount(include_lesson=self.lesson_include())

    def resolved_login_ap(self) -> int:
        return 0 if self.task_claimed else int(TASK_LOGIN_AP)

    def resolved_lesson_ap(self) -> int:
        return int(TASK_LESSON_AP) if self.lesson_include() else 0

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "HoardConfig":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in (data or {}).items() if k in known}
        cfg = cls(**kwargs)
        try:
            t = int(cfg.tubes)
        except Exception:
            t = 3
            cfg.auto_tubes = True
        if cfg.auto_tubes:
            # 自动模式：占位 3，真正管数在 build_plan 里按距离估算
            cfg.tubes = 3 if t <= 0 else (6 if t > 6 else t)
        else:
            cfg.tubes = 0 if t < 0 else (6 if t > 6 else t)
        try:
            td = int(getattr(cfg, "tube_days", 1) or 1)
        except Exception:
            td = 1
        cfg.tube_days = 0 if td < 0 else (3 if td > 3 else td)
        # 策略：买管数 > 0 → 勤奋；=0 → 懒人。UI 不再让人选。
        try:
            _tubes_n = int(cfg.tubes or 0)
        except Exception:
            _tubes_n = 0
        if cfg.auto_tubes:
            # 自动管数仍按勤奋轴推演
            cfg.strategy = STRATEGY_XIUXIAN
        elif _tubes_n <= 0:
            cfg.strategy = STRATEGY_SIMPLE
        else:
            cfg.strategy = STRATEGY_XIUXIAN
        # 多选清体
        modes = []
        raw_modes = str(getattr(cfg, "clear_modes", "") or "").strip()
        if raw_modes:
            modes = [x.strip() for x in raw_modes.split(",") if x.strip()]
        if not modes:
            modes = [cfg.clear_mode or CLEAR_MODE_ACTIVITY]
        # 合法化
        allowed = {
            CLEAR_MODE_ACTIVITY,
            CLEAR_MODE_MAINLINE,
            CLEAR_MODE_NOTIFY_ONLY,
            "activity",
            "mainline",
            "special",
            "scrimmage",
            "notify_only",
        }
        modes = [m for m in modes if m in allowed] or [CLEAR_MODE_ACTIVITY]
        cfg.clear_modes = ",".join(modes)
        cfg.clear_mode = modes[0]
        cfg.jjc_refresh = max(0, min(3, int(cfg.jjc_refresh or 0)))
        if cfg.jjc_buy_mode not in (JJC_BUY_NONE, JJC_BUY_30, JJC_BUY_30_60):
            # 旧配置可能只有 jjc_ap 数字
            if int(cfg.jjc_ap or 0) > 0:
                # 尽量反推
                if int(cfg.jjc_ap) >= 360:
                    cfg.jjc_buy_mode = JJC_BUY_30_60
                    cfg.jjc_refresh = 3
                elif int(cfg.jjc_ap) >= 90:
                    cfg.jjc_buy_mode = JJC_BUY_30_60
                    cfg.jjc_refresh = max(0, int(cfg.jjc_ap) // 90 - 1)
                else:
                    cfg.jjc_buy_mode = JJC_BUY_30
            else:
                cfg.jjc_buy_mode = JJC_BUY_30_60
        # 固定值强制
        cfg.group_ap = GROUP_AP
        cfg.task_ap = cfg.resolved_task_ap()
        cfg.jjc_ap = cfg.resolved_jjc_ap()
        try:
            cfg.hard_cap = max(1, int(cfg.hard_cap or AP_HARD_CAP))
        except Exception:
            cfg.hard_cap = AP_HARD_CAP
        try:
            cfg.natural_soft_cap = max(0, min(int(cfg.natural_soft_cap or AP_SOFT_NATURAL_CAP), cfg.hard_cap))
        except Exception:
            cfg.natural_soft_cap = min(AP_SOFT_NATURAL_CAP, cfg.hard_cap)
        try:
            cfg.cafe_ap_full_cap = float(cfg.cafe_ap_full_cap or CAFE_AP_FULL_CAP)
        except Exception:
            cfg.cafe_ap_full_cap = CAFE_AP_FULL_CAP
        if not cfg.cafe_ap_per_hour or float(cfg.cafe_ap_per_hour) <= 0:
            cfg.cafe_ap_per_hour = float(cfg.cafe_ap_full_cap) / 24.0
        return cfg

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["jjc_ap"] = self.resolved_jjc_ap()
        d["task_ap"] = self.resolved_task_ap()
        d["group_ap"] = GROUP_AP
        return d


@dataclass
class PlanStep:
    when: datetime
    action: str
    mode: str  # auto | manual
    note: str = ""
    amount: int = 0
    expect_ap: int = 0
    expect_mail: int = 0
    deadline: Optional[datetime] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "when": self.when.isoformat(sep=" ", timespec="minutes"),
            "action": self.action,
            "mode": self.mode,
            "note": self.note,
            "amount": self.amount,
            "expect_ap": self.expect_ap,
            "expect_mail": self.expect_mail,
            "deadline": self.deadline.isoformat(sep=" ", timespec="minutes")
            if self.deadline
            else None,
            "meta": self.meta,
        }


@dataclass
class MailParcel:
    amount: int
    overflow_at: datetime
    expire_at_override: Optional[datetime] = None
    source: str = ""
    # stack_for_claim = 主堆囤到花体日 03:50 整包领；禁止 0.2h 临期规则动它
    role: str = ""

    @property
    def expire_at(self) -> datetime:
        if self.expire_at_override is not None:
            return self.expire_at_override
        return self.overflow_at + timedelta(seconds=MAIL_TTL_SECONDS)

    @property
    def handle_by(self) -> datetime:
        # 临期处理窗：到期前 30 分钟起就要准备清体领取刷新
        return self.expire_at - timedelta(minutes=30)

    def remain_hours(self, now: datetime) -> float:
        return max(0.0, (self.expire_at - now).total_seconds() / 3600.0)


@dataclass
class HoardPlan:
    config: HoardConfig
    generated_at: datetime
    spend_at: datetime
    steps: List[PlanStep] = field(default_factory=list)
    mail_parcels: List[MailParcel] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(sep=" ", timespec="minutes"),
            "spend_at": self.spend_at.isoformat(sep=" ", timespec="minutes"),
            "config": self.config.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "mail_parcels": [
                {
                    "amount": p.amount,
                    "overflow_at": p.overflow_at.isoformat(sep=" ", timespec="minutes"),
                    "expire_at": p.expire_at.isoformat(sep=" ", timespec="minutes"),
                    "handle_by": p.handle_by.isoformat(sep=" ", timespec="minutes"),
                    "source": getattr(p, "source", "") or "",
                    "role": getattr(p, "role", "") or "",
                    "remain_hours": round(p.remain_hours(self.generated_at), 2),
                }
                for p in self.mail_parcels
            ],
            "warnings": list(self.warnings),
            "summary": dict(self.summary),
        }

    def timeline_text(self) -> str:
        lines = [
            f"囤体计划 | 策略={self.config.strategy} | 管数={self.config.tubes} | "
            f"花体={self.spend_at.strftime('%Y-%m-%d %H:%M')}",
            f"钻石预算≈{tube_cost_pyroxene(self.config.tubes)} | "
            f"买管获得={tube_gain_ap(self.config.tubes)} | "
            f"JJC/日={self.config.resolved_jjc_ap()} | 任务/日={self.config.resolved_task_ap()}",
            "-" * 48,
        ]
        for s in self.steps:
            tag = "AUTO" if s.mode == "auto" else "手动"
            dead = f" | 截止 {s.deadline.strftime('%m-%d %H:%M')}" if s.deadline else ""
            lines.append(
                f"[{tag}] {s.when.strftime('%m-%d %H:%M')}  {s.action:<16} "
                f"ap≈{s.expect_ap:<4} mail≈{s.expect_mail:<4}  {s.note}{dead}"
            )
        if self.warnings:
            lines.append("-" * 48)
            lines.append("警告:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        if self.summary:
            lines.append("-" * 48)
            lines.append(
                "汇总: " + ", ".join(f"{k}={v}" for k, v in self.summary.items())
            )
        return "\n".join(lines)


class _Sim:
    """AP / 邮箱仿真。"""

    def __init__(
        self,
        now: datetime,
        ap: int,
        mail_parcels: Optional[Sequence[MailParcel]] = None,
        natural_per_hour: float = AP_PER_HOUR,
        natural_soft_cap: int = AP_SOFT_NATURAL_CAP,
        hard_cap: int = AP_HARD_CAP,
    ):
        self.hard_cap = max(1, int(hard_cap))
        self.t = now
        self.ap = max(0, min(int(ap), self.hard_cap))
        self.mail: List[MailParcel] = list(mail_parcels or [])
        self.natural_per_hour = float(natural_per_hour)
        self.natural_soft_cap = min(int(natural_soft_cap), self.hard_cap)
        self.steps: List[PlanStep] = []
        self.warnings: List[str] = []
        # 咖啡厅库存仿真（领完从 0 再积）
        self.cafe_stock: float = 0.0
        self.cafe_per_hour: float = CAFE_AP_PER_HOUR
        self.cafe_cap: float = CAFE_AP_FULL_CAP
        self._cafe_last_t: datetime = now

    @property
    def mail_total(self) -> int:
        return sum(p.amount for p in self.mail)

    def set_cafe(self, stock: float, per_hour: float, cap: float) -> None:
        self.cafe_stock = max(0.0, float(stock))
        self.cafe_per_hour = float(per_hour)
        self.cafe_cap = float(cap)
        self._cafe_last_t = self.t

    def _tick_cafe(self, when: datetime) -> None:
        if when <= self._cafe_last_t:
            return
        hours = (when - self._cafe_last_t).total_seconds() / 3600.0
        self.cafe_stock = min(self.cafe_cap, self.cafe_stock + hours * self.cafe_per_hour)
        self._cafe_last_t = when

    def advance_to(self, when: datetime) -> None:
        if when <= self.t:
            self._tick_cafe(when)
            return
        # 自然回复：只到软顶，绝不进邮
        hours = (when - self.t).total_seconds() / 3600.0
        gain = int(hours * self.natural_per_hour)
        if gain > 0 and self.ap < self.natural_soft_cap:
            self.ap = min(self.natural_soft_cap, self.ap + gain)
        self._tick_cafe(when)
        self.t = when

    def _push_mail(self, amount: int, at: datetime, role: str = "") -> None:
        if amount <= 0:
            return
        r = role or str(getattr(self, "_mail_push_role", "") or "")
        self.mail.append(MailParcel(amount=int(amount), overflow_at=at, role=r, source=r))

    def _emit(
        self,
        action: str,
        mode: str,
        note: str = "",
        amount: int = 0,
        deadline: Optional[datetime] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.steps.append(
            PlanStep(
                when=self.t,
                action=action,
                mode=mode,
                note=note,
                amount=amount,
                expect_ap=self.ap,
                expect_mail=self.mail_total,
                deadline=deadline,
                meta=meta or {},
            )
        )

    def ensure_headroom(self, need: int, clear_mode: str, cfg: Optional["HoardConfig"] = None) -> bool:
        need = int(need)
        if self.ap + need <= self.hard_cap:
            return True
        target = max(0, self.hard_cap - need)
        drop = self.ap - target
        recipe_meta = _attach_clear_recipe(cfg, drop) if cfg is not None else {}
        # 先记 ensure，再记具体清体拆解
        mode = "manual" if clear_mode == CLEAR_MODE_NOTIFY_ONLY else "auto"
        self._emit(
            ACTION_ENSURE_HEADROOM,
            mode,
            note=f"买/领直充前需空位 {need} → 清到 {target}",
            amount=drop,
            meta={"target_ap": target, "clear_mode": clear_mode, **recipe_meta},
        )
        # clear_to 会真正改 ap 并写清体步骤
        self.clear_to(
            target,
            clear_mode,
            note=f"清体到 {target}（腾空位 {need}）",
            meta=recipe_meta,
        )
        return True

    def buy_tubes(self, tubes: int, clear_mode: str) -> None:
        if tubes <= 0:
            return
        gain = tube_gain_ap(tubes)
        cost = tube_cost_pyroxene(tubes)
        # 若栏位不够但距离软顶回满还有较长时间，先等到软顶节奏再清/买，避免 999→639 浪费自回
        if self.ap + gain > self.hard_cap:
            need_drop = self.ap + gain - self.hard_cap
            # 无额外上下文时仍 ensure；调用方可先 advance
            self.ensure_headroom(gain, clear_mode)
        if self.ap + gain > self.hard_cap:
            self.warnings.append(
                f"买体 {tubes} 次仍会超过满值 {self.hard_cap}（当前计划 ap={self.ap}），已跳过买体"
            )
            return
        self.ap += gain
        self._emit(
            ACTION_BUY_TUBES,
            "auto",
            note=f"买体 {tubes} 次 +{gain}（约 {cost} 钻），直充不进邮",
            amount=gain,
            meta={"tubes": tubes, "pyroxene": cost},
        )

    def free_buy(self, amount: int, clear_mode: str, *, allow_clear: bool = False) -> None:
        """每日礼包体力：与任务/JJC 相同，满栏溢出进邮（用户实机确认可进邮）。"""
        amount = int(amount)
        if amount <= 0:
            return
        # 统一走可囤领取：不满进栏，满则进邮；禁止为 +10 清体
        self.claim_hoardable(
            ACTION_FREE_BUY,
            amount,
            f"每日礼包 +{amount}（可进邮）",
            meta={"free_buy": True},
        )

    def claim_hoardable(
        self,
        action: str,
        amount: int,
        note: str,
        force_overflow: bool = False,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        amount = int(amount)
        if amount <= 0:
            return
        room = self.hard_cap - self.ap
        into = min(room, amount)
        overflow = amount - into
        self.ap += into
        if overflow > 0:
            self._push_mail(overflow, self.t)
        base_meta: Dict[str, Any] = {"overflow": overflow, "into_char": into}
        if meta:
            base_meta.update(meta)
        self._emit(
            action,
            "auto",
            note=note
            + (
                f" → 体+{into}"
                + (f" 邮+{overflow}" if overflow else "")
            ),
            amount=amount,
            deadline=self.mail[-1].handle_by if overflow and self.mail else None,
            meta=base_meta,
        )

    def claim_cafe(self, amount: Optional[int] = None, note: str = "") -> None:
        self._tick_cafe(self.t)
        if amount is None:
            amount = int(round(self.cafe_stock))
        amount = max(0, int(amount))
        if amount <= 0:
            return
        self.claim_hoardable(
            ACTION_CLAIM_CAFE,
            amount,
            note or f"咖啡厅领取≈{amount}",
        )
        # 领完库存清零
        self.cafe_stock = max(0.0, self.cafe_stock - amount)
        if amount >= int(self.cafe_stock) or amount >= int(self.cafe_cap * 0.9):
            self.cafe_stock = 0.0
        self._cafe_last_t = self.t

    def use_ap_card(self, amount: int) -> None:
        self.claim_hoardable(
            ACTION_USE_AP_CARD,
            amount,
            note=f"使用体力卡 +{amount}（可进邮）",
        )

    def clear_to(
        self,
        target: int,
        clear_mode: str,
        note: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        target = max(0, int(target))
        if self.ap <= target:
            return
        drop = self.ap - target
        mode = "manual" if clear_mode == CLEAR_MODE_NOTIFY_ONLY else "auto"
        self.ap = target
        base_meta: Dict[str, Any] = {"target_ap": target, "clear_mode": clear_mode, "drop": drop}
        if meta:
            base_meta.update(meta)
        detail = ""
        recipe = (meta or {}).get("clear_recipe") if meta else None
        if isinstance(recipe, list) and recipe:
            detail = "；步骤：" + " → ".join(str(x) for x in recipe)
        self._emit(
            ACTION_CLEAR_AP if mode == "auto" else ACTION_NOTIFY,
            mode,
            note=(note or f"清体到 {target}") + detail,
            amount=drop,
            meta=base_meta,
        )

    def hold_until(self, when: datetime, note: str = "保持满栏，抑制危险日常") -> None:
        self.advance_to(when)
        self._emit(ACTION_HOLD, "auto", note=note, amount=0)


    def claim_from_mail(self, amount: Optional[int] = None, note: str = "") -> int:
        """从邮箱领体力进角色栏（不能超过 hard_cap）。返回实际领到的量。"""
        if not self.mail:
            return 0
        room = self.hard_cap - self.ap
        if room <= 0:
            return 0
        want = room if amount is None else max(0, min(int(amount), room))
        if want <= 0:
            return 0
        taken = 0
        # 先领最早过期的
        self.mail.sort(key=lambda p: p.expire_at)
        new_mail = []
        for parcel in self.mail:
            if taken >= want:
                new_mail.append(parcel)
                continue
            need = want - taken
            if parcel.amount <= need:
                taken += parcel.amount
            else:
                taken += need
                new_mail.append(
                    MailParcel(
                        amount=parcel.amount - need,
                        overflow_at=parcel.overflow_at,
                        expire_at_override=getattr(parcel, "expire_at_override", None),
                        source=getattr(parcel, "source", "") or "",
                        role=getattr(parcel, "role", "") or "",
                    )
                )
        self.mail = new_mail
        self.ap += taken
        if taken > 0:
            self._emit(
                ACTION_CLAIM_MAIL,
                "auto",
                note=note or f"从邮箱领取 +{taken} 垫体力栏",
                amount=taken,
                meta={"from_mail": taken},
            )
        return taken

    def drain_expiring_mail(
        self,
        clear_mode: str,
        before: datetime,
        note_prefix: str = "",
    ) -> None:
        """在 before 前：把角色扫到 0 → 领邮垫满 →（可选）再扫再领，避免邮体过期浪费。

        这是囤体中「过期邮」的正确处理：不是让用户干瞪眼，而是自动花掉角色栏再领邮。
        """
        expiring = [p for p in self.mail if p.handle_by <= before or p.expire_at <= before]
        if not expiring:
            return
        total_exp = sum(p.amount for p in expiring)
        # 时刻：最早 handle_by 与 now 之间
        when = min(p.handle_by for p in expiring)
        if when < self.t:
            when = self.t
        self.advance_to(when)

        # 循环：扫光 → 领邮，直到没有即将过期邮或角色已满且邮仍在
        for _ in range(6):
            expiring = [p for p in self.mail if p.expire_at <= before + timedelta(hours=1)]
            if not expiring:
                break
            # 1) 角色有体就清到 0，腾空位领邮
            if self.ap > 0:
                drop = self.ap
                self.clear_to(
                    0,
                    clear_mode,
                    note=(note_prefix or "")
                    + f"扫光体力栏（约 {drop}）以便领取即将过期邮箱体力",
                )
            # 2) 从邮箱领到满
            got = self.claim_from_mail(
                note=(note_prefix or "")
                + f"领取即将过期邮箱体力，垫满体力（邮箱仍约 {self.mail_total}）"
            )
            if got <= 0:
                break
            # 3) 若仍有过期邮且角色已满，再扫一轮继续领
            still = sum(p.amount for p in self.mail if p.expire_at <= before + timedelta(hours=1))
            if still <= 0:
                break
            if self.ap >= self.hard_cap:
                # 满了但邮还多：再扫光继续领
                continue
            break

    def fill_to_hard_cap(
        self,
        cfg: "HoardConfig",
        clear_mode: str,
    ) -> None:
        """花体前用「快过期邮垫档」算法尽量到 990–999；不够再买管。"""
        if self.ap >= self.hard_cap:
            return
        # 把当前 mail 转成 MailBag
        bags = [
            MailBag(
                amount=p.amount,
                overflow_at=p.overflow_at,
                expire_at=p.expire_at,
                source="",
            )
            for p in self.mail
        ]
        pad = build_pad_plan(
            current_ap=self.ap,
            bags=bags,
            now=self.t,
            hard_cap=self.hard_cap,
            success_lo=max(0, self.hard_cap - 9),
        )
        # 执行 pad 步骤到仿真
        for st in pad.steps:
            if st.action == "clear" and st.clear_amount > 0:
                target = max(0, self.ap - st.clear_amount)
                self.clear_to(target, clear_mode, note=st.note or "为领邮清出空位")
            elif st.action == "claim_mail" and st.claim_amount > 0:
                self.claim_from_mail(amount=st.claim_amount, note=st.note or "领快过期邮垫档")
            elif st.action == "manual_hint":
                self._emit(ACTION_NOTIFY, "auto", note=st.note)
        # 仍不足：买管（整管，且不超 hard_cap）
        if self.ap < self.hard_cap and cfg.tubes > 0:
            need = self.hard_cap - self.ap
            if need >= TUBE_AP:
                n = min(cfg.tubes, need // TUBE_AP)
                if n > 0:
                    self.buy_tubes(n, clear_mode)
        # 存手顺到最后一步 meta（narrative 可读 summary）
        if pad.manual_script:
            self._emit(
                ACTION_NOTIFY,
                "auto",
                note="邮箱垫满手顺已生成（OCR 失败时按说明逐步领）",
                meta={"mail_pad_script": pad.manual_script, "pad": pad.to_dict()},
            )


    def spend_ready(self, note: str = "到点花体：请上线花体 / 处理邮箱近过期体力") -> None:
        earliest_expire = min((p.expire_at for p in self.mail), default=None)
        self._emit(
            ACTION_SPEND_READY,
            "manual",
            note=note,
            amount=self.mail_total,
            deadline=earliest_expire,
            meta={"mail_total": self.mail_total, "ap": self.ap},
        )


def _resolve_spend_at(cfg: HoardConfig, now: datetime) -> datetime:
    """解析用户填的消费日+花体时刻。

    显式日期不再把已过点的花体自动顺延到次日——过期由 executor.arm_plan
    硬拦（置 PHASE_ABORTED），不再仅靠 UI 拦截。
    未填日期时，默认取「明天」的花体时刻。
    """
    if not cfg.target_date:
        day = server_day_start(now) + timedelta(days=1)
    else:
        y, m, d = [int(x) for x in cfg.target_date.split("-")]
        day = datetime(y, m, d, SERVER_DAY_RESET_HOUR, 0, 0)
    return combine_server_date_and_time(day, cfg.spend_time)


def _stack_day(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    buy_tubes: bool,
    use_card: bool,
    force_fill_soft: bool = True,
    cafe_amount: Optional[int] = None,
    skip_claimed_today: bool = False,
    skip_cafe: bool = False,
    claim_cafe_first: bool = False,
    free_buy_allow_clear: bool = False,
    label: str = "",
) -> None:
    """在 sim.t 执行一轮「可囤日」堆叠。

    勤奋顺序（用户口径）：
    1) 若需要买体：先保证角色栏空位，再买体（直充不进邮）
    2) 可先领咖啡重置计时（满则进邮）
    3) 日替后：礼包/小组/任务/竞技场店（满则进邮）
    4) 体力卡（可进邮）
    """
    jjc = 0 if (skip_claimed_today and cfg.jjc_claimed) else sim_jjc_amount(int(sim.mail_total), cfg)
    task = 0 if (skip_claimed_today and cfg.task_claimed) else cfg.resolved_task_ap()
    group = 0 if (skip_claimed_today and cfg.group_claimed) else int(cfg.group_ap)
    free_b = 0 if (skip_claimed_today and cfg.free_buy_claimed) else int(cfg.free_buy_ap)

    if force_fill_soft and sim.ap < cfg.natural_soft_cap:
        need = cfg.natural_soft_cap - sim.ap
        hours = need / max(cfg.natural_ap_per_hour, 0.1)
        sim.advance_to(sim.t + timedelta(hours=hours))

    # 直充：买体力
    if buy_tubes and cfg.tubes > 0:
        gain = tube_gain_ap(cfg.tubes)
        if sim.ap + gain > sim.hard_cap:
            # 勤奋：尽量只清到 hard-gain，让之后自回吃满到买点
            target = max(0, sim.hard_cap - gain)
            if sim.ap > target:
                hours_left_note = ""
                sim.clear_to(
                    target,
                    cfg.clear_mode,
                    note=note_keep_regen(sim, target, f"买体前清到 {target}（空位 {gain}）"),
                )
        sim.buy_tubes(cfg.tubes, cfg.clear_mode)

    # 咖啡：可选提前领（重置计时）
    if claim_cafe_first and not skip_cafe:
        sim.claim_cafe(amount=cafe_amount, note="领取咖啡厅奖励（重置计时）")

    # 为礼包+10 腾一点点空位（979~989）
    if free_b > 0 and free_buy_allow_clear and sim.ap + free_b > sim.hard_cap:
        # 只空出 free_b，不整段大清
        target = max(0, sim.hard_cap - free_b)
        if sim.ap > target:
            sim.clear_to(
                target,
                cfg.clear_mode,
                note=f"空出 {free_b} 位给礼包体（清到 {target}）",
            )

    # 执行优先级（用户修订 2026-08-27，取代「领任务体优先」）：
    # 领到期邮在外层 drain 流程；买管已在前 → 本批 =
    # JJC店(最繁琐,优先) → 礼包 → 小组 → 咖啡 → 任务体(最后)
    if jjc > 0:
        sim.claim_hoardable(
            ACTION_CLAIM_JJC,
            jjc,
            f"竞技场商店 +{jjc}（{cfg.jjc_buy_mode}，刷新{cfg.jjc_refresh}次）",
        )
    if free_b > 0:
        sim.free_buy(free_b, cfg.clear_mode, allow_clear=bool(free_buy_allow_clear))

    if group > 0:
        sim.claim_hoardable(ACTION_CLAIM_GROUP, group, "小组体力 +10")
    if (not skip_cafe) and (not claim_cafe_first):
        sim.claim_cafe(amount=cafe_amount)
    if task > 0:
        lesson_note = (
            f"任务体力 +{task}（登录{TASK_LOGIN_AP}"
            + (f"+日程{TASK_LESSON_AP}" if cfg.lesson_include() else "，未计日程50")
            + "）"
        )
        sim.claim_hoardable(ACTION_CLAIM_TASK, task, lesson_note)

    if use_card and cfg.use_ap_card and cfg.ap_card_amount > 0:
        sim.use_ap_card(cfg.ap_card_amount)

    if sim.ap < cfg.natural_soft_cap:
        need = cfg.natural_soft_cap - sim.ap
        hours = need / max(cfg.natural_ap_per_hour, 0.1)
        back = sim.t + timedelta(hours=hours)
        sim._emit(
            ACTION_WAIT,
            "auto",
            note=f"等待自然回复到软顶≈{cfg.natural_soft_cap}（约 {hours:.1f}h）",
            amount=need,
            deadline=back,
        )
        sim.advance_to(back)


def note_keep_regen(sim: _Sim, target: int, base: str) -> str:
    """附带「不浪费自回」说明。"""
    drop = max(0, sim.ap - target)
    # 粗算：从 target 回满 soft 需要的小时；以及从现在到软顶可吃的自回
    soft = int(sim.natural_soft_cap)
    per_h = max(0.1, float(sim.natural_per_hour))
    if target < soft:
        can_regen = soft - target
        hours = can_regen / per_h
        return f"{base}；不浪费自回（约可再自回 {can_regen}≈{hours:.0f}h）"
    if drop > 0:
        return f"{base}；本次花掉约 {drop}"
    return base


def _strategy_lead_days(strategy: str, tube_days: int = 1) -> int:
    """主堆叠相对花体日向前看几天（不含花体当天）。"""
    if strategy == STRATEGY_SIMPLE:
        return 1
    if strategy == STRATEGY_XIUXIAN:
        # 买体天数：1→至少看前1~2日；2→前2日；3→前3日
        return max(2, min(3, int(tube_days or 1) + 1))
    return 2  # simple_plus


def _pre_reset_moment(day_start: datetime, minutes_before: int = 10) -> datetime:
    """某游戏日 04:00 前 N 分钟。"""
    return day_start - timedelta(minutes=max(1, int(minutes_before)))


def _min_keep_ap(cfg: HoardConfig) -> int:
    """至少留 1/24 软顶（约 1 小时自回），禁止无脑清到 0。"""
    soft = max(1, int(cfg.natural_soft_cap or AP_SOFT_NATURAL_CAP))
    return max(1, int(round(soft / 24.0)))


# 清体单次耗体（估算，用于计划拆解）
AP_COST_ACTIVITY = 20
AP_COST_SCRIMMAGE = 15
AP_COST_SPECIAL = 20
AP_COST_MAINLINE_NORMAL = 10
AP_COST_MAINLINE_HARD = 15


def _parse_int_list(raw: Any, n: int = 0) -> List[int]:
    s = str(raw or "").strip().replace("，", ",")
    if not s:
        return [0] * n if n else []
    parts = [p.strip() for p in s.split(",")]
    out: List[int] = []
    for p in parts:
        if p == "" or p.lower() == "max":
            out.append(-1 if p.lower() == "max" else 0)
            continue
        try:
            out.append(int(float(p)))
        except Exception:
            out.append(0)
    if n > 0:
        while len(out) < n:
            out.append(0)
        out = out[:n]
    return out


def _parse_mainline_entries(priority: str) -> List[Tuple[str, int]]:
    """解析主线优先级。

    支持：
    - BAAS 经典：`16-5-max` / `16-3-3`（章-关-次数）
    - 多关空格：`5-1-0 1-1-0`（次数 0=不扫）
    - 逗号：`5-1-3,1-1-2`
    返回 [(label, times), ...]，times=0 不扫，-1=max。
    """
    s = str(priority or "").strip()
    if not s:
        return []
    s = s.replace("；", " ").replace("，", ",").replace("—", "-")
    raw_parts: List[str] = []
    for tok in s.split():
        raw_parts.extend([p.strip() for p in tok.split(",") if p.strip()])
    out: List[Tuple[str, int]] = []
    for part in raw_parts:
        segs = [x.strip() for x in part.split("-") if x.strip() != ""]
        if len(segs) < 2:
            continue
        if len(segs) >= 3:
            label = f"{segs[0]}-{segs[1]}"
            times_s = segs[2]
        else:
            label = segs[0]
            times_s = segs[1]
        if times_s.lower() in ("max", "m"):
            times = -1
        else:
            try:
                times = int(float(times_s))
            except Exception:
                times = 0
        out.append((label, times))
    return out


def _mainline_cost_estimate(priority: str, hard: bool = False) -> int:
    """主线优先级串 → 估算耗体（次数 0 不计，max 按 30 次上限展示）。"""
    unit = AP_COST_MAINLINE_HARD if hard else AP_COST_MAINLINE_NORMAL
    total = 0
    for _label, times in _parse_mainline_entries(priority):
        if times == 0:
            continue
        if times < 0:
            total += 30 * unit
        else:
            total += max(0, times) * unit
    return total


def _mainline_recipe_lines(priority: str, hard: bool, left: int) -> Tuple[List[str], int]:
    """把主线配置拆成可读步骤并扣 left。次数 0 的关卡跳过。"""
    unit = AP_COST_MAINLINE_HARD if hard else AP_COST_MAINLINE_NORMAL
    kind = "困难" if hard else "普通"
    steps: List[str] = []
    for label, times in _parse_mainline_entries(priority):
        if left <= 0:
            break
        if times == 0:
            continue
        if times < 0:
            n = max(1, left // unit) if left >= unit else (1 if left > 0 else 0)
        else:
            n = min(times, left // unit) if left >= unit else 0
            if n <= 0 and times > 0 and left > 0:
                n = 1
            if times > 0:
                n = min(times, n)
        if n <= 0:
            continue
        cost = min(left, n * unit)
        steps.append(f"主线{kind}{label} {unit}×{n}(−{cost})")
        left -= cost
    return steps, left



def build_clear_recipe(cfg: HoardConfig, drop: int) -> List[str]:
    """按用户填写的清体去向，把 drop 拆成「交流会15×n / 活动20×m …」。

    规则（用户校正）：
    - 表单次数 = 当天清体时「各入口允许打多少次」的预算，不是无限池。
    - 正数：该入口最多用这么多次；三所交流会合计也不能超过用户填的次数之和
      （每天交流会总共只有 6 次，表单 2,2,2 即各 2，合计 6，禁止再写「继续scrimmage」超打）。
    - 0：该入口不打。
    - -1/max：该入口可作补量（在预算类用完后，用 -1 入口把剩余体耗到接近 0）。
    - 禁止在预算用尽后再用「继续xxx」虚增次数；只允许 -1 入口或已声明的 max 入口补。
    顺序：交流会 → 特殊委托 → 活动 → 主线困难 → 主线普通 →（仅 -1）补量。
    """
    drop = max(0, int(drop))
    if drop <= 0:
        return []
    modes = [m.strip() for m in str(getattr(cfg, "clear_modes", "") or "").split(",") if m.strip()]
    if not modes:
        modes = [str(getattr(cfg, "clear_mode", "") or CLEAR_MODE_ACTIVITY)]

    left = drop
    steps: List[str] = []
    # 记录 -1 补量入口，预算阶段用完后再动
    flex: List[Tuple[str, int, str]] = []  # (label_prefix, unit, mode_key)

    def _take(label: str, unit: int, max_n: int) -> None:
        nonlocal left
        if left <= 0 or unit <= 0 or max_n == 0:
            return
        if max_n < 0:
            # flex later
            return
        whole = left // unit
        if whole <= 0:
            return
        n = min(int(max_n), whole)
        if n <= 0:
            return
        cost = n * unit
        steps.append(f"{label}{unit}×{n}(−{cost})")
        left -= cost

    # 交流会：scrimmage_times = a,b,c —— 各校次数上限；合计通常 ≤6
    counts_s = _parse_int_list(getattr(cfg, "scrimmage_times", "0,0,0"), 3)
    names_s = ("三一", "格黑娜", "千年")
    if "scrimmage" in modes or any(x != 0 for x in counts_s):
        for i, c in enumerate(counts_s):
            if c < 0:
                flex.append((f"交流会{names_s[i]}", AP_COST_SCRIMMAGE, "scrimmage"))
            elif c > 0:
                _take(f"交流会{names_s[i]}", AP_COST_SCRIMMAGE, c)

    # 特殊委托
    counts_sp = _parse_int_list(getattr(cfg, "special_task_times", "0,0"), 2)
    names_sp = ("据点防御", "物品回收")
    if "special" in modes or any(x != 0 for x in counts_sp):
        for i, c in enumerate(counts_sp):
            if c < 0:
                flex.append((f"特殊委托{names_sp[i]}", AP_COST_SPECIAL, "special"))
            elif c > 0:
                _take(f"特殊委托{names_sp[i]}", AP_COST_SPECIAL, c)

    # 活动
    act_times_raw = str(getattr(cfg, "activity_sweep_times", "0") or "0").strip()
    act_stage = str(getattr(cfg, "activity_sweep_task_number", "1") or "1").strip()
    if "activity" in modes or act_times_raw not in ("", "0"):
        unit = AP_COST_ACTIVITY
        label = f"活动{act_stage}图"
        if act_times_raw.lower() in ("max", "-1") or (
            act_times_raw.lstrip("-").isdigit() and int(float(act_times_raw)) < 0
        ):
            flex.append((label, unit, "activity"))
        else:
            try:
                cfg_n = int(float(act_times_raw))
            except Exception:
                cfg_n = 0
            if cfg_n > 0:
                _take(label, unit, cfg_n)
            elif cfg_n == 0 and "activity" in modes and act_times_raw in ("", "0"):
                # 勾了活动但次数 0：不扫
                pass

    # 主线（次数 0 不扫）
    if "mainline" in modes or str(getattr(cfg, "mainline_priority", "") or "").strip() or str(
        getattr(cfg, "hard_priority", "") or ""
    ).strip():
        hard_p = str(getattr(cfg, "hard_priority", "") or "")
        norm_p = str(getattr(cfg, "mainline_priority", "") or "")
        if left > 0 and hard_p.strip():
            lines, left = _mainline_recipe_lines(hard_p, True, left)
            steps.extend(lines)
        if left > 0 and norm_p.strip():
            lines, left = _mainline_recipe_lines(norm_p, False, left)
            steps.extend(lines)

    # 仅 -1/max 入口可补剩余体；禁止「继续scrimmage」虚增每日 6 次上限
    if left > 0 and flex:
        for label, unit, _mk in flex:
            if left <= 0:
                break
            whole = left // unit
            if whole <= 0:
                continue
            cost = whole * unit
            steps.append(f"{label}{unit}×{whole}(−{cost})（-1补量）")
            left -= cost

    # 正数预算与 flex(-1) 用完后：禁止凭空塞主线/虚增活动次数
    if left > 0:
        if left <= 20:
            steps.append(f"余{left}体：不足一次扫荡，可忽略（执行按≤20算完成）")
        else:
            hint = "请把活动次数改成 -1/max，或加大表单次数"
            if "mainline" in modes and (
                str(getattr(cfg, "mainline_priority", "") or "").strip()
                or str(getattr(cfg, "hard_priority", "") or "").strip()
            ):
                hint = "请加大活动/主线次数，或把活动改成 -1"
            steps.append(f"余{left}体：表单预算已用尽（{hint}）")

    return steps


def _attach_clear_recipe(cfg: HoardConfig, drop: int) -> Dict[str, Any]:
    recipe = build_clear_recipe(cfg, drop)
    return {"clear_recipe": recipe, "clear_drop": int(drop)}


def mail_parcels_from_bags(
    bags: Sequence[Dict[str, Any]],
    now: datetime,
) -> List[MailParcel]:
    """表单/OCR 邮箱明细 → MailParcel（尊重 remain_hours）。"""
    out: List[MailParcel] = []
    now = now.replace(second=0, microsecond=0)
    for b in bags or []:
        if not isinstance(b, dict):
            continue
        try:
            amt = int(b.get("amount") or 0)
        except Exception:
            continue
        if amt <= 0:
            continue
        rh = b.get("remain_hours")
        if rh is None:
            rh = b.get("remaining_hours")
        if rh is None and b.get("remaining_minutes") is not None:
            try:
                rh = float(b.get("remaining_minutes")) / 60.0
            except Exception:
                rh = None
        try:
            rh_f = float(rh) if rh is not None else 23.0
        except Exception:
            rh_f = 23.0
        rh_f = max(0.0, rh_f)
        exp = now + timedelta(hours=rh_f)
        ov = exp - timedelta(seconds=MAIL_TTL_SECONDS)
        role = str(b.get("role") or "")
        # 识别进表的限时体默认视为主堆囤货：禁止被 0.2h 临期规则提前领光
        # 仅当明确 role=rescue/urgent 或剩余已 <2h 才允许临期救
        if not role:
            if rh_f >= 2.0:
                role = "stack_for_claim"
            elif amt >= 200 and rh_f >= 1.0:
                role = "stack_for_claim"
        out.append(
            MailParcel(
                amount=amt,
                overflow_at=ov,
                expire_at_override=exp,
                source=str(b.get("source") or "bag"),
                role=role,
            )
        )
    return out


def _clear_to_arrive_soft(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    next_anchor: datetime,
    note_prefix: str = "清体",
) -> None:
    """清到「到 next_anchor 时刚好吃满软顶」的起点，并至少保留 1/24 软顶。

    例：软顶 160、距节点 21h、每小时 10 → 可自回 160（封顶 soft）→ 目标 max(min_keep, soft-160)=min_keep。
    距节点 10h → 可自回 100 → 目标 max(min_keep, 160-100)=60。到点约为软顶满，不是 0。
    """
    soft = int(cfg.natural_soft_cap)
    per_h = max(0.1, float(cfg.natural_ap_per_hour))
    hours = max(0.0, (next_anchor - sim.t).total_seconds() / 3600.0)
    regen = int(hours * per_h)
    min_keep = _min_keep_ap(cfg)
    # 希望 next 时 ap≈soft：现在应 = soft - regen（下限 min_keep）
    target = max(min_keep, soft - regen)
    target = min(target, soft)  # 不超过软顶
    if sim.ap > target:
        drop = sim.ap - target
        sim.clear_to(
            target,
            cfg.clear_mode,
            note=note_keep_regen(
                sim,
                target,
                f"{note_prefix}到 {target}（距节点≈{hours:.0f}h 可自回{min(regen, soft)}，到点≈软顶{soft}；至少留{min_keep}）",
            ),
            meta=_attach_clear_recipe(cfg, drop),
        )


def _diligent_clear_for_buy(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    tubes: int,
    next_anchor: datetime,
) -> None:
    """买体前清栏：既要买得下，又要尽量吃满到锚点的自回；绝不无脑清 0。"""
    tubes = max(0, int(tubes))
    if tubes <= 0:
        return
    gain = tube_gain_ap(tubes)
    hard = int(sim.hard_cap)
    soft = int(cfg.natural_soft_cap)
    per_h = max(0.1, float(cfg.natural_ap_per_hour))
    hours = max(0.0, (next_anchor - sim.t).total_seconds() / 3600.0)
    regen = int(hours * per_h)
    min_keep = _min_keep_ap(cfg)
    max_before_buy = hard - gain

    if sim.ap + gain <= hard:
        # 已放得下：若远超 soft 且距锚点很长，可压到「到点满 soft」以少浪费
        if sim.ap > soft and hours >= 1.0:
            want = max(min_keep, soft - regen)
            want = min(want, soft)
            if want < sim.ap and want + gain <= hard:
                drop = sim.ap - want
                sim.clear_to(
                    want,
                    cfg.clear_mode,
                    note=note_keep_regen(
                        sim,
                        want,
                        f"买体前压到 {want}（到点≈软顶；仍放得下+{gain}）",
                    ),
                    meta=_attach_clear_recipe(cfg, drop),
                )
        return

    # 放不下：至少 max_before_buy；并尽量贴 soft-regen
    want = max(min_keep, soft - regen)
    target = min(max_before_buy, want)
    target = max(min_keep, int(target))
    target = min(target, max_before_buy)
    if sim.ap > target:
        drop = sim.ap - target
        sim.clear_to(
            target,
            cfg.clear_mode,
            note=note_keep_regen(
                sim,
                target,
                f"买体前清到 {target}（空位{gain}；距节点≈{hours:.0f}h 可自回≈{min(regen, soft)}）",
            ),
            meta=_attach_clear_recipe(cfg, drop),
        )


def _claim_daily_sources(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    skip_claimed_today: bool,
    include_free: bool = True,
    include_cafe: bool = False,
) -> None:
    """领取日替源。skip_claimed_today=True 时跳过表单勾了已领的项。

    规则：礼包/登陆/日程/小组/JJC 全部可进邮；满栏直接进邮，禁止为它们清体。
    """
    jjc = 0 if (skip_claimed_today and cfg.jjc_claimed) else sim_jjc_amount(int(sim.mail_total), cfg)
    login = 0 if (skip_claimed_today and cfg.task_claimed) else int(TASK_LOGIN_AP)
    if skip_claimed_today:
        lesson = 0 if (bool(getattr(cfg, "lesson_claimed", False)) or not cfg.lesson_include()) else int(TASK_LESSON_AP)
    else:
        lesson = int(TASK_LESSON_AP) if cfg.lesson_include() else 0
    group = 0 if (skip_claimed_today and cfg.group_claimed) else int(cfg.group_ap)
    free_b = 0 if (skip_claimed_today and cfg.free_buy_claimed) else int(cfg.free_buy_ap)

    # 全部可进邮：礼包/小组/任务/JJC 满栏直接进邮，禁止为它们清体
    if include_free and free_b > 0:
        sim.free_buy(free_b, cfg.clear_mode, allow_clear=False)

    if group > 0:
        sim.claim_hoardable(ACTION_CLAIM_GROUP, group, "小组体力 +10（可进邮）")
    if login > 0:
        sim.claim_hoardable(
            ACTION_CLAIM_TASK,
            login,
            f"任务体力 +{login}（登录{TASK_LOGIN_AP}，可进邮）",
            meta={"task_part": "login"},
        )
    if lesson > 0:
        sim.claim_hoardable(
            ACTION_CLAIM_TASK,
            lesson,
            f"日程体力 +{lesson}（完成日程后领取，可进邮；执行成功勾已领）",
            meta={"task_part": "lesson", "mark_lesson_claimed": True},
        )
    if jjc > 0:
        sim.claim_hoardable(
            ACTION_CLAIM_JJC,
            jjc,
            f"竞技场商店 +{jjc}（{cfg.jjc_buy_mode}，刷新{cfg.jjc_refresh}次，可进邮）",
        )
    if include_cafe:
        sim.claim_cafe(note="领取咖啡厅奖励（可进邮）")


def _mail_pad_loop(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    until: datetime,
    prefer_small_first: bool = True,
    max_rounds: int = 6,
    drain_all: bool = False,
    rotate_to_refresh_mail: bool = False,
    max_rotate: int = 2,
) -> None:
    """邮箱垫角色：小额优先一次垫满空位；rotate 轮数由 max_rotate 控制。"""
    if until > sim.t:
        sim.advance_to(until)

    def _fill_room() -> int:
        room = sim.hard_cap - sim.ap
        if room <= 0 or not sim.mail:
            return 0
        sim.mail.sort(
            key=lambda p: (
                (p.amount if prefer_small_first else -p.amount),
                p.expire_at,
            )
        )
        return sim.claim_from_mail(
            amount=room,
            note=f"领取邮箱垫体 +{room}（小额优先，一次垫满空位）",
        )

    rotates = 0
    if not rotate_to_refresh_mail:
        max_rotate = 0
    else:
        max_rotate = max(0, int(max_rotate))
    for _ in range(max_rounds):
        if not sim.mail:
            break
        room = sim.hard_cap - sim.ap
        if room > 0:
            got = _fill_room()
            if got <= 0:
                break
            if sim.ap >= sim.hard_cap - 1:
                if rotates >= max_rotate or not sim.mail:
                    break
                bags = sorted(sim.mail, key=lambda p: (p.amount, p.expire_at))
                need_room = min(30, max(10, bags[0].amount if bags else 20))
                target = max(_min_keep_ap(cfg), sim.hard_cap - need_room)
                if sim.ap > target:
                    sim.clear_to(
                        target,
                        cfg.clear_mode,
                        note=f"花一点到 {target}，再领邮刷新倒计时（空{need_room}）",
                    )
                rotates += 1
                continue
            continue
        if rotates >= max_rotate or not (drain_all or rotate_to_refresh_mail) or not sim.mail:
            break
        bags = sorted(sim.mail, key=lambda p: (p.amount, p.expire_at))
        need_room = min(30, max(10, bags[0].amount if bags else 20))
        target = max(_min_keep_ap(cfg), sim.hard_cap - need_room)
        if sim.ap > target:
            sim.clear_to(
                target,
                cfg.clear_mode,
                note=f"花一点到 {target}，再领邮刷新倒计时（空{need_room}）",
            )
        rotates += 1


def _mail_reserve_window(spend_at: datetime) -> datetime:
    """邮箱储备窗 = 花体时刻的「前一天同一钟点 + 10 分钟」。

    例：花体 08-13 18:30 → 窗 08-12 18:40
        花体 08-13 04:10 → 窗 08-12 04:20
    此时满栏溢出进邮，到花体时邮约剩 24h-24h+10min ≈ 10 分钟到期窗口。
    """
    return (spend_at - timedelta(days=1)) + timedelta(minutes=10)


def _after_overflow_sources(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    next_anchor: datetime,
    do_pad: bool = True,
    keep_mail: bool = True,
) -> None:
    """领完可溢出源后的处理。

    - 有邮箱且 keep_mail：只做「垫满体力 + 最多 2 轮小刷新」，然后 **保持近满栏**，
      邮箱剩余留给花体。禁止再压到软顶（会把邮又领光）。
    - 无邮箱：才按到下一节点压到「到点满软顶」。
    """
    if do_pad and sim.mail_total > 0:
        # 有邮时：只垫满体力 1 次；邮件多则不再 rotate（避免刷光）
        if sim.ap < sim.hard_cap:
            room = sim.hard_cap - sim.ap
            sim.mail.sort(key=lambda p: (p.amount, p.expire_at))
            sim.claim_from_mail(
                amount=room,
                note=f"领源后垫满 +{room}（剩余邮保留）",
            )
        elif sim.mail_total < 100:
            # 邮很少时允许 1 轮刷新倒计时
            _mail_pad_loop(
                sim,
                cfg,
                until=sim.t,
                prefer_small_first=True,
                rotate_to_refresh_mail=True,
                max_rounds=2,
            )
    if keep_mail and sim.mail_total > 0:
        # 角色尽量满着挂机；邮箱倒计时在跑
        return
    if next_anchor > sim.t + timedelta(minutes=30):
        _clear_to_arrive_soft(
            sim, cfg, next_anchor=next_anchor, note_prefix="领源后压体"
        )


def _today_unclaimed_gain(cfg: HoardConfig) -> int:
    """今日尚未勾选「已领」的可囤/直充合计（登陆/日程分开）。"""
    g = 0
    g += int(cfg.resolved_login_ap() or 0)
    g += int(cfg.resolved_lesson_ap() or 0)
    if not cfg.jjc_claimed:
        g += int(cfg.resolved_jjc_ap() or 0)
    if not cfg.group_claimed:
        g += int(cfg.group_ap or 0)
    if not cfg.free_buy_claimed:
        g += int(cfg.free_buy_ap or 0)
    return max(0, g)


def _diligent_worth_clearing_high_ap(cfg: HoardConfig, sim: _Sim) -> bool:
    """高体力时是否还值得为勤奋先清一刀（今日源大多未领）。"""
    soft = int(cfg.natural_soft_cap or AP_SOFT_NATURAL_CAP)
    if sim.ap <= soft + 40:
        return True
    gain = _today_unclaimed_gain(cfg)
    threshold = max(360, int(cfg.resolved_jjc_ap() or 0) + int(cfg.resolved_task_ap() or 0))
    if gain < threshold:
        return False
    if cfg.task_claimed and cfg.jjc_claimed:
        return False
    return True


def _pre_reset_buy_moment(spend_at: datetime) -> datetime:
    """花体前 20 分钟（04:10 → 03:50；18:30 → 18:10）。

    贴 04:00 刷新时，关键买体/垫邮必须在刷新前做完。
    """
    return spend_at - timedelta(minutes=20)


def _stack_day_0350(spend_at: datetime, days_before: int) -> datetime:
    """花体墙上日期往前第 N 天的 03:50。

    days_before=1, 花体 08-13 04:10 → 08-12 03:50
    days_before=1, 花体 08-13 18:30 → 08-12 03:50
    （按日历日回退，避免「游戏日 04:00」把主买算到花体当天 03:50）
    """
    d = (spend_at - timedelta(days=int(days_before))).date()
    return datetime(d.year, d.month, d.day, 3, 50, 0)


def _make_room_for_direct(sim: _Sim, cfg: HoardConfig, amount: int, note: str) -> None:
    """仅为直充（礼包等）空出 amount，不清光。已有空位则不做事。"""
    amount = max(0, int(amount))
    if amount <= 0:
        return
    if sim.ap + amount <= sim.hard_cap:
        return
    target = max(_min_keep_ap(cfg), sim.hard_cap - amount)
    if sim.ap > target:
        drop = sim.ap - target
        sim.clear_to(
            target,
            cfg.clear_mode,
            note=note,
            meta=_attach_clear_recipe(cfg, drop),
        )


def _claim_cafe_overflow(sim: _Sim, cfg: HoardConfig, note: str) -> None:
    """领咖啡：满栏溢出进邮。已满则直接进邮；未满先填栏。"""
    sim.claim_cafe(note=note)


def _pad_mail_small_first(sim: _Sim, cfg: HoardConfig, *, rotate_rounds: int = 2) -> None:
    """小额邮优先垫满；可轮转少量刷新 TTL，不把邮刷光。"""
    if sim.mail_total <= 0:
        return
    _mail_pad_loop(
        sim,
        cfg,
        until=sim.t,
        prefer_small_first=True,
        rotate_to_refresh_mail=(rotate_rounds > 0),
        max_rounds=max(2, int(rotate_rounds) + 1),
        max_rotate=max(0, int(rotate_rounds)),
        drain_all=False,
    )


def _claim_urgent_mail_bags(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    remain_h_limit: float = 1.0,
    note_prefix: str = "临期邮",
) -> int:
    """只处理「剩余 ≤ remain_h_limit」的邮包：腾出刚好空位 → 领这些包。

    不把未临期的大包领光。角色清到 0 仅当临期总量 ≥ 当前体或需要整包空位。
    返回领到的量。
    """
    if not sim.mail:
        return 0
    def _is_rescue(p: MailParcel) -> bool:
        if (getattr(p, "role", "") or "") == "stack_for_claim":
            return False
        return p.remain_hours(sim.t) <= remain_h_limit + 1e-9 and p.amount > 0

    urgent = [p for p in sim.mail if _is_rescue(p)]
    if not urgent:
        return 0
    need = sum(p.amount for p in urgent)
    # 腾空位：最多清 need，且尽量清到 0 仅当 need 很大
    room = sim.hard_cap - sim.ap
    if room < need:
        # 需要额外空位
        want_room = min(need, sim.hard_cap)
        target = max(0, sim.hard_cap - want_room)
        if sim.ap > target:
            drop = sim.ap - target
            sim.clear_to(
                target,
                cfg.clear_mode,
                note=f"{note_prefix}：清体到 {target}，空出约 {want_room} 领临期邮（共{need}）",
                meta=_attach_clear_recipe(cfg, drop),
            )
    # 只领临期包：按过期排序，逐包 claim
    got_total = 0
    sim.mail.sort(key=lambda p: p.expire_at)
    for _ in range(12):
        urgent = [p for p in sim.mail if _is_rescue(p)]
        if not urgent:
            break
        room = sim.hard_cap - sim.ap
        if room <= 0:
            # 满了还有临期：再清一轮空位（最多再清一个最小临期包）
            urgent.sort(key=lambda p: p.expire_at)
            need_one = min(urgent[0].amount, sim.hard_cap)
            target = max(0, sim.hard_cap - need_one)
            if sim.ap > target:
                drop = sim.ap - target
                sim.clear_to(
                    target,
                    cfg.clear_mode,
                    note=f"{note_prefix}：再清 {drop} 继续领临期包+{urgent[0].amount}",
                    meta=_attach_clear_recipe(cfg, drop),
                )
            room = sim.hard_cap - sim.ap
            if room <= 0:
                break
        # claim 不超过 room，且优先临期
        before = sim.mail_total
        # 临时把非临期挪开：只从临期领
        non_urgent = [p for p in sim.mail if not _is_rescue(p)]
        only_u = [p for p in sim.mail if _is_rescue(p)]
        sim.mail = only_u
        got = sim.claim_from_mail(
            amount=room,
            note=f"{note_prefix}：领取临期邮 +{room}（未临期包保留）",
        )
        # 合并回未临期
        sim.mail.extend(non_urgent)
        got_total += int(got or 0)
        if got <= 0:
            break
        if sim.mail_total >= before:
            break
    return got_total


def _schedule_urgent_mail_watch(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    now: datetime,
    until: datetime,
    spend_at: Optional[datetime] = None,
) -> None:
    """临期监视（与主堆整包领分工）：

    A. role=stack_for_claim 或 到期 ≥ protect_until（花体日 03:50）：
       **绝不**走 0.2h 临期领。留给计划里的「清到空位 → 一次领满 999」。
    B. 其它包：
       - 剩余 >1h（粗小时）：计划步「每 10 分钟 OCR 巡检」直到出现「不到1小时」
       - 进入不到1h：内计时，剩 ≈0.2h 时清空位领取（仅这些包）

    游戏邮箱不显示分钟，只显示「N小时 / 不到1小时」——精确 0.2 靠内计时。
    """
    if not sim.mail or until <= now:
        return
    spend_at = spend_at or until
    protect_until = getattr(sim, "_mail_protect_until", None) or (
        spend_at - timedelta(minutes=25)
    )

    # 分类
    rescue: List[MailParcel] = []
    for p in list(sim.mail):
        role = (getattr(p, "role", "") or "")
        if role == "stack_for_claim":
            continue
        if role in ("rescue", "urgent"):
            rescue.append(p)
            continue
        # 能撑到花体日 03:50（protect_until）的包 = 主堆囤货，绝不走 0.2h
        if p.expire_at >= protect_until:
            continue
        # 剩余仍 ≥12h：一律当囤货（OCR 粗「22小时」族）
        if p.remain_hours(max(now, sim.t)) >= 12.0:
            continue
        if p.amount >= 200 and p.remain_hours(max(now, sim.t)) >= 2.0:
            continue
        rescue.append(p)

    if not rescue:
        # 仍提示：主堆邮走整包领，不巡检 0.2
        if any((getattr(p, "role", "") == "stack_for_claim") or p.amount >= 200 for p in sim.mail):
            if now <= protect_until <= until:
                sim.advance_to(max(min(protect_until, until), sim.t))
                # 不在这里领，由花体日 03:50 步骤领
        return

    seen = set()
    for p in sorted(rescue, key=lambda x: x.expire_at):
        exp = p.expire_at
        key = exp.isoformat(sep=" ", timespec="minutes")
        if key in seen:
            continue
        seen.add(key)
        remain_h_now = (exp - max(now, sim.t)).total_seconds() / 3600.0
        if remain_h_now <= 0:
            continue

        # 粗小时阶段：到期前 1h 起 10 分钟巡检
        watch_at = exp - timedelta(hours=1)
        # 内计时领取：0.2h = 12min
        act_at = exp - timedelta(minutes=12)
        if act_at > until:
            continue
        if act_at < now - timedelta(minutes=40):
            if now < exp:
                act_at = max(now, sim.t)
            else:
                continue

        t_watch = max(now, sim.t, watch_at)
        if t_watch < until and t_watch <= act_at:
            sim.advance_to(max(t_watch, sim.t))
            bag_amt = sum(
                x.amount
                for x in rescue
                if abs((x.expire_at - exp).total_seconds()) < 120
            )
            sim._emit(
                ACTION_NOTIFY,
                "auto",
                note=(
                    f"临期巡检：非囤货邮约 +{bag_amt} 将进「不到1小时」；"
                    f"每 10 分钟识别，一出现不到1h 则内计时，"
                    f"小数点剩≈0.2h 再清体领取（主堆960+囤货不动，留给 "
                    f"{protect_until.strftime('%m-%d %H:%M')} 整包领）"
                ),
                amount=int(bag_amt),
                deadline=exp,
                meta={
                    "urgent_mail_watch": True,
                    "poll_seconds": 600,  # 10 分钟
                    "poll_seconds_under_1h": 120,  # 进入不到1h 后 2 分钟
                    "bag_amount": int(bag_amt),
                    "expire_at": exp.isoformat(sep=" ", timespec="minutes"),
                    "refresh_when_remain_h": 0.2,
                    "only_urgent": True,
                    "skip_stack_mail": True,
                    "protect_until": protect_until.isoformat(sep=" ", timespec="minutes"),
                },
            )
        t_act = max(act_at, sim.t)
        if t_act >= until:
            continue
        sim.advance_to(t_act)
        _claim_urgent_mail_bags(
            sim,
            cfg,
            remain_h_limit=0.25,
            note_prefix="临期邮领取（内计时≈0.2h；跳过主堆囤货）",
        )


def _after_claim_refresh_mail_ttl(
    sim: _Sim,
    cfg: HoardConfig,
    *,
    reason: str,
) -> None:
    """领完可囤源后：只垫满角色空位，绝不把刚进的 24h 邮整锅刷光。"""
    if sim.mail_total <= 0:
        return
    if sim.ap < sim.hard_cap:
        _pad_mail_small_first(sim, cfg, rotate_rounds=0)
    # 仅当已经有 ≤1h 临期包才救
    if any(p.remain_hours(sim.t) <= 1.0 for p in sim.mail):
        _claim_urgent_mail_bags(sim, cfg, remain_h_limit=1.0, note_prefix=f"{reason}·临期邮")



def _diligent_buy_tubes_to_near_full(
    sim: "_Sim",
    cfg: "HoardConfig",
    max_tubes: int,
    reason: str,
    hard: int,
    near_full: int,
) -> int:
    """按缺口买管，返回实际买的管数。不超过 max_tubes。"""
    if max_tubes <= 0:
        return 0
    if sim.ap >= near_full:
        return 0
    need = hard - sim.ap
    n_fit = need // TUBE_AP
    if n_fit <= 0:
        if need < 60:
            return 0
        if max_tubes >= 1 and sim.ap > hard - TUBE_AP:
            target = hard - TUBE_AP
            drop = sim.ap - target
            if drop > 0:
                sim.clear_to(
                    target,
                    cfg.clear_mode,
                    note=(
                        f"{reason}：差 {need} 不足一管，清到 {target} 再买 1 管"
                        f"（上限×{max_tubes}，买后≈{hard}）"
                    ),
                    meta=_attach_clear_recipe(cfg, drop),
                )
            n_fit = 1
        else:
            return 0
    n = min(max_tubes, max(1, n_fit))
    gain = tube_gain_ap(n)
    if sim.ap + gain > hard:
        target = hard - gain
        if sim.ap > target:
            drop = sim.ap - target
            sim.clear_to(
                target,
                cfg.clear_mode,
                note=(
                    f"{reason}：清到 {target} 后买 {n} 管 +{gain}"
                    f"（预算上限 {max_tubes} 管，不是必买满）"
                ),
                meta=_attach_clear_recipe(cfg, drop),
            )
    if sim.ap + tube_gain_ap(n) <= hard:
        sim.buy_tubes(n, cfg.clear_mode)
        return n
    room = hard - sim.ap
    n2 = min(max_tubes, room // TUBE_AP)
    if n2 > 0:
        sim.buy_tubes(n2, cfg.clear_mode)
        return n2
    return 0


def _diligent_schedule_stack_claims(
    sim: "_Sim",
    cfg: "HoardConfig",
    now: datetime,
    until: datetime,
    note_prefix: str,
    hard: int,
) -> None:
    """按识别明细登记领取点：计划写清几点领哪几包。"""
    if not sim.mail:
        return

    def _planned_claim_at_for_parcel(p: MailParcel) -> datetime:
        return p.expire_at - timedelta(minutes=6)

    buckets: Dict[str, List[MailParcel]] = {}
    for p in list(sim.mail):
        if p.amount <= 0:
            continue
        if p.remain_hours(sim.t) >= 48:
            act = min(until - timedelta(minutes=5), p.expire_at - timedelta(minutes=6))
        else:
            act = _planned_claim_at_for_parcel(p)
        if act > until + timedelta(minutes=1):
            continue
        if act < sim.t - timedelta(minutes=5):
            act = max(sim.t, now)
        key = act.strftime("%Y-%m-%d %H:%M")
        buckets.setdefault(key, []).append(p)

    for key in sorted(buckets.keys()):
        group = buckets[key]
        when = datetime.strptime(key, "%Y-%m-%d %H:%M")
        if when > until + timedelta(minutes=1):
            continue
        amt = sum(int(p.amount) for p in group)
        if amt <= 0:
            continue
        sim.advance_to(max(when, sim.t))
        detail = "、".join(f"{p.amount}@{p.remain_hours(when):.1f}h" for p in group[:8])
        if len(group) > 8:
            detail += f"…共{len(group)}封"
        need = min(amt, hard)
        target = max(0, hard - need)
        if sim.ap > target:
            drop = sim.ap - target
            sim.clear_to(
                target,
                cfg.clear_mode,
                note=(
                    f"{note_prefix} {when.strftime('%m-%d %H:%M')}：清到 {target}，"
                    f"空出 {need} 领计划邮 {detail}"
                ),
                meta={
                    **_attach_clear_recipe(cfg, drop),
                    "planned_mail_claim": True,
                    "claim_when": key,
                    "claim_amounts": [int(p.amount) for p in group],
                },
            )
        keep = [p for p in sim.mail if p not in group]
        only = [p for p in sim.mail if p in group]
        sim.mail = only
        sim.claim_from_mail(
            amount=need,
            note=(
                f"{note_prefix} {when.strftime('%m-%d %H:%M')}：按计划领取 +{need}"
                f"（{detail}｜设备端为一键全领）"
            ),
        )
        sim.mail.extend(keep)


def _stack_drain_old_mail(sim: "_Sim", cfg: "HoardConfig", hard: int) -> None:
    """主堆 03:50：先清体再领完旧邮（循环清→领直到旧邮领完）。"""
    for _ in range(8):
        if sim.mail_total <= 0:
            break
        if sim.ap >= hard:
            need = min(int(sim.mail_total), hard)
            target = max(0, hard - need)
            if sim.ap > target:
                drop = sim.ap - target
                sim.clear_to(
                    target,
                    cfg.clear_mode,
                    note=f"主堆 03:50：清到 {target}，空出 {need} 领完旧邮",
                    meta=_attach_clear_recipe(cfg, drop),
                )
            else:
                break
        got = sim.claim_from_mail(note="主堆前领取旧邮")
        if got <= 0:
            break


def _stack_early_tubes(
    sim: "_Sim",
    cfg: "HoardConfig",
    max_tubes: int,
    near_full: int,
    hard: int,
    late_after_main_reset: bool,
) -> int:
    """主堆 03:50 预补管：偏低先抬近满以便咖啡溢出进邮；已近满/已满不买。"""
    bought_early = 0
    if (not late_after_main_reset) and sim.ap < near_full and max_tubes > 0:
        if sim.ap < hard - TUBE_AP:
            bought_early = _diligent_buy_tubes_to_near_full(
                sim, cfg, max_tubes, "主堆 03:50 预补", hard, near_full
            )
            if bought_early > 0:
                sim._emit(
                    ACTION_NOTIFY,
                    "auto",
                    note=(
                        f"主堆预买 {bought_early} 管（上限 {max_tubes}）："
                        f"当前偏低，先抬近满以便咖啡溢出进邮"
                    ),
                    meta={"tubes_bought_early": bought_early, "tubes_cap": max_tubes},
                )
        else:
            sim._emit(
                ACTION_NOTIFY,
                "auto",
                note=(
                    f"主堆体约 {sim.ap} 已接近满，跳过预买"
                    f"（上限 {max_tubes} 管留到领完咖啡/日替再按缺口补）"
                ),
                meta={"skip_early_buy": True, "tubes_cap": max_tubes},
            )
    elif max_tubes > 0 and sim.ap >= near_full:
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=(
                f"主堆体已 {sim.ap}≈满：不买管（上限 {max_tubes} 管仅作预算，"
                f"禁止 999→清→再买满管）"
            ),
            meta={"skip_buy_already_full": True, "tubes_cap": max_tubes},
        )
    return bought_early


def _stack_daily_jjc(
    sim: "_Sim",
    cfg: "HoardConfig",
    late_after_main_reset: bool,
    now: datetime,
    day_reset_main: datetime,
    spend_at: datetime,
    claim_mail_at: datetime,
    hard: int,
) -> None:
    """主堆日 04:00 动态竞技场：日替/咖啡补领 → 按识别邮量买 JJC。"""
    do_daily_jjc = (
        day_reset_main < spend_at
        and now < claim_mail_at
        and (
            late_after_main_reset
            or day_reset_main >= sim.t - timedelta(minutes=1)
        )
    )
    if not do_daily_jjc:
        return
    if not late_after_main_reset:
        sim.advance_to(max(day_reset_main, sim.t))
    else:
        sim.advance_to(max(now, sim.t))
    saved_jjc_mode = cfg.jjc_buy_mode
    saved_jjc_ap = cfg.jjc_ap
    cfg.jjc_buy_mode = JJC_BUY_NONE
    cfg.jjc_ap = 0
    try:
        _claim_daily_sources(
            sim,
            cfg,
            skip_claimed_today=True if late_after_main_reset else False,
            include_free=True,
        )
    finally:
        cfg.jjc_buy_mode = saved_jjc_mode
        cfg.jjc_ap = saved_jjc_ap

    # 主堆日 04:00：03:50 已领过咖啡，日界后又满，必须再领一次进邮
    try:
        _claim_cafe_overflow(
            sim,
            cfg,
            "主堆 04:00：领取咖啡厅（日界后已满，溢出进邮）",
        )
    except Exception:
        sim.claim_cafe(note="主堆 04:00：领取咖啡厅奖励")

    if cfg.use_ap_card and cfg.ap_card_amount > 0:
        sim.use_ap_card(cfg.ap_card_amount)

    has_bags = bool(getattr(cfg, "mail_bags", None)) or int(sim.mail_total or 0) > 0
    if (not has_bags) and (not late_after_main_reset):
        sim._emit(
            ACTION_CLAIM_MAIL,
            "auto",
            note="识别邮箱限时体力（确认邮量，供竞技场动态购买；不点一键领）",
            amount=0,
            meta={
                "scan_only": True,
                "after_daily": True,
                "expect_mail": sim.mail_total,
            },
        )
    else:
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=(
                f"沿用已有邮箱明细约 {sim.mail_total}（不重复 OCR；"
                f"不对可在表单改）"
            ),
            meta={"skip_rescan": True, "expect_mail": sim.mail_total},
        )

    base_mail = int(sim.mail_total)
    # 体力卡溢出进邮 → 从 JJC 可用空位扣除
    ap_card_overflow = 0
    if getattr(cfg, "use_ap_card", False) and int(getattr(cfg, "ap_card_amount", 0) or 0) > 0:
        ap_card_overflow = int(cfg.ap_card_amount)
    jjc_plan = plan_jjc_under_mail_cap(
        base_mail,
        ap_card_overflow=ap_card_overflow,
        target=MAIL_STACK_TARGET,
        hard_cap=min(hard, MAIL_STACK_HARD),
        prefer_mode=str(saved_jjc_mode or JJC_BUY_30_60),
    )
    jjc_amt = int(jjc_plan.get("amount") or 0)
    if jjc_amt > 0:
        sim.claim_hoardable(
            ACTION_CLAIM_JJC,
            jjc_amt,
            jjc_plan.get("note")
            or f"竞技场 +{jjc_amt}（按识别邮量动态，目标邮≈{MAIL_STACK_TARGET}）",
            meta={
                "jjc_dynamic": True,
                "refresh": jjc_plan.get("refresh"),
                "buy_30": jjc_plan.get("buy_30"),
                "buy_60": jjc_plan.get("buy_60"),
                "mode": jjc_plan.get("mode"),
                "base_mail": base_mail,
                "mail_target": MAIL_STACK_TARGET,
                "mail_hard": min(hard, MAIL_STACK_HARD),
            },
        )
    else:
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=jjc_plan.get("note") or f"邮箱已≈{base_mail}，跳过竞技场",
            meta={"jjc_dynamic": True, "amount": 0, "base_mail": base_mail},
        )


def _diligent_main_stack_phase(
    sim: "_Sim",
    cfg: "HoardConfig",
    now: datetime,
    spend_at: datetime,
    main_at: datetime,
    day_reset_main: datetime,
    day_reset_spend: datetime,
    claim_mail_at: datetime,
    soft: int,
    hard: int,
    max_tubes: int,
    near_full: int,
) -> None:
    """主堆日 03:50～04:00：旧邮/咖啡/日替/动态JJC/角色清0。"""
    late_after_main_reset = now >= day_reset_main
    if late_after_main_reset:
        sim.advance_to(max(now, sim.t))
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=(
                f"已过主堆 04:00（现在 {now.strftime('%H:%M')}）："
                f"保留邮箱囤货约 {sim.mail_total}，不再领旧邮；"
                f"只补日替/竞技场（邮→≈{MAIL_STACK_TARGET}）后清角色到 0"
            ),
            meta={"late_main_stack": True, "keep_mail": sim.mail_total},
        )
    else:
        sim.advance_to(max(main_at, sim.t))

    if not late_after_main_reset:
        _stack_drain_old_mail(sim, cfg, hard)

    _stack_early_tubes(sim, cfg, max_tubes, near_full, hard, late_after_main_reset)

    sim._mail_push_role = "stack_for_claim"  # type: ignore[attr-defined]

    if not late_after_main_reset:
        skip_now = server_day_start(sim.t) == server_day_start(now)
        if skip_now and _today_unclaimed_gain(cfg) > 0:
            saved_jjc_mode = cfg.jjc_buy_mode
            saved_jjc_ap = cfg.jjc_ap
            cfg.jjc_buy_mode = JJC_BUY_NONE
            cfg.jjc_ap = 0
            try:
                _claim_daily_sources(sim, cfg, skip_claimed_today=True, include_free=True)
            finally:
                cfg.jjc_buy_mode = saved_jjc_mode
                cfg.jjc_ap = saved_jjc_ap

        _claim_cafe_overflow(
            sim,
            cfg,
            "领取咖啡厅奖励（重置计时，溢出进邮）",
        )
        sim._emit(
            ACTION_CLAIM_MAIL,
            "auto",
            note="主堆识别邮箱（仅此一次写入明细；之后不自动重扫）",
            amount=0,
            meta={
                "scan_only": True,
                "after_cafe": True,
                "once_stack_scan": True,
                "expect_mail": sim.mail_total,
            },
        )

    _stack_daily_jjc(
        sim, cfg, late_after_main_reset, now,
        day_reset_main, spend_at, claim_mail_at, hard
    )

    hours = max(0.0, (claim_mail_at - sim.t).total_seconds() / 3600.0)
    can_regen = int(hours * float(cfg.natural_ap_per_hour))
    drop = sim.ap
    mail_keep = int(sim.mail_total)
    if drop > 0:
        sim.clear_to(
            0,
            cfg.clear_mode,
            note=(
                f"主堆收工：角色清 0（约 {hours:.0f}h 自回≈{min(can_regen, soft)}）；"
                f"邮箱囤货约 {mail_keep}（目标≈{MAIL_STACK_TARGET}，硬顶{MAIL_STACK_HARD}；"
                f"花体日前按计划 0.2 领邮，主堆日 03:50 只负责堆邮）"
            ),
            meta={
                **_attach_clear_recipe(cfg, drop),
                "mail_keep": mail_keep,
                "mail_target": MAIL_STACK_TARGET,
            },
        )
    else:
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=f"主堆收工：角色已是 0；邮箱囤货约 {mail_keep}（目标≈{MAIL_STACK_TARGET}）",
            meta={"mail_keep": mail_keep},
        )
    sim._mail_push_role = ""  # type: ignore[attr-defined]


def _diligent_pre_main_keep_ap(
    sim: _Sim,
    now: datetime,
    main_at: datetime,
    hard: int,
    soft: int,
    tubes: int,
    unclaimed: int,
) -> None:
    """主堆 03:50 前：高体力保持，不预清（只发策略说明）。"""
    ready_full = (
        sim.ap >= hard - 1
        and sim.mail_total <= 0
        and unclaimed <= 0
        and now >= main_at - timedelta(hours=6)
    )
    if ready_full:
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=f"主堆前已是体{sim.ap}/邮0 且今日源已领完：不再预清砸体，直等 {main_at.strftime('%m-%d %H:%M')}",
            meta={"skip_preclear": True},
        )
    elif now < main_at - timedelta(minutes=5):
        if sim.ap >= hard - 30:
            sim._emit(
                ACTION_NOTIFY,
                "auto",
                note=(
                    f"主堆前体已≈{sim.ap}：保持，不预清；"
                    f"买管上限×{tubes}只在 03:50 仍不够近满时按缺口买"
                ),
                meta={"keep_high_ap": True},
            )
        elif sim.ap > soft:
            sim._emit(
                ACTION_NOTIFY,
                "auto",
                note=(
                    f"主堆前体约 {sim.ap}：保持到 03:50（不砸到软顶）；"
                    f"届时按缺口最多买 {tubes} 管，已近满则 0 管"
                ),
                meta={"keep_mid_ap": True, "tubes_cap": tubes},
            )


def _diligent_pre_reset_mail_flush(
    sim: _Sim,
    cfg: HoardConfig,
    now: datetime,
    day_reset_spend: datetime,
    spend_at: datetime,
    hard: int,
) -> None:
    """花体日前：按计划 0.2 动态领邮；04:00 前兜底清体领完短倒计时邮。"""
    pre_reset = day_reset_spend - timedelta(minutes=5)
    if not (pre_reset > sim.t and pre_reset < spend_at):
        return
    _diligent_schedule_stack_claims(
        sim, cfg, now, pre_reset, "花体日前按计划领邮", hard
    )
    sim.advance_to(max(pre_reset, sim.t))
    short = [
        p for p in list(sim.mail)
        if p.amount > 0 and p.remain_hours(sim.t) <= 1.05 and p.remain_hours(sim.t) < 48
    ]
    if short:
        need = min(sum(p.amount for p in short), hard)
        target = max(0, hard - need)
        if sim.ap > target:
            drop = sim.ap - target
            sim.clear_to(
                target,
                cfg.clear_mode,
                note=(
                    f"花体日 04:00 前兜底：清到 {target}，空出 {need}，"
                    f"领完不足1h 邮，避免过期"
                ),
                meta={**_attach_clear_recipe(cfg, drop), "pre_reset_mail_flush": True},
            )
        keep = [p for p in sim.mail if p not in short]
        sim.mail = short
        sim.claim_from_mail(
            amount=need,
            note=f"花体日 04:00 前兜底：领取短倒计时邮 +{need}",
        )
        sim.mail.extend(keep)
    sim._emit(
        ACTION_NOTIFY,
        "auto",
        note=(
            f"花体日 04:00 前邮处理完毕：体{sim.ap}/邮{sim.mail_total}"
            f"（目标：短倒计时邮已清，长邮可留）"
        ),
        meta={"spend_day_mail_claim": True, "expect_ap": sim.ap, "expect_mail": sim.mail_total},
    )


def _diligent_spend_day_daily_claim(
    sim: _Sim,
    cfg: HoardConfig,
    now: datetime,
    day_reset_spend: datetime,
    spend_at: datetime,
) -> None:
    """花体日 04:00：日替进邮（含礼包）+ 咖啡（03:50 领过，04:00 又满）。"""
    if not (day_reset_spend > sim.t and day_reset_spend < spend_at):
        return
    sim.advance_to(day_reset_spend)
    skip = server_day_start(day_reset_spend) == server_day_start(now)
    _claim_daily_sources(sim, cfg, skip_claimed_today=skip, include_free=True)
    # 日界后咖啡立刻满额，必须并入 04:00 批次，否则会拖到花体才提醒
    try:
        _claim_cafe_overflow(
            sim,
            cfg,
            "花体日 04:00：领取咖啡厅（日界后已满，溢出进邮）",
        )
    except Exception:
        sim.claim_cafe(note="花体日 04:00：领取咖啡厅奖励")
    sim._emit(
        ACTION_NOTIFY,
        "auto",
        note="花体日 04:00：已领小组/任务/竞技场/礼包/咖啡进邮",
        meta={
            "spend_day_daily_claim": True,
            "include_free": True,
            "include_cafe": True,
        },
    )


def _build_diligent_plan(sim: _Sim, cfg: HoardConfig, now: datetime, spend_at: datetime) -> None:
    """勤奋囤体（用户校正后的核心）。"""
    tubes = int(cfg.tubes or 0)
    soft = int(cfg.natural_soft_cap or AP_SOFT_NATURAL_CAP)
    hard = int(sim.hard_cap)
    unclaimed = _today_unclaimed_gain(cfg)

    main_at = _stack_day_0350(spend_at, 1)
    spend_0350 = _stack_day_0350(spend_at, 0)
    if spend_at.hour < 4 or (spend_at.hour == 4 and spend_at.minute <= 10):
        claim_mail_at = min(spend_0350, spend_at - timedelta(minutes=20))
        if claim_mail_at < server_day_start(spend_at) - timedelta(hours=1):
            claim_mail_at = spend_at - timedelta(minutes=20)
    else:
        claim_mail_at = spend_0350
    claim_mail_at = datetime(spend_at.year, spend_at.month, spend_at.day, 3, 50, 0)
    if claim_mail_at >= spend_at:
        claim_mail_at = spend_at - timedelta(minutes=20)
    day_reset_main = server_day_start(main_at) + timedelta(days=1)
    day_reset_spend = server_day_start(spend_at)

    sim.advance_to(now)

    # 主堆日 03:50：只用于「领到邮箱囤货」的收工锚点（方便算一夜自回）
    sim._mail_protect_until = day_reset_spend  # type: ignore[attr-defined]

    # ----- 0) 已有邮箱：撑不到主堆/整包领点的非囤货，才走临期救 -----
    if sim.mail_total > 0 and now < main_at:
        _schedule_urgent_mail_watch(
            sim, cfg, now=now, until=main_at, spend_at=spend_at
        )

    # ----- 1) 主堆 03:50 前：高体力保持，不预清 -----
    _diligent_pre_main_keep_ap(sim, now, main_at, hard, soft, tubes, unclaimed)

    # ----- 2) 主堆日 03:50～04:00 -----
    if main_at < spend_at and main_at >= now - timedelta(hours=20):
        max_tubes = max(0, int(tubes or 0))
        near_full = max(0, hard - 9)
        _diligent_main_stack_phase(
            sim,
            cfg,
            now,
            spend_at,
            main_at,
            day_reset_main,
            day_reset_spend,
            claim_mail_at,
            soft,
            hard,
            max_tubes,
            near_full,
        )

    # ----- 3) 花体日前：按计划 0.2 动态领邮 -----
    _diligent_pre_reset_mail_flush(sim, cfg, now, day_reset_spend, spend_at, hard)
    # ----- 4) 花体日 04:00：日替进邮（含礼包）+ 咖啡（03:50 领过，04:00 又满）-----
    _diligent_spend_day_daily_claim(sim, cfg, now, day_reset_spend, spend_at)

    # ----- 5) 挂到花体 -----
    if sim.t < spend_at:
        if sim.mail_total > 0:
            _schedule_urgent_mail_watch(
                sim, cfg, now=sim.t, until=spend_at, spend_at=spend_at
            )
        if sim.t < spend_at:
            sim.hold_until(
                spend_at,
                note="挂机到花体（角色近满 + 邮箱倒计时；临期会清空位再领）",
            )

    sim.advance_to(spend_at)
    sim._tick_cafe(spend_at)
    cafe_at_spend = int(round(sim.cafe_stock))
    sim._cafe_at_spend = cafe_at_spend  # type: ignore[attr-defined]
    if cafe_at_spend > 0:
        sim._emit(
            ACTION_NOTIFY,
            "manual",
            note=(
                f"花体时咖啡≈{cafe_at_spend}。顺序：先花角色体/小额邮，再大额邮与咖啡；"
                f"领邮必须有空位"
            ),
            amount=cafe_at_spend,
            meta={"cafe_at_spend": cafe_at_spend},
        )
    sim.spend_ready(
        note=(
            f"到点花体：体≈{sim.ap} + 邮≈{sim.mail_total}"
            + (f" + 咖啡≈{cafe_at_spend}" if cafe_at_spend else "")
        )
    )


def _build_lazy_plan(sim: _Sim, cfg: HoardConfig, now: datetime, spend_at: datetime) -> None:
    """懒人：不买体；日替领源进邮；邮箱储备窗 = 花体前一天同时钟+10分。"""
    reserve_at = _mail_reserve_window(spend_at)
    spend_day = server_day_start(spend_at)

    # 日替领源
    r0 = server_day_start(now)
    if r0 <= now:
        r0 += timedelta(days=1)
    while r0 < spend_at:
        t = r0 + timedelta(minutes=5)
        if t >= now and t < reserve_at:
            sim.advance_to(t)
            skip = server_day_start(t) == server_day_start(now)
            _claim_daily_sources(sim, cfg, skip_claimed_today=skip, include_free=True)
            _after_overflow_sources(sim, cfg, next_anchor=min(reserve_at, spend_at), do_pad=True)
        r0 += timedelta(days=1)

    # 储备窗
    if reserve_at > sim.t and reserve_at < spend_at:
        sim.advance_to(max(reserve_at, now))
    if sim.t < spend_at and sim.t <= reserve_at + timedelta(minutes=30):
        if sim.ap < sim.hard_cap and sim.mail_total > 0:
            room = sim.hard_cap - sim.ap
            sim.mail.sort(key=lambda p: (p.amount, p.expire_at))
            sim.claim_from_mail(
                amount=room,
                note=f"储备窗垫满体力 +{room}（剩余邮箱保留）",
            )
        # 保持近满+留邮
        sim._emit(
            ACTION_NOTIFY,
            "auto",
            note=(
                f"邮箱储备窗 {reserve_at.strftime('%m-%d %H:%M')} "
                f"（花体前一天同时钟+10分）：体力近满、邮箱保留，花体时邮约剩10分钟"
            ),
            meta={"mail_reserve_window": True, "expect_mail": sim.mail_total},
        )
        sim.hold_until(spend_at, note="懒人 Hold 至花体")

    sim.advance_to(spend_at)
    sim._tick_cafe(spend_at)
    cafe_at_spend = int(round(sim.cafe_stock))
    sim._cafe_at_spend = cafe_at_spend  # type: ignore[attr-defined]
    if cafe_at_spend > 0:
        sim._emit(
            ACTION_NOTIFY,
            "manual",
            note=f"花体时咖啡≈{cafe_at_spend}；先小额邮再大额/咖啡",
            amount=cafe_at_spend,
            meta={"cafe_at_spend": cafe_at_spend},
        )
    sim.spend_ready(
        note=f"到点花体：体≈{sim.ap} + 邮箱≈{sim.mail_total}"
        + (f" + 咖啡≈{cafe_at_spend}" if cafe_at_spend else "")
    )



def _prepare_mail_parcels(
    cfg: HoardConfig, existing_mail: Optional[Sequence[MailParcel]], now: datetime
) -> List[MailParcel]:
    """邮箱明细：优先用表单/OCR 明细（带剩余小时），否则才用总量估算。"""
    mail_parcels: List[MailParcel] = list(existing_mail or [])
    if not mail_parcels:
        bags = getattr(cfg, "mail_bags", None) or []
        if bags:
            mail_parcels = mail_parcels_from_bags(bags, now)
        elif int(cfg.existing_mail_ap or 0) > 0:
            for b in bags_from_total_estimate(int(cfg.existing_mail_ap), now):
                mail_parcels.append(
                    MailParcel(amount=b.amount, overflow_at=b.overflow_at)
                )
    return mail_parcels


def _normalize_tube_budget(cfg: HoardConfig, now: datetime, spend_at: datetime) -> None:
    """自动买体数按距花体天数分档；tube_days 归一到 0～3。"""
    if cfg.auto_tubes or int(cfg.tubes) < 0:
        hours_to_spend = max(0.0, (spend_at - now).total_seconds() / 3600.0)
        days = hours_to_spend / 24.0
        if days >= 2.5:
            cfg.tubes = 3
        elif days >= 1.5:
            cfg.tubes = 4
        elif days >= 0.8:
            cfg.tubes = 5
        else:
            cfg.tubes = 6
        cfg.auto_tubes = True

    try:
        cfg.tube_days = max(0, min(3, int(getattr(cfg, "tube_days", 1) or 1)))
    except Exception:
        cfg.tube_days = 1
    if cfg.tubes <= 0:
        cfg.tube_days = 0


def _append_plan_warnings(sim: _Sim, cfg: HoardConfig) -> None:
    """任务日程提醒 + 角色体+邮箱合计缺口提示。"""
    # 任务日程提醒
    task_steps = [s for s in sim.steps if s.action == ACTION_CLAIM_TASK]
    if task_steps and not cfg.task_claimed:
        first_task = min(task_steps, key=lambda s: s.when)
        if cfg.lesson_include():
            sim.warnings.append(
                f"日程体力 +{TASK_LESSON_AP} 未领：请不晚于 "
                f"{first_task.when.strftime('%m-%d %H:%M')} 做完日程并领取（执行后会勾已领）"
            )

    # 勤勉堆邮路径：花体日 03:50 才把邮一次性领到角色，规划期末角色体常 <999，
    # 不能再用「花体前体约 x/999 还差」吓人。只在「角色+邮箱」合计仍明显不够时提示。
    mail_ap = int(sum(int(getattr(p, "amount", 0) or 0) for p in sim.mail))
    reachable = int(sim.ap) + mail_ap
    if reachable + 30 < sim.hard_cap:  # 允许咖啡等未建模小额
        need = sim.hard_cap - reachable
        if need > 0:
            sim.warnings.append(
                f"按当前时间轴，角色体+邮箱合计约 {reachable}，距花体日拉满 999 还差约 {need}。"
                f"可加大买管上限或检查任务/咖啡/JJC 是否会进邮。"
            )


def _build_plan_summary(
    sim: _Sim, cfg: HoardConfig, cafe0: int, cafe_at_spend: int, lead: int
) -> dict:
    """汇总计划摘要（供 UI 与账本展示）。"""
    return {
        "final_ap": sim.ap,
        "final_mail": sim.mail_total,
        "total_spendable": sim.ap + sim.mail_total,
        "tubes": cfg.tubes,
        "tube_days": int(getattr(cfg, "tube_days", 1) or 1),
        "tube_ap": tube_gain_ap(cfg.tubes) * max(1, int(getattr(cfg, "tube_days", 1) or 1)),
        "pyroxene_cost": tube_cost_pyroxene(cfg.tubes)
        * max(1, int(getattr(cfg, "tube_days", 1) or 1) if cfg.tubes else 0),
        "jjc_ap_per_day": cfg.resolved_jjc_ap(),
        "task_ap_per_day": cfg.resolved_task_ap(),
        "strategy": cfg.strategy,
        "clear_mode": cfg.clear_mode,
        "lead_days": lead,
        "cafe_initial": cafe0,
        "cafe_at_spend": cafe_at_spend,
        "hard_cap": cfg.hard_cap,
        "soft_cap": cfg.natural_soft_cap,
        "auto_tubes": bool(cfg.auto_tubes),
        "mail_parcels": len(sim.mail),
        "total_with_cafe": sim.ap + sim.mail_total + cafe_at_spend,
        "pad_script": next(
            (
                (s.meta or {}).get("mail_pad_script")
                for s in reversed(sim.steps)
                if (s.meta or {}).get("mail_pad_script")
            ),
            "",
        ),
    }


def build_plan(
    cfg: HoardConfig,
    now: Optional[datetime] = None,
    current_ap: int = 0,
    existing_mail: Optional[Sequence[MailParcel]] = None,
) -> HoardPlan:
    """根据配置生成囤体时间轴。目标：花体点角色≈999 + 邮箱尽量多近过期体。"""
    now = now or datetime.now().replace(second=0, microsecond=0)
    if not isinstance(cfg, HoardConfig):
        cfg = HoardConfig.from_mapping(cfg)  # type: ignore[arg-type]
    else:
        cfg = HoardConfig.from_mapping(cfg.to_dict())

    if cfg.current_ap is not None and current_ap == 0:
        current_ap = int(cfg.current_ap)
    if current_ap <= 0:
        # config 没存当前体力（用户没填/没回写）：按满体兜底，
        # 否则 sim.ap=0 → clear_to 因 ap<=0 跳过，清体步骤直接消失
        try:
            current_ap = int(cfg.hard_cap) or 0
        except Exception:
            pass

    spend_at = _resolve_spend_at(cfg, now)

    mail_parcels = _prepare_mail_parcels(cfg, existing_mail, now)

    # 自动买体数 / tube_days 归一
    _normalize_tube_budget(cfg, now, spend_at)

    sim = _Sim(
        now=now,
        ap=current_ap,
        mail_parcels=mail_parcels,
        natural_per_hour=cfg.natural_ap_per_hour,
        natural_soft_cap=cfg.natural_soft_cap,
        hard_cap=cfg.hard_cap,
    )
    cafe0 = estimate_cafe_claimable(
        cfg.cafe_hours_since_claim,
        cfg.cafe_ap_per_hour,
        cfg.cafe_ap_full_cap,
        cfg.cafe_claimable_manual,
    )
    sim.set_cafe(cafe0, cfg.cafe_ap_per_hour, cfg.cafe_ap_full_cap)

    if cfg.current_ap is None and current_ap == 0:
        sim.warnings.append(
            "未填写「当前体力」，计划按 0 起算；请填游戏内实时体力后重算"
        )

    lead = _strategy_lead_days(cfg.strategy, int(getattr(cfg, "tube_days", 1) or 1))

    if cfg.strategy == STRATEGY_XIUXIAN and int(cfg.tubes or 0) > 0:
        _build_diligent_plan(sim, cfg, now, spend_at)
    else:
        _build_lazy_plan(sim, cfg, now, spend_at)

    cafe_at_spend = int(getattr(sim, "_cafe_at_spend", 0) or 0)
    if cafe_at_spend <= 0:
        sim._tick_cafe(spend_at)
        cafe_at_spend = int(round(sim.cafe_stock))

    _append_plan_warnings(sim, cfg)

    # 时间轴按 when 严格升序落盘（稳定排序：同刻保持生成先后语义）；
    # 里程碑（到点花体等）打 meta.milestone，UI 单独渲染，不混作普通执行步骤
    sim.steps.sort(key=lambda s: s.when)
    for _s in sim.steps:
        if _s.action == ACTION_SPEND_READY:
            _s.meta.setdefault("milestone", True)

    plan = HoardPlan(
        config=cfg,
        generated_at=now,
        spend_at=spend_at,
        steps=sim.steps,
        mail_parcels=list(sim.mail),
        warnings=list(sim.warnings),
        summary=_build_plan_summary(sim, cfg, cafe0, cafe_at_spend, lead),
    )
    if plan.summary["final_mail"] <= 0 and int(plan.summary.get("cafe_at_spend") or 0) <= 0:
        plan.warnings.append(
            "推演结果邮箱与花体时咖啡都≈0。请检查：提前天数、竞技场店、咖啡可领、是否过早领光。"
        )
    return plan


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off", ""):
        return False
    return bool(value)


def _as_optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None



def _lesson_claimed_from_config(_get) -> bool:
    """UI「日程50体」开关：已领=True / 未领=False。

    新键 hoard_ap_lesson_claimed；若无则看 hoard_ap_lesson_ready：
    - 历史坑：旧 UI 把 lesson_ready 默认 True 且开关文案是已领/未领，
      实际却当「会做日程」。现统一：有 lesson_claimed 用它；
      否则若显式写了 lesson_ready，则 **取反** 不再使用（易错），
      默认未领（False）让计划去领 +50。
    """
    raw = _get("hoard_ap_lesson_claimed", None)
    if raw is not None and str(raw).strip() != "":
        return _as_bool(raw, False)
    # 无新键：默认未领，让勤奋轴去领日程
    return False



def _parse_mail_bags_cfg(_get) -> List[Dict[str, Any]]:
    """从 config 读邮箱明细 JSON / 列表。"""
    raw = _get("hoard_ap_mail_bags_json", None)
    if raw is None:
        raw = _get("hoard_ap_mail_bags", None)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [b for b in raw if isinstance(b, dict)]
    s = str(raw or "").strip()
    if not s:
        return []
    try:
        import json
        data = json.loads(s)
        if isinstance(data, list):
            return [b for b in data if isinstance(b, dict)]
    except Exception:
        pass
    # 兼容 20@1,30@18
    bags = []
    for part in s.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "@" in part:
            a, h = part.split("@", 1)
            try:
                bags.append({"amount": int(float(a)), "remain_hours": float(h)})
            except Exception:
                continue
        else:
            try:
                bags.append({"amount": int(float(part)), "remain_hours": 23.0})
            except Exception:
                continue
    return bags


def build_plan_from_user_config(config_obj: Any, now: Optional[datetime] = None) -> HoardPlan:
    """从 BAAS config dataclass / dict 读囤体字段。"""

    def _get(key: str, default: Any = None) -> Any:
        if isinstance(config_obj, dict):
            return config_obj.get(key, default)
        return getattr(config_obj, key, default)

    manual = _get("hoard_ap_cafe_claimable_manual", "")
    try:
        manual_val: Optional[float] = (
            float(manual) if str(manual).strip() != "" else None
        )
    except (TypeError, ValueError):
        manual_val = None

    current_ap_cfg = _as_optional_int(_get("hoard_ap_current_ap", ""))
    mail_ap_cfg = _as_optional_int(_get("hoard_ap_mail_ap", "")) or 0

    # JJC：优先囤体自己的 mode/refresh；否则从商店配置推断
    jjc_mode = str(_get("hoard_ap_jjc_buy_mode", "") or "").strip()
    jjc_refresh = _as_optional_int(_get("hoard_ap_jjc_refresh", ""))
    if not jjc_mode:
        jjc_mode, jjc_refresh_infer = _infer_jjc_from_shop(config_obj)
        if jjc_refresh is None:
            jjc_refresh = jjc_refresh_infer
    if jjc_refresh is None:
        jjc_refresh = _as_optional_int(_get("TacticalChallengeShopRefreshTime", 0)) or 0

    tubes_raw = str(_get("hoard_ap_tubes", "3") or "3").strip().lower()
    auto_tubes = tubes_raw in ("", "auto", "自动")
    try:
        tubes_val = 3 if auto_tubes else int(float(tubes_raw))
    except Exception:
        tubes_val, auto_tubes = 3, True

    tube_days_val = _as_optional_int(_get("hoard_ap_tube_days", 2))
    if tube_days_val is None:
        tube_days_val = 2
    tube_days_val = max(0, min(3, int(tube_days_val)))
    hard_cap = _as_optional_int(_get("hoard_ap_hard_cap", 999)) or AP_HARD_CAP
    soft_cap = _as_optional_int(_get("hoard_ap_soft_cap", 160)) or AP_SOFT_NATURAL_CAP

    cafe_cap_raw = _get("hoard_ap_cafe_ap_full_cap", CAFE_AP_FULL_CAP)
    try:
        cafe_cap_v = float(cafe_cap_raw)
    except Exception:
        cafe_cap_v = float(CAFE_AP_FULL_CAP)
    per_h_raw = str(_get("hoard_ap_cafe_ap_per_hour", "") or "").strip()
    if per_h_raw:
        try:
            per_h_v = float(per_h_raw)
        except Exception:
            per_h_v = cafe_cap_v / 24.0
    else:
        per_h_v = cafe_cap_v / 24.0

    # 跨天检测：claimed_day_start < 今天 → 昨日已领标记当未领，重排领任务/礼包/小组
    _today_pf = (now or datetime.now()).strftime("%Y-%m-%d")
    _claimed_day = str(_get("hoard_ap_claimed_day_start", "") or "")
    _crossed = bool(_claimed_day) and _claimed_day < _today_pf

    cfg = HoardConfig(
        enabled=_as_bool(_get("hoard_ap_enabled", False)),
        target_date=str(_get("hoard_ap_target_date", "") or ""),
        spend_time=str(_get("hoard_ap_spend_time", "18:30") or "18:30"),
        tubes=tubes_val,
        tube_days=tube_days_val,
        auto_tubes=auto_tubes,
        strategy=str(_get("hoard_ap_strategy", STRATEGY_SIMPLE_PLUS)),
        clear_mode=str(_get("hoard_ap_clear_mode", CLEAR_MODE_ACTIVITY)),
        clear_modes=str(_get("hoard_ap_clear_modes", "") or ""),
        use_ap_card=_as_bool(_get("hoard_ap_use_ap_card", False)),
        ap_card_amount=_parse_card_amount(_get("hoard_ap_card_amount", "0")),
        cafe_ap_per_hour=per_h_v,
        cafe_ap_full_cap=cafe_cap_v,
        cafe_claimable_manual=manual_val,
        cafe_hours_since_claim=float(_get("hoard_ap_cafe_hours_since_claim", 0) or 0),
        jjc_buy_mode=jjc_mode or JJC_BUY_30_60,
        jjc_refresh=int(jjc_refresh or 0),
        xiuxian_clear_time=str(_get("hoard_ap_xiuxian_clear_time", "02:00") or "02:00"),
        current_ap=current_ap_cfg,
        existing_mail_ap=int(mail_ap_cfg),
        task_claimed=_as_bool(_get("hoard_ap_task_claimed", False)) and not _crossed,
        lesson_claimed=_lesson_claimed_from_config(_get) and not _crossed,
        lesson_ready=(not _lesson_claimed_from_config(_get)) or _crossed,
        jjc_claimed=_as_bool(_get("hoard_ap_jjc_claimed", False)) and not _crossed,
        group_claimed=_as_bool(_get("hoard_ap_group_claimed", False)) and not _crossed,
        free_buy_claimed=_as_bool(_get("hoard_ap_free_buy_claimed", False)) and not _crossed,
        hard_cap=int(hard_cap),
        natural_soft_cap=int(soft_cap),
        hold_cafe_until_spend=True,
        activity_sweep_task_number=str(_get("activity_sweep_task_number", "1") or "1"),
        activity_sweep_times=str(_get("activity_sweep_times", "0") or "0"),
        special_task_times=str(_get("special_task_times", "0,0") or "0,0"),
        scrimmage_times=str(_get("scrimmage_times", "0,0,0") or "0,0,0"),
        mainline_priority=str(_get("mainlinePriority", "") or _get("mainline_priority", "") or ""),
        hard_priority=str(_get("hardPriority", "") or _get("hard_priority", "") or ""),
        mail_bags=_parse_mail_bags_cfg(_get),
    )

    current_ap = int(current_ap_cfg) if current_ap_cfg is not None else 0
    if current_ap_cfg is None:
        ap_info = _get("ap", {}) or {}
        if isinstance(ap_info, dict):
            try:
                current_ap = int(ap_info.get("count") or 0)
            except (TypeError, ValueError):
                current_ap = 0
    if current_ap < 0:
        current_ap = 0
    return build_plan(cfg, now=now, current_ap=current_ap)


def _infer_jjc_from_shop(config_obj: Any) -> Tuple[str, int]:
    """从 TacticalChallengeShopList / RefreshTime 推断买 30/60 与刷新。"""

    def _get(key: str, default: Any = None) -> Any:
        if isinstance(config_obj, dict):
            return config_obj.get(key, default)
        return getattr(config_obj, key, default)

    refresh = 0
    try:
        refresh = int(_get("TacticalChallengeShopRefreshTime", 0) or 0)
    except (TypeError, ValueError):
        refresh = 0
    refresh = max(0, min(3, refresh))

    goods = _get("TacticalChallengeShopList", None)
    if not goods:
        return JJC_BUY_30_60, refresh

    # 找 30AP/60AP 下标：优先 static 价目名，否则 CN 常用 6/7
    idx_30, idx_60 = 6, 7
    try:
        static = _get("static_config", None) or getattr(config_obj, "static_config", None)
        server = _get("server_mode", None) or getattr(config_obj, "server_mode", "CN")
        price_list = None
        if static is not None:
            price_list = getattr(static, "tactical_challenge_shop_price_list", None)
            if isinstance(price_list, dict):
                price_list = price_list.get(server) or price_list.get("CN")
        if price_list:
            for i, row in enumerate(price_list):
                name = str(row[0]) if row else ""
                if name.replace(" ", "") in ("30AP", "30ap", "30体力"):
                    idx_30 = i
                if name.replace(" ", "") in ("60AP", "60ap", "60体力"):
                    idx_60 = i
    except Exception:
        pass

    try:
        buy_30 = int(goods[idx_30]) == 1 if idx_30 < len(goods) else False
        buy_60 = int(goods[idx_60]) == 1 if idx_60 < len(goods) else False
    except Exception:
        buy_30, buy_60 = False, False

    if buy_30 and buy_60:
        return JJC_BUY_30_60, refresh
    if buy_30:
        return JJC_BUY_30, refresh
    if buy_60:
        # 只买 60 也按 30_60 里仅 60——简化为 30_60 但计算用 60 only
        return JJC_BUY_30_60, refresh  # 实际 jjc_ap 仍按 list；此处 fallback
    return JJC_BUY_NONE, refresh


def apply_jjc_to_shop_config(config_obj: Any, buy_mode: str, refresh: int) -> None:
    """把囤体页的 JJC 选择写回战术竞赛商店配置。"""

    def _get(key: str, default: Any = None) -> Any:
        if isinstance(config_obj, dict):
            return config_obj.get(key, default)
        if hasattr(config_obj, "get"):
            try:
                return config_obj.get(key, default)
            except TypeError:
                return getattr(config_obj, key, default)
        return getattr(config_obj, key, default)

    def _set(key: str, value: Any) -> None:
        if isinstance(config_obj, dict):
            config_obj[key] = value
            return
        if hasattr(config_obj, "set"):
            config_obj.set(key, value)
            return
        if hasattr(config_obj, "update"):
            try:
                config_obj.update(key, value)
                return
            except TypeError:
                pass
        setattr(config_obj, key, value)

    refresh = max(0, min(3, int(refresh or 0)))
    # BAAS 商店内部用 int 比较刷新次数，不能写字符串
    _set("TacticalChallengeShopRefreshTime", int(refresh))

    raw_goods = list(_get("TacticalChallengeShopList") or [])
    goods = []
    for x in raw_goods:
        try:
            goods.append(int(x))
        except Exception:
            try:
                goods.append(1 if str(x).lower() in ("1", "true", "yes") else 0)
            except Exception:
                goods.append(0)
    if not goods:
        goods = [0] * 16
    while len(goods) < 16:
        goods.append(0)

    idx_30, idx_60 = 6, 7
    try:
        static = getattr(config_obj, "static_config", None)
        server = getattr(config_obj, "server_mode", "CN")
        if static is not None:
            pl = getattr(static, "tactical_challenge_shop_price_list", None)
            if isinstance(pl, dict):
                rows = pl.get(server) or pl.get("CN") or []
                for i, row in enumerate(rows):
                    name = str(row[0]).replace(" ", "")
                    if name.upper() == "30AP":
                        idx_30 = i
                    if name.upper() == "60AP":
                        idx_60 = i
    except Exception:
        pass

    # 只改体力格，不动其它勾选
    if buy_mode == JJC_BUY_NONE:
        goods[int(idx_30)] = 0
        goods[int(idx_60)] = 0
    elif buy_mode == JJC_BUY_30:
        goods[int(idx_30)] = 1
        goods[int(idx_60)] = 0
    else:  # 30_60 — 若动态只要 60，由调用方 mode 区分；默认两格都开
        # 动态 plan 可能只要 60：看 buy_mode 字符串不够，兼容 meta 时由 executor 再写
        goods[int(idx_30)] = 1
        goods[int(idx_60)] = 1
    # 全部转为 int，避免商店里 int < str 崩
    goods = [int(x) for x in goods]
    _set("TacticalChallengeShopList", goods)
