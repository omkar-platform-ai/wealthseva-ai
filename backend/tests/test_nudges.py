"""
Tests for Money Moments nudge engine — deterministic rules, no LLM.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from routers.nudges import _idle_cash_nudge, _sip_shortfall_nudges, _months_remaining

client = TestClient(app)


class TestIdleCashNudge:
    PORTFOLIO_WITH_EXCESS = [
        {"name": "ICICI Pru Liquid Fund", "category": "Liquid",
         "current_value": 240000.0, "gain_loss_pct": 6.9},
    ]
    PORTFOLIO_AT_THRESHOLD = [
        {"name": "ICICI Pru Liquid Fund", "category": "Liquid",
         "current_value": 170000.0, "gain_loss_pct": 6.9},  # < emergency_needed * 1.3
    ]
    PORTFOLIO_NO_LIQUID = [
        {"name": "HDFC Flexi Cap", "category": "Flexi Cap Equity", "current_value": 100000.0},
    ]

    def test_fires_when_liquid_exceeds_threshold(self):
        nudge = _idle_cash_nudge(self.PORTFOLIO_WITH_EXCESS)
        assert nudge is not None
        assert nudge.type.value == "idle_cash"
        assert nudge.severity == "high"
        assert "70,800" in nudge.title  # ₹2.4L - ₹1.692L ≈ ₹70,800
        assert "70,800" in nudge.chat_seed

    def test_suppressed_when_liquid_within_threshold(self):
        assert _idle_cash_nudge(self.PORTFOLIO_AT_THRESHOLD) is None

    def test_suppressed_when_no_liquid_fund(self):
        assert _idle_cash_nudge(self.PORTFOLIO_NO_LIQUID) is None

    def test_why_trace_has_three_data_points(self):
        nudge = _idle_cash_nudge(self.PORTFOLIO_WITH_EXCESS)
        assert nudge is not None
        assert len(nudge.why_trace.data_points) == 3
        assert "calculation" in nudge.why_trace.calculation.lower() or "₹" in nudge.why_trace.calculation


class TestSipShortfallNudge:
    GOALS_WITH_SHORTFALL = [
        {
            "id": "goal-002",
            "name": "Child Education",
            "target_amount": 2_500_000.0,
            "target_date": "2038-06-01",
            "current_savings": 80_000.0,
            "monthly_sip": 6_000.0,
        },
    ]
    GOALS_ON_TRACK = [
        {
            "id": "goal-001",
            "name": "Retirement Corpus",
            "target_amount": 5_000_000.0,
            "target_date": "2046-07-01",
            "current_savings": 0.0,
            "monthly_sip": 5_000.0,
        },
    ]
    GOALS_TOO_CLOSE = [
        {
            "id": "goal-003",
            "name": "Emergency Fund",
            "target_amount": 480_000.0,
            "target_date": "2027-03-31",
            "current_savings": 240_000.0,
            "monthly_sip": 5_000.0,
        },
    ]

    def test_fires_when_sip_is_below_required(self):
        nudges = _sip_shortfall_nudges(self.GOALS_WITH_SHORTFALL)
        assert len(nudges) == 1
        assert nudges[0].type.value == "sip_shortfall"
        assert "Child Education" in nudges[0].title

    def test_suppressed_when_sip_is_on_track(self):
        nudges = _sip_shortfall_nudges(self.GOALS_ON_TRACK)
        assert len(nudges) == 0

    def test_suppressed_when_goal_too_close(self):
        nudges = _sip_shortfall_nudges(self.GOALS_TOO_CLOSE)
        assert len(nudges) == 0

    def test_chat_seed_references_goal_name(self):
        nudges = _sip_shortfall_nudges(self.GOALS_WITH_SHORTFALL)
        assert "Child Education" in nudges[0].chat_seed

    def test_why_trace_shows_calculation(self):
        nudges = _sip_shortfall_nudges(self.GOALS_WITH_SHORTFALL)
        calc = nudges[0].why_trace.calculation
        assert "Required" in calc and "Actual" in calc and "Gap" in calc


class TestNudgesEndpoint:
    def test_get_nudges_200(self):
        response = client.get("/api/nudges")
        assert response.status_code == 200

    def test_response_has_nudges_and_source(self):
        data = client.get("/api/nudges").json()
        assert "nudges" in data
        assert "source" in data
        assert data["source"] in ("mock", "live")

    def test_idle_cash_nudge_present_in_mock_data(self):
        """Mock portfolio always has ₹2.4L liquid fund — idle-cash nudge must fire."""
        nudges = client.get("/api/nudges").json()["nudges"]
        types = [n["type"] for n in nudges]
        assert "idle_cash" in types

    def test_nudges_have_required_fields(self):
        nudges = client.get("/api/nudges").json()["nudges"]
        for n in nudges:
            assert all(k in n for k in ("id", "type", "title", "body", "severity", "why_trace", "chat_seed"))
            assert all(k in n["why_trace"] for k in ("data_points", "rule", "calculation"))

    def test_months_remaining_positive_for_future_date(self):
        months = _months_remaining("2038-06-01")
        assert months > 100  # well in the future
