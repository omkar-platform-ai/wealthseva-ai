"""
IDBI Sandbox API wrapper — will be wired to real APIs after shortlisting (July 22).
Uses mock data for initial submission (July 9).

All mock data describes ONE coherent demo customer:
Ramesh, 42, Mumbai, salaried (₹80,000/month), moderate risk profile,
₹5.1L invested of which ₹2.4L sits idle in a liquid fund (his emergency corpus).
Keep frontend demo surfaces (demo page, dashboard) consistent with these numbers.
"""
import os
from fastapi import APIRouter
import httpx
from models.schemas import IDBIPortfolioResponse, IDBIRiskProfileResponse, IDBIGoalsResponse

router = APIRouter()

IDBI_BASE_URL = os.getenv("IDBI_SANDBOX_BASE_URL", "")
IDBI_API_KEY = os.getenv("IDBI_SANDBOX_API_KEY", "")

MOCK_TRANSACTIONS = [
    {"category": "Food & Dining", "amount": 8500, "month": "June 2026"},
    {"category": "Transport", "amount": 3200, "month": "June 2026"},
    {"category": "Shopping", "amount": 12000, "month": "June 2026"},
    {"category": "Utilities", "amount": 4500, "month": "June 2026"},
]

# Total ₹5,09,620 — the liquid fund (₹2.4L, ~47%) is Ramesh's idle-cash story
MOCK_PORTFOLIO = [
    {
        "isin": "INF179K01UT0",
        "name": "HDFC Flexi Cap Fund",
        "category": "Flexi Cap Equity",
        "units": 60.0,
        "nav": 1904.00,
        "current_value": 114240.00,
        "gain_loss_pct": 12.4,
    },
    {
        "isin": "INF200K01RO2",
        "name": "SBI Blue Chip Fund",
        "category": "Large Cap Equity",
        "units": 703.18,
        "nav": 88.00,
        "current_value": 61879.84,
        "gain_loss_pct": 8.2,
    },
    {
        "isin": "INF179K01BC4",
        "name": "HDFC Short Term Debt Fund",
        "category": "Short Duration Debt",
        "units": 2854.24,
        "nav": 29.50,
        "current_value": 84200.08,
        "gain_loss_pct": 4.1,
    },
    {
        "isin": "INF200KA1FS1",
        "name": "SBI Gold ETF",
        "category": "Gold ETF",
        "units": 150.0,
        "nav": 62.00,
        "current_value": 9300.00,
        "gain_loss_pct": 6.3,
    },
    {
        "isin": "INF277K01ZL1",
        "name": "ICICI Pru Liquid Fund",
        "category": "Liquid",
        "units": 640.0,
        "nav": 375.00,
        "current_value": 240000.00,
        "gain_loss_pct": 6.9,
    },
]

MOCK_RISK_PROFILE = {
    "profile": "moderate",
    "score": 58,
    "age": 42,
    "investment_horizon_years": 20,
    "risk_capacity": "medium",
    "recommended_allocation": {
        "equity": 60,
        "debt": 30,
        "gold": 10,
    },
    "explanation": (
        "Based on your age (42), stable income, and 20-year horizon to retirement, a Moderate risk profile "
        "balances growth through equity exposure with downside protection via debt instruments."
    ),
}

# Monthly SIPs total ₹16,000 — 20% of Ramesh's ₹80,000 income
MOCK_GOALS = [
    {
        "id": "goal-001",
        "name": "Retirement Corpus",
        "target_amount": 5000000.0,
        "target_date": "2046-07-01",
        "current_savings": 0.0,
        "monthly_sip": 5000.0,
        "progress_pct": 0.0,
    },
    {
        "id": "goal-002",
        "name": "Child Education",
        "target_amount": 2500000.0,
        "target_date": "2038-06-01",
        "current_savings": 80000.0,
        "monthly_sip": 6000.0,
        "progress_pct": 3.2,
    },
    {
        "id": "goal-003",
        "name": "Emergency Fund",
        "target_amount": 480000.0,
        "target_date": "2027-03-31",
        "current_savings": 240000.0,
        "monthly_sip": 5000.0,
        "progress_pct": 50.0,
    },
]


async def _live_get(path: str, mock_data):
    """GET from the IDBI sandbox; fall back to mock data on any failure — never 500."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{IDBI_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {IDBI_API_KEY}"},
            )
            response.raise_for_status()
            return {"data": response.json(), "source": "live"}
    except Exception:
        return {"data": mock_data, "source": "mock"}


@router.get("/idbi/transactions")
async def get_transactions(account_id: str = "demo"):
    """Fetch transaction data. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_TRANSACTIONS, "source": "mock"}
    return await _live_get(f"/accounts/{account_id}/transactions", MOCK_TRANSACTIONS)


@router.get("/idbi/portfolio", response_model=IDBIPortfolioResponse)
async def get_portfolio(account_id: str = "demo"):
    """Fetch portfolio holdings. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_PORTFOLIO, "source": "mock"}
    return await _live_get(f"/accounts/{account_id}/portfolio", MOCK_PORTFOLIO)


@router.get("/idbi/risk", response_model=IDBIRiskProfileResponse)
async def get_risk_profile(account_id: str = "demo"):
    """Fetch risk profile. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_RISK_PROFILE, "source": "mock"}
    return await _live_get(f"/accounts/{account_id}/risk", MOCK_RISK_PROFILE)


@router.get("/idbi/goals", response_model=IDBIGoalsResponse)
async def get_goals(account_id: str = "demo"):
    """Fetch financial goals. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_GOALS, "source": "mock"}
    return await _live_get(f"/accounts/{account_id}/goals", MOCK_GOALS)
