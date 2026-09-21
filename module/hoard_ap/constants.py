"""囤体数值常量。

硬约束：
1. 角色栏硬顶 999；买管 / 免费买体永不进邮箱，购买瞬间 ap+gain 必须 <= 999。
2. 可囤来源在 ap 满时领取 → 溢出进邮，从进邮时刻起约 24h；邮内不可再囤。
3. 自然回复只回满软顶（默认 160），绝不会因自然回复进邮。
4. 国服日替 04:00。
5. 1 管 = 120；1-3 管 30 钻/管，4-6 管 60 钻/管。
6. 每日任务体力固定 150 = 登录任务 100 + 日程任务 50；小组 10。
7. JJC 店：每轮可买 30 与/或 60，刷新 0–3 次 → 面额 = 单轮合计 × (刷新+1)。
8. 囤体启用且处于活跃相位时：下列调度任务全部由囤体接管，原入口不得再执行。
"""

from __future__ import annotations

# --- caps / regen ---
AP_HARD_CAP = 999
AP_SOFT_NATURAL_CAP = 160
AP_PER_HOUR = 10
AP_PER_SECOND = AP_PER_HOUR / 3600.0

# --- server day boundary (CN) ---
SERVER_DAY_RESET_HOUR = 4  # 04:00 local game day switch

# --- mail ---
MAIL_TTL_SECONDS = 24 * 3600
MAIL_HANDLE_MARGIN_SECONDS = 10 * 60  # process ~10 min before expire
MAIL_PAD_SUCCESS_MIN = 990
MAIL_PAD_SUCCESS_MAX = 999

# --- direct (never mail) ---
TUBE_AP = 120
TUBE_PRICE_TIER1 = 30  # tubes 1..3
TUBE_PRICE_TIER2 = 60  # tubes 4..6
FREE_BUY_AP = 10

# --- fixed daily sources ---
GROUP_AP = 10
TASK_LOGIN_AP = 100  # 任务里登录即可领
TASK_LESSON_AP = 50  # 需先做/领日程
TASK_AP = TASK_LOGIN_AP + TASK_LESSON_AP  # 150
JJC_AP_30 = 30
JJC_AP_60 = 60
# 兼容旧字段默认（3 刷 × (30+60) = 360）
JJC_SHOP_AP = 360

CAFE_AP_PER_HOUR = 30.8
CAFE_AP_FULL_CAP = 740

# JJC buy modes
JJC_BUY_NONE = "none"
JJC_BUY_30 = "30"
JJC_BUY_30_60 = "30_60"

# --- phases ---
PHASE_IDLE = "Idle"
PHASE_ARMED = "Armed"
PHASE_PRE_OVERFLOW = "PhasePreOverflow"
PHASE_STACK = "PhaseStack"
PHASE_HOLD = "PhaseHold"
PHASE_CLEAR = "PhaseClear"
PHASE_SPEND_READY = "PhaseSpendReady"
PHASE_DONE = "Done"
PHASE_ABORTED = "Aborted"

# ---------------------------------------------------------------------------
# 调度接管表
# 囤体启用 + 活跃相位时，这些 func_name 一律从 valid_task_queue 剔除；
# 只允许 hoard_ap 自己在计划时间点内调用对应实现。
# 咖啡厅：整包 cafe_reward 会被压制领奖部分（见 cafe_guard / should_skip_cafe_collect）；
# no1/no2 邀请默认放行（与体力无关），若用户要求也可一并压制。
# ---------------------------------------------------------------------------
HOARD_OWNED_FUNCS = frozenset(
    {
        # 体力领取类
        "mail",
        "collect_daily_power",
        "collect_daily_free_power",
        "group",
        "tactical_challenge_shop",
        "purchase_ap",
        # 清体 / 扫荡类（囤体计划外禁止自行花体）
        "normal_task",
        "hard_task",
        "activity_sweep",
        "clear_special_task_power",
        "scrimmage",
        # 悬赏通缉(rewarded_task)不耗体力 → 不接管，原调度照跑
        # 其它可能误领体力/奖励的
        "collect_reward",
        # 注意：cafe_reward 不进本表。
        # 队列层放行，让邀请/摸头仍可跑；小时领奖由 cafe_reward 内 guard + should_skip_cafe_collect 拦截。
        # no1_cafe_invite / no2_cafe_invite 与体力无关，始终放行。
        # restart（凌晨四点重启）绝不进本表——日界重启是铁律，囤体不得压制。
    }
)

