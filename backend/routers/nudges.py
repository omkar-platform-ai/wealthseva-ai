"""
Money Moments nudge engine — deterministic rules over IDBI sandbox data.
No LLM is involved; every figure is arithmetic-only (coherent with RiskTrace/GoalTrace).
"""
import asyncio
from datetime import date
from typing import Optional
from fastapi import APIRouter
from models.schemas import Nudge, NudgeType, NudgeWhyTrace, NudgesResponse
from routers.idbi import get_portfolio, get_goals

router = APIRouter()

_MONTHLY_RATE = 0.01          # 12% p.a. assumed for equity/diversified funds
_EMERGENCY_MONTHS = 6
_MONTHLY_EXPENSES = 28_200    # derived from MOCK_TRANSACTIONS in idbi.py
_SIP_DRIFT_FLOOR = 12         # months — skip goals too close to adjust via SIP
_SIP_SHORTFALL_PCT = 0.10     # 10% below required → fire nudge


def _fv_factor(months: int) -> float:
    r = _MONTHLY_RATE
    return ((1 + r) ** months - 1) / r


def _fv_lump(amount: float, months: int) -> float:
    return amount * (1 + _MONTHLY_RATE) ** months


def _months_remaining(target_date_str: str) -> int:
    target = date.fromisoformat(target_date_str)
    today = date.today()
    return max(0, (target.year - today.year) * 12 + (target.month - today.month))


def _idle_cash_nudge(portfolio: list) -> Optional[Nudge]:
    liquid = next((h for h in portfolio if h.get("category") == "Liquid"), None)
    if not liquid:
        return None
    liquid_value = liquid["current_value"]
    emergency_needed = _EMERGENCY_MONTHS * _MONTHLY_EXPENSES
    excess = liquid_value - emergency_needed
    if excess <= emergency_needed * 0.30:
        return None
    liquid_return_pct = liquid.get("gain_loss_pct", 7.0)
    return Nudge(
        id="nudge-idle-cash",
        type=NudgeType.IDLE_CASH,
        title=f"₹{excess:,.0f} sitting idle above your emergency corpus",
        body=(
            f"Your liquid fund (₹{liquid_value:,.0f}) covers your "
            f"{_EMERGENCY_MONTHS}-month emergency corpus (₹{emergency_needed:,.0f}) "
            f"with ₹{excess:,.0f} to spare. That excess is earning "
            f"~{liquid_return_pct:.1f}% p.a. — it could work harder in a "
            "diversified equity or short-duration debt fund."
        ),
        severity="high",
        why_trace=NudgeWhyTrace(
            data_points=[
                f"Liquid fund ({liquid['name']}): ₹{liquid_value:,.0f}",
                f"Monthly expenses (from bank transactions): ₹{_MONTHLY_EXPENSES:,}",
                f"Emergency corpus = {_EMERGENCY_MONTHS} months × ₹{_MONTHLY_EXPENSES:,} = ₹{emergency_needed:,.0f}",
            ],
            rule=f"Liquid fund > emergency corpus × 1.3 → idle-cash nudge",
            calculation=f"₹{liquid_value:,.0f} − ₹{emergency_needed:,.0f} = ₹{excess:,.0f} excess",
        ),
        chat_seed=(
            f"I have ₹{excess:,.0f} above my emergency corpus sitting in the liquid fund. "
            "Where should I invest it to earn better returns?"
        ),
    )


def _sip_shortfall_nudges(goals: list) -> list:
    nudges = []
    for g in goals:
        months = _months_remaining(g["target_date"])
        # Skip goals too close to maturity — SIP changes won't help
        if months < _SIP_DRIFT_FLOOR:
            continue
        current = g.get("current_savings", 0.0)
        target = g["target_amount"]
        actual_sip = g.get("monthly_sip", 0.0)
        if actual_sip <= 0:
            continue
        fv_current = _fv_lump(current, months)
        remaining = target - fv_current
        if remaining <= 0:
            continue
        factor = _fv_factor(months)
        required_sip = remaining / factor
        if actual_sip >= required_sip * (1 - _SIP_SHORTFALL_PCT):
            continue
        shortfall = required_sip - actual_sip
        nudges.append(Nudge(
            id=f"nudge-sip-{g['id']}",
            type=NudgeType.SIP_SHORTFALL,
            title=f"{g['name']} SIP is ₹{shortfall:,.0f}/month below target",
            body=(
                f"To reach ₹{target:,.0f} by {g['target_date'][:7]}, you need "
                f"₹{required_sip:,.0f}/month at 12% p.a. Your current SIP is "
                f"₹{actual_sip:,.0f} — a ₹{shortfall:,.0f}/month gap that "
                f"compounds over {months} months."
            ),
            severity="medium",
            why_trace=NudgeWhyTrace(
                data_points=[
                    f"Goal: {g['name']} — target ₹{target:,.0f} by {g['target_date'][:7]}",
                    f"Current savings ₹{current:,.0f} grows to ₹{fv_current:,.0f} at 12% p.a.",
                    f"Remaining to fund via SIP: ₹{remaining:,.0f} over {months} months",
                ],
                rule=f"Required SIP > actual SIP by >{_SIP_SHORTFALL_PCT*100:.0f}% → SIP-shortfall nudge",
                calculation=(
                    f"Required: ₹{required_sip:,.0f}/month · "
                    f"Actual: ₹{actual_sip:,.0f}/month · "
                    f"Gap: ₹{shortfall:,.0f}/month"
                ),
            ),
            chat_seed=(
                f"My {g['name']} goal needs ₹{required_sip:,.0f}/month but I'm only investing "
                f"₹{actual_sip:,.0f}. How do I close the ₹{shortfall:,.0f} monthly gap?"
            ),
        ))
    return nudges


@router.get("/nudges", response_model=NudgesResponse)
async def get_nudges(account_id: str = "demo"):
    """Deterministic Money Moments nudges — no LLM, bank-data-grounded."""
    portfolio_resp, goals_resp = await asyncio.gather(
        get_portfolio(account_id),
        get_goals(account_id),
    )
    portfolio = portfolio_resp.get("data") or []
    goals = goals_resp.get("data") or []
    # Normalise: IDBIGoal Pydantic objects → dicts
    portfolio = [h if isinstance(h, dict) else h.model_dump() for h in portfolio]
    goals = [g if isinstance(g, dict) else g.model_dump() for g in goals]

    nudges: list = []
    idle = _idle_cash_nudge(portfolio)
    if idle:
        nudges.append(idle)
    nudges.extend(_sip_shortfall_nudges(goals))

    return NudgesResponse(nudges=nudges, source=portfolio_resp.get("source", "mock"))
