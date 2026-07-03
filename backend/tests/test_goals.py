"""
Tests for goals router: GET /api/goals/presets, POST /api/goals, _compute_projection().
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from routers.goals import _compute_projection

http_client = TestClient(app)


class TestGoalPresets:
    """GET /api/goals/presets returns the expected structure."""

    def test_presets_returns_four_items(self):
        response = http_client.get("/api/goals/presets")
        assert response.status_code == 200
        body = response.json()
        assert "presets" in body
        presets = body["presets"]
        assert len(presets) == 4

    def test_presets_have_required_fields(self):
        response = http_client.get("/api/goals/presets")
        presets = response.json()["presets"]
        for p in presets:
            assert "id" in p
            assert "label_key" in p
            assert "target_amount" in p
            assert "years" in p
            assert p["target_amount"] > 0
            assert p["years"] > 0


class TestComputeProjection:
    """Unit tests for _compute_projection()."""

    def test_retirement_sip_in_reasonable_range(self):
        target_date = (date.today().replace(year=date.today().year + 25)).isoformat()
        result = _compute_projection(10_000_000, 0, target_date)
        # 12% p.a. SIP for 25 years to reach ₹1 crore → expect ~₹4,000–₹8,000/month
        assert 3_000 <= result["monthly_sip"] <= 10_000, (
            f"SIP ₹{result['monthly_sip']} outside expected range"
        )
        assert result["projected_corpus"] > 0
        assert len(result["yearly_data"]) > 0

    def test_fully_funded_goal_returns_zero_sip(self):
        target_date = (date.today().replace(year=date.today().year + 5)).isoformat()
        # current_savings already exceeds target_amount → no SIP needed
        result = _compute_projection(500_000, 1_000_000, target_date)
        assert result["monthly_sip"] == 0
        assert result["trace"]["gap"] == 0

    def test_invalid_date_returns_safe_fallback(self):
        result = _compute_projection(500_000, 0, "not-a-date")
        assert result["monthly_sip"] == 0
        assert result["projected_corpus"] == 500_000
        assert result["yearly_data"] == []
        assert result["trace"] is None

    def test_projection_includes_deterministic_trace(self):
        target_date = (date.today().replace(year=date.today().year + 10)).isoformat()
        result = _compute_projection(5_000_000, 100_000, target_date)
        trace = result["trace"]
        assert trace["target_amount"] == 5_000_000
        assert trace["current_savings"] == 100_000
        assert trace["months"] == 120
        assert trace["annual_return_pct"] == 12
        # Trace numbers must be internally consistent with the projection
        # (±1 tolerance: gap and fv_savings are rounded independently)
        assert trace["monthly_sip"] == result["monthly_sip"]
        assert abs(trace["gap"] - (5_000_000 - trace["fv_savings"])) <= 1


class TestGoalsEndpoint:
    """POST /api/goals with client=None uses fallback path."""

    def test_post_goals_client_none_returns_200(self):
        target_date = (date.today().replace(year=date.today().year + 10)).isoformat()
        payload = {
            "goals": [
                {
                    "name": "House",
                    "target_amount": 5_000_000,
                    "target_date": target_date,
                    "current_savings": 100_000,
                }
            ],
            "language": "en",
        }
        with patch("services.claude_service.client", None):
            response = http_client.post("/api/goals", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert "projections" in body
        assert "total_monthly_required" in body
        assert "summary" in body
        assert isinstance(body["summary"], str) and len(body["summary"]) > 0