# 花体窗口已到点后仍压制的「禁止自动花体」集合（领源可放，清体扫荡仍压）
HOARD_SPEND_BLOCK_FUNCS = frozenset(
    {
        "normal_task",
        "hard_task",
        "activity_sweep",
        "clear_special_task_power",
        "scrimmage",
        "purchase_ap",
    }
)

# 主页/囤体「优先清体」：勾选后拦截其它耗体扫荡（可在未开囤体时单独生效）
# 值："" | normal | hard | special | high_value
# 兼容旧值 mainline（= normal+hard 都放行，读侧会归一）
PREFER_CLEAR_NONE = ""
PREFER_CLEAR_NORMAL = "normal"
PREFER_CLEAR_HARD = "hard"
PREFER_CLEAR_MAINLINE = "mainline"  # 旧兼容
PREFER_CLEAR_SPECIAL = "special"
PREFER_CLEAR_HIGH_VALUE = "high_value"

PREFER_CLEAR_ALLOW = {
    # 普通多倍：只放行普通扫荡，拦困难等
    PREFER_CLEAR_NORMAL: frozenset({"normal_task"}),
    # 困难多倍：只放行困难扫荡，拦普通等
    PREFER_CLEAR_HARD: frozenset({"hard_task"}),
    # 旧 mainline：普通+困难都放行（兼容老配置）
    PREFER_CLEAR_MAINLINE: frozenset({"normal_task", "hard_task"}),
    PREFER_CLEAR_SPECIAL: frozenset({"clear_special_task_power"}),
    PREFER_CLEAR_HIGH_VALUE: frozenset({"activity_sweep"}),
}

# 仅用于「是否跳过咖啡领奖」判断（不剔除整个 cafe_reward 事件）
HOARD_CAFE_COLLECT_FUNC = "cafe_reward"

# 活跃相位集合（启用囤体且相位在此内 → 压制 HOARD_OWNED_FUNCS）
HOARD_ACTIVE_PHASES = frozenset(
    {
        PHASE_ARMED,
        PHASE_PRE_OVERFLOW,
        PHASE_STACK,
        PHASE_HOLD,
        PHASE_CLEAR,
        PHASE_SPEND_READY,
    }
)

# 兼容旧 CONFLICT_TABLE：任意活跃相位都压（比旧「按相位细分」更狠，符合「囤体优先」）
CONFLICT_TABLE = {name: set(HOARD_ACTIVE_PHASES) for name in HOARD_OWNED_FUNCS}

# Actions the executor understands.
ACTION_WAIT = "wait"
ACTION_NOTIFY = "notify"
ACTION_BUY_TUBES = "buy_tubes"
ACTION_FREE_BUY = "free_buy"
ACTION_CLAIM_TASK = "claim_task"
ACTION_CLAIM_GROUP = "claim_group"
ACTION_CLAIM_JJC = "claim_jjc"
ACTION_CLAIM_CAFE = "claim_cafe"
ACTION_USE_AP_CARD = "use_ap_card"
ACTION_CLEAR_AP = "clear_ap"
ACTION_ENSURE_HEADROOM = "ensure_headroom"
ACTION_HOLD = "hold"
ACTION_SPEND_READY = "spend_ready"
ACTION_CLAIM_MAIL = "claim_mail"
ACTION_RECORD_OVERFLOW = "record_overflow"
ACTION_CLAIM_TASK_DAILY_ONLY = "claim_task_daily_only"

# Clear modes (user config)
CLEAR_MODE_ACTIVITY = "activity"
CLEAR_MODE_MAINLINE = "mainline"
CLEAR_MODE_NOTIFY_ONLY = "notify_only"
CLEAR_MODE_SPECIAL = "special"
CLEAR_MODE_SCRIMMAGE = "scrimmage"

# Strategy templates（内部；UI 不再让人选，由买管数推导勤奋/懒人）
STRATEGY_SIMPLE = "simple"  # 懒人：到 999 后不二度买管挖自然回
STRATEGY_SIMPLE_PLUS = "simple_plus"
STRATEGY_XIUXIAN = "xiuxian"  # 勤奋：买管>0，可清到 0 再叠邮
