"""邮箱垫满算法：快过期邮 = 免费垫到 990–999 的资源。

规则：
- 领邮不能超过 hard_cap（999）
- 优先剩余时间短的包
- 角色已接近满时：只清出「够领下一包」的空位，不无脑扫到 0
- 产出逐步手顺（OCR 失败时给人看）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class MailBag:
    amount: int
    overflow_at: datetime
    expire_at: Optional[datetime] = None
    source: str = ""
    remaining_minutes: Optional[int] = None  # OCR；None=用 expire 推算

    def __post_init__(self) -> None:
        if self.expire_at is None:
            self.expire_at = self.overflow_at + timedelta(hours=24)

    def seconds_left(self, now: datetime) -> float:
        if self.remaining_minutes is not None:
            return max(0.0, float(self.remaining_minutes) * 60.0)
        assert self.expire_at is not None
        return max(0.0, (self.expire_at - now).total_seconds())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": int(self.amount),
            "overflow_at": self.overflow_at.isoformat(sep=" ", timespec="minutes"),
            "expire_at": self.expire_at.isoformat(sep=" ", timespec="minutes")
            if self.expire_at
            else None,
            "source": self.source,
            "remaining_minutes": self.remaining_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MailBag":
        def _p(s: Any) -> datetime:
            if isinstance(s, datetime):
                return s
            s = str(s or "").replace("T", " ")
            for n in (16, 19):
                try:
                    return datetime.strptime(s[:n], "%Y-%m-%d %H:%M" if n == 16 else "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            return datetime.now()

        ov = _p(data.get("overflow_at"))
        ex = data.get("expire_at")
        return cls(
            amount=int(data.get("amount") or 0),
            overflow_at=ov,
            expire_at=_p(ex) if ex else ov + timedelta(hours=24),
            source=str(data.get("source") or ""),
            remaining_minutes=(
                int(data["remaining_minutes"])
                if data.get("remaining_minutes") is not None
                else None
            ),
        )


@dataclass
class PadStep:
    """一步：花多少 / 领哪包 / 领后预估体力。"""

    action: str  # clear | claim_mail | done | manual_hint
    clear_amount: int = 0
    claim_amount: int = 0
    bag_index: int = -1
    bag_amount: int = 0
    expect_ap_after: int = 0
    expect_mail_after: int = 0
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "clear_amount": self.clear_amount,
            "claim_amount": self.claim_amount,
            "bag_index": self.bag_index,
            "bag_amount": self.bag_amount,
            "expect_ap_after": self.expect_ap_after,
            "expect_mail_after": self.expect_mail_after,
            "note": self.note,
        }


@dataclass
class PadPlan:
    start_ap: int
    hard_cap: int
    success_lo: int  # 990
    steps: List[PadStep] = field(default_factory=list)
    final_ap: int = 0
    final_mail: int = 0
    bags_after: List[MailBag] = field(default_factory=list)
    manual_script: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_ap": self.start_ap,
            "hard_cap": self.hard_cap,
            "success_lo": self.success_lo,
            "steps": [s.to_dict() for s in self.steps],
            "final_ap": self.final_ap,
            "final_mail": self.final_mail,
            "bags_after": [b.to_dict() for b in self.bags_after],
            "manual_script": self.manual_script,
        }


def sort_bags(bags: Sequence[MailBag], now: datetime) -> List[Tuple[int, MailBag]]:
    """返回 (原下标, bag)，按剩余时间升序；同剩余则大包优先（一次垫更多）。"""
    indexed = list(enumerate(bags))
    indexed.sort(key=lambda it: (it[1].seconds_left(now), -it[1].amount))
    return indexed


def build_pad_plan(
    current_ap: int,
    bags: Sequence[MailBag],
    now: Optional[datetime] = None,
    hard_cap: int = 999,
    success_lo: int = 990,
    max_rounds: int = 12,
) -> PadPlan:
    """生成「花一点空位 → 领最快过期邮 → 直到快过期处理完或垫到 success_lo+」的步骤。"""
    now = now or datetime.now().replace(second=0, microsecond=0)
    hard_cap = int(hard_cap)
    success_lo = int(success_lo)
    ap = max(0, min(int(current_ap), hard_cap))
    # 可变副本
    work: List[MailBag] = [
        MailBag(
            amount=int(b.amount),
            overflow_at=b.overflow_at,
            expire_at=b.expire_at,
            source=b.source,
            remaining_minutes=b.remaining_minutes,
        )
        for b in bags
        if int(b.amount) > 0
    ]
    plan = PadPlan(start_ap=ap, hard_cap=hard_cap, success_lo=success_lo)
    # 「快过期」：24h 内会过期的都算（台账内邮体）
    # 实际执行时会再按 remaining_minutes 收紧

    for _ in range(max_rounds):
        if not work:
            break
        ordered = sort_bags(work, now)
        # 只处理仍有剩余时间的
        ordered = [(i, b) for i, b in ordered if b.seconds_left(now) > 0 and b.amount > 0]
        if not ordered:
            break

        room = hard_cap - ap
        next_i, next_b = ordered[0]

        if room <= 0:
            # 满了：只清出够领「下一整包或 room 目标」的空位
            # 目标：领完后尽量到 hard_cap，所以至少清 next 包能进来的量
            need_room = min(next_b.amount, hard_cap)  # 想整包领就清 amount
            # 但若包很大，至少清到能继续垫（清 need_room）
            clear_amt = need_room
            if clear_amt > ap:
                clear_amt = ap
            if clear_amt <= 0:
                break
            ap -= clear_amt
            plan.steps.append(
                PadStep(
                    action="clear",
                    clear_amount=clear_amt,
                    expect_ap_after=ap,
                    expect_mail_after=sum(x.amount for x in work),
                    note=f"花掉 {clear_amt} 点空出栏位，准备领最快过期邮包 +{next_b.amount}",
                )
            )
            room = hard_cap - ap

        # 从最快过期包领 min(room, bag)
        claim = min(room, next_b.amount)
        if claim <= 0:
            break
        # 更新包
        # find bag in work by identity - use ordered index into work carefully
        # rebuild: match by expire+amount+source first occurrence
        target = None
        for b in work:
            if (
                b.amount == next_b.amount
                and b.overflow_at == next_b.overflow_at
                and b.source == next_b.source
            ):
                target = b
                break
        if target is None:
            target = work[0]
        target.amount -= claim
        if target.amount <= 0:
            work = [b for b in work if b is not target]
        ap += claim
        plan.steps.append(
            PadStep(
                action="claim_mail",
                claim_amount=claim,
                bag_amount=claim + max(0, target.amount),
                expect_ap_after=ap,
                expect_mail_after=sum(x.amount for x in work),
                note=(
                    f"领邮箱 +{claim}"
                    + (f"（来源 {target.source}）" if target.source else "")
                    + f" → 体约 {ap}（目标 {success_lo}–{hard_cap}）"
                ),
            )
        )

        if success_lo <= ap <= hard_cap and not any(
            b.seconds_left(now) < 6 * 3600 for b in work
        ):
            # 已在成功带且无 6h 内急邮
            break
        if success_lo <= ap <= hard_cap and not work:
            break

    plan.final_ap = ap
    plan.final_mail = sum(b.amount for b in work)
    plan.bags_after = work
    plan.manual_script = render_manual_script(plan, now)
    if success_lo <= ap <= hard_cap:
        plan.steps.append(
            PadStep(
                action="done",
                expect_ap_after=ap,
                expect_mail_after=plan.final_mail,
                note=f"垫档完成：体约 {ap}（{success_lo}–{hard_cap} 算成功）",
            )
        )
    else:
        plan.steps.append(
            PadStep(
                action="manual_hint",
                expect_ap_after=ap,
                expect_mail_after=plan.final_mail,
                note=f"自动步骤后体约 {ap}，未进入 {success_lo}–{hard_cap}；见手顺或补扫/补邮",
            )
        )
    return plan


def render_manual_script(plan: PadPlan, now: datetime) -> str:
    """OCR 失败时给人看的逐步手顺。"""
    lines = [
        "【邮箱垫满手顺】（OCR 失败时按此手动；领完看体力是否在 990–999）",
        f"起始体力约 {plan.start_ap}，硬顶 {plan.hard_cap}",
        "",
    ]
    n = 0
    for s in plan.steps:
        if s.action == "clear":
            n += 1
            lines.append(
                f"{n}. 扫荡花掉约 {s.clear_amount} 点 → 体约 {s.expect_ap_after}"
            )
        elif s.action == "claim_mail":
            n += 1
            lines.append(
                f"{n}. 邮箱里按「剩余时间最短」优先，领取约 {s.claim_amount} 点"
                f" → 体约 {s.expect_ap_after}（邮箱约剩 {s.expect_mail_after}）"
            )
        elif s.action == "done":
            lines.append(f"完成：体约 {s.expect_ap_after}")
        elif s.action == "manual_hint":
            lines.append(f"注意：{s.note}")
    lines.append("")
    lines.append("校验：领取后当前体力在 990–999 即成功；差太多就停手改手动。")
    return "\n".join(lines)


def bags_from_total_estimate(
    total: int,
    now: datetime,
    chunk: int = 90,
) -> List[MailBag]:
    """只有总量没有分包时：拆成 chunk 近似包，过期按 now+24h（偏保守同刻）。"""
    total = max(0, int(total))
    if total <= 0:
        return []
    bags: List[MailBag] = []
    left = total
    # 第一包可以是 remainder，便于多样
    while left > 0:
        amt = min(chunk, left)
        bags.append(
            MailBag(
                amount=amt,
                overflow_at=now,
                expire_at=now + timedelta(hours=24),
                source="estimate",
            )
        )
        left -= amt
    return bags
