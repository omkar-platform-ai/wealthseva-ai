"""
Account context service — fetches the customer's IDBI account snapshot
(portfolio, risk profile, goals) and formats it as compact system-prompt
context, so Shreya grounds replies in the customer's actual data
("your ₹2.4L sitting idle in the liquid fund") in any language.

Reuses the IDBI sandbox wrapper endpoints, so mock/live routing and the
Ramesh demo customer stay defined in exactly one place (routers/idbi.py).
"""
import asyncio
import logging

from routers.idbi import get_portfolio, get_risk_profile, get_goals

logger = logging.getLogger("wealthseva.account")


def _inr(value: float) -> str:
    return f"₹{value:,.0f}"


def format_account_context(portfolio: list, risk: dict, goals: list) -> str:
    """Render the account snapshot as compact plain-text prompt context."""
    lines: list[str] = []

    if portfolio:
        total = sum(h.get("current_value", 0) for h in portfolio)
        lines.append(f"Portfolio holdings (total {_inr(total)}):")
        for h in portfolio:
            lines.append(
                f"- {h.get('name')} ({h.get('category')}): {_inr(h.get('current_value', 0))}, "
                f"{h.get('gain_loss_pct', 0):+.1f}% overall"
            )

    if risk:
        alloc = risk.get("recommended_allocation") or {}
        alloc_str = ", ".join(f"{k} {v}%" for k, v in alloc.items())
        lines.append(
            f"Risk profile: {risk.get('profile')} (score {risk.get('score')}), "
            f"age {risk.get('age')}, horizon {risk.get('investment_horizon_years')} years; "
            f"recommended allocation: {alloc_str}"
        )

    if goals:
        lines.append("Financial goals:")
        for g in goals:
            lines.append(
                f"- {g.get('name')}: target {_inr(g.get('target_amount', 0))} by {g.get('target_date')}, "
                f"SIP {_inr(g.get('monthly_sip', 0))}/month, {g.get('progress_pct', 0)}% funded"
            )

    return "\n".join(lines)


async def get_account_context(account_id: str = "demo") -> str:
    """Fetch and format the account snapshot; empty string on any failure.

    Chat must never break because account data is unavailable — the reply is
    simply less personalised (same graceful-degradation contract as RAG).
    """
    try:
        pf, risk, goals = await asyncio.gather(
            get_portfolio(account_id),
            get_risk_profile(account_id),
            get_goals(account_id),
        )
        return format_account_context(
            pf.get("data") or [],
            risk.get("data") or {},
            goals.get("data") or [],
        )
    except Exception as exc:
        logger.warning("account context unavailable: %s", exc)
        return ""
