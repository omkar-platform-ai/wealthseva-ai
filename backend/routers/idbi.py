"""
IDBI Sandbox API wrapper — will be wired to real APIs after shortlisting (July 22).
Uses mock data for initial submission (July 9).
"""
import os
from fastapi import APIRouter
import httpx

router = APIRouter()

IDBI_BASE_URL = os.getenv("IDBI_SANDBOX_BASE_URL", "")
IDBI_API_KEY = os.getenv("IDBI_SANDBOX_API_KEY", "")

MOCK_TRANSACTIONS = [
    {"category": "Food & Dining", "amount": 8500, "month": "June 2026"},
    {"category": "Transport", "amount": 3200, "month": "June 2026"},
    {"category": "Shopping", "amount": 12000, "month": "June 2026"},
    {"category": "Utilities", "amount": 4500, "month": "June 2026"},
]


@router.get("/idbi/transactions")
async def get_transactions(account_id: str = "demo"):
    """Fetch transaction data. Uses mock data until sandbox access granted."""
    if not IDBI_BASE_URL or not IDBI_API_KEY:
        return {"transactions": MOCK_TRANSACTIONS, "source": "mock"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{IDBI_BASE_URL}/accounts/{account_id}/transactions",
            headers={"Authorization": f"Bearer {IDBI_API_KEY}"},
        )
        return response.json()
