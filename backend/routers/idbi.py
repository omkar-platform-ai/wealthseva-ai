"""
IDBI Sandbox API wrapper — will be wired to real APIs after shortlisting (July 22).
Uses mock data for initial submission (July 9).
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

MOCK_PORTFOLIO = [
    {
        "isin": "INF209K01YQ5",
        "name": "Aditya Birla SL Frontline Equity Fund",
        "category": "Large Cap Equity",
        "units": 245.678,
        "nav": 412.35,
        "current_value": 101284.48,
        "gain_loss_pct": 18.4,
    },
    {
        "isin": "INF174K01LS2",
        "name": "HDFC Mid-Cap Opportunities Fund",
        "category": "Mid Cap Equity",
        "units": 312.45,
        "nav": 198.72,
        "current_value": 62094.54,
        "gain_loss_pct": 24.1,
    },
    {
        "isin": "INF200K01RO2",
        "name": "SBI Blue Chip Fund",
        "category": "Large Cap Equity",
        "units": 189.23,
        "nav": 87.45,
        "current_value": 16549.64,
        "gain_loss_pct": 11.2,
    },
    {
        "isin": "INF846K01DP8",
        "name": "Axis Long Term Equity Fund",
        "category": "ELSS",
        "units": 523.10,
        "nav": 74.18,
        "current_value": 38801.80,
        "gain_loss_pct": 9.8,
    },
    {
        "isin": "INF277K01ZL1",
        "name": "ICICI Pru Liquid Fund",
        "category": "Liquid",
        "units": 1024.50,
        "nav": 341.22,
        "current_value": 349500.09,
        "gain_loss_pct": 6.9,
    },
]

MOCK_RISK_PROFILE = {
    "profile": "moderate",
    "score": 58,
    "age": 32,
    "investment_horizon_years": 15,
    "risk_capacity": "medium",
    "recommended_allocation": {
        "equity": 60,
        "debt": 30,
        "gold": 5,
        "cash": 5,
    },
    "explanation": (
        "Based on your age (32), stable income, and 15-year horizon, a Moderate risk profile "
        "balances growth through equity exposure with downside protection via debt instruments."
    ),
}

MOCK_GOALS = [
    {
        "id": "goal-001",
        "name": "Home Purchase",
        "target_amount": 5000000.0,
        "target_date": "2031-12-31",
        "current_savings": 850000.0,
        "monthly_sip": 28000.0,
        "progress_pct": 17.0,
    },
    {
        "id": "goal-002",
        "name": "Child Education",
        "target_amount": 2500000.0,
        "target_date": "2036-06-01",
        "current_savings": 320000.0,
        "monthly_sip": 12000.0,
        "progress_pct": 12.8,
    },
    {
        "id": "goal-003",
        "name": "Retirement Corpus",
        "target_amount": 30000000.0,
        "target_date": "2054-01-01",
        "current_savings": 1200000.0,
        "monthly_sip": 25000.0,
        "progress_pct": 4.0,
    },
    {
        "id": "goal-004",
        "name": "Emergency Fund",
        "target_amount": 600000.0,
        "target_date": "2027-03-31",
        "current_savings": 420000.0,
        "monthly_sip": 15000.0,
        "progress_pct": 70.0,
    },
]


@router.get("/idbi/transactions")
async def get_transactions(account_id: str = "demo"):
    """Fetch transaction data. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_TRANSACTIONS, "source": "mock"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{IDBI_BASE_URL}/accounts/{account_id}/transactions",
            headers={"Authorization": f"Bearer {IDBI_API_KEY}"},
        )
        return {"data": response.json(), "source": "live"}


@router.get("/idbi/portfolio", response_model=IDBIPortfolioResponse)
async def get_portfolio(account_id: str = "demo"):
    """Fetch portfolio holdings. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_PORTFOLIO, "source": "mock"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{IDBI_BASE_URL}/accounts/{account_id}/portfolio",
            headers={"Authorization": f"Bearer {IDBI_API_KEY}"},
        )
        return {"data": response.json(), "source": "live"}


@router.get("/idbi/risk", response_model=IDBIRiskProfileResponse)
async def get_risk_profile(account_id: str = "demo"):
    """Fetch risk profile. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_RISK_PROFILE, "source": "mock"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{IDBI_BASE_URL}/accounts/{account_id}/risk",
            headers={"Authorization": f"Bearer {IDBI_API_KEY}"},
        )
        return {"data": response.json(), "source": "live"}


@router.get("/idbi/goals", response_model=IDBIGoalsResponse)
async def get_goals(account_id: str = "demo"):
    """Fetch financial goals. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"data": MOCK_GOALS, "source": "mock"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{IDBI_BASE_URL}/accounts/{account_id}/goals",
            headers={"Authorization": f"Bearer {IDBI_API_KEY}"},
        )
        return {"data": response.json(), "source": "live"}
