"""
Tests for IDBI mock endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def unset_idbi_env(monkeypatch):
    """Ensure IDBI env vars are unset for mock testing"""
    monkeypatch.setenv("IDBI_SANDBOX_BASE_URL", "")
    monkeypatch.setenv("IDBI_SANDBOX_API_KEY", "")


class TestIDBIEndpoints:
    """Test suite for IDBI mock endpoints"""

    def test_get_portfolio_returns_mock(self, client):
        """Test portfolio endpoint returns mock data with source: mock"""
        response = client.get("/api/idbi/portfolio")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "source" in data
        assert data["source"] == "mock"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Verify portfolio holding structure
        holding = data["data"][0]
        assert "isin" in holding
        assert "name" in holding
        assert "category" in holding
        assert "units" in holding
        assert "nav" in holding
        assert "current_value" in holding
        assert "gain_loss_pct" in holding

    def test_get_risk_profile_returns_mock(self, client):
        """Test risk profile endpoint returns mock data with source: mock"""
        response = client.get("/api/idbi/risk")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "source" in data
        assert data["source"] == "mock"
        assert isinstance(data["data"], dict)

        # Verify risk profile structure
        risk_data = data["data"]
        assert "profile" in risk_data
        assert "score" in risk_data
        assert "recommended_allocation" in risk_data
        assert isinstance(risk_data["recommended_allocation"], dict)

    def test_get_goals_returns_mock(self, client):
        """Test goals endpoint returns mock data with source: mock"""
        response = client.get("/api/idbi/goals")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "source" in data
        assert data["source"] == "mock"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Verify goal structure
        goal = data["data"][0]
        assert "id" in goal
        assert "name" in goal
        assert "target_amount" in goal
        assert "target_date" in goal
        assert "current_savings" in goal
        assert "monthly_sip" in goal
        assert "progress_pct" in goal

    def test_get_transactions_returns_mock(self, client):
        """Test transactions endpoint returns mock data with source: mock"""
        response = client.get("/api/idbi/transactions")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "source" in data
        assert data["source"] == "mock"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Verify transaction structure
        transaction = data["data"][0]
        assert "category" in transaction
        assert "amount" in transaction
        assert "month" in transaction

    def test_all_endpoints_use_mock_without_env_vars(self, client):
        """Verify all endpoints return source: mock when env vars not set"""
        endpoints = ["/api/idbi/portfolio", "/api/idbi/risk", "/api/idbi/goals", "/api/idbi/transactions"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed for {endpoint}"
            data = response.json()
            assert data["source"] == "mock", f"Non-mock source for {endpoint}"
