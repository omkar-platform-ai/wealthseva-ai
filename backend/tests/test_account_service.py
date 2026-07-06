"""
Tests for the account context service (customer snapshot → prompt context).
"""
import pytest
from unittest.mock import AsyncMock, patch

from routers.idbi import MOCK_PORTFOLIO, MOCK_RISK_PROFILE, MOCK_GOALS
from services.account_service import format_account_context, get_account_context


class TestFormatAccountContext:
    def test_includes_holdings_total_risk_and_goals(self):
        text = format_account_context(MOCK_PORTFOLIO, MOCK_RISK_PROFILE, MOCK_GOALS)

        # The idle-cash story Shreya must be able to reference
        assert "ICICI Pru Liquid Fund" in text
        assert "₹240,000" in text
        # Portfolio total, risk profile, and goals all present
        assert "₹509,620" in text
        assert "Risk profile: moderate" in text
        assert "Retirement Corpus" in text
        assert "₹5,000/month" in text

    def test_empty_inputs_produce_empty_context(self):
        assert format_account_context([], {}, []) == ""


class TestGetAccountContext:
    @pytest.mark.asyncio
    async def test_mock_backed_snapshot(self):
        """Without sandbox env vars the snapshot is mock-backed but complete."""
        text = await get_account_context()

        assert "ICICI Pru Liquid Fund" in text
        assert "Risk profile: moderate" in text
        assert "Financial goals:" in text

    @pytest.mark.asyncio
    async def test_failure_returns_empty_never_raises(self):
        """Account data being unavailable must never break chat."""
        with patch(
            "services.account_service.get_portfolio",
            AsyncMock(side_effect=RuntimeError("sandbox down")),
        ):
            assert await get_account_context() == ""
