"""囤体 (AP hoarding) package.

Public entry points used by BAAS scheduler / GUI:
- planner: pure schedule calculator
- executor.implement: scheduler task `hoard_ap`
- state: runtime phase + mail ledger helpers
"""

from module.hoard_ap.planner import (
    HoardConfig,
    HoardPlan,
    PlanStep,
    build_plan,
    tube_cost_pyroxene,
    tube_gain_ap,
)
from module.hoard_ap.constants import (
    AP_HARD_CAP,
    AP_PER_HOUR,
    FREE_BUY_AP,
    GROUP_AP,
    JJC_SHOP_AP,
    MAIL_TTL_SECONDS,
    SERVER_DAY_RESET_HOUR,
    TASK_AP,
    TUBE_AP,
)

__all__ = [
    "AP_HARD_CAP",
    "AP_PER_HOUR",
    "FREE_BUY_AP",
    "GROUP_AP",
    "JJC_SHOP_AP",
    "MAIL_TTL_SECONDS",
    "SERVER_DAY_RESET_HOUR",
    "TASK_AP",
    "TUBE_AP",
    "HoardConfig",
    "HoardPlan",
    "PlanStep",
    "build_plan",
    "tube_cost_pyroxene",
    "tube_gain_ap",
]
from module.hoard_ap import narrative  # noqa: F401
