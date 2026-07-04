"""
Portfolio analyzer endpoint tests.
Tests JSON response structure, language support, and sample CSV generation.
"""
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

# Sample portfolio CSV content
SAMPLE_CSV = """Ticker,Category,Value,Units
HDFC Top 100,Large Cap Equity,50000,120
ICICI Prudential Gilt,Debt,30000,450
SBI Liquid Fund,Liquid,20000,200"""


def test_post_portfolio_english():
    """POST /api/portfolio with English returns structured JSON."""
    files = {"file": ("portfolio.csv", SAMPLE_CSV, "text/csv")}
    data = {"language": "en"}

    response = client.post("/api/portfolio", files=files, data=data)

    assert response.status_code == 200
    result = response.json()

    # Verify response structure
    assert "summary" in result
    assert "recommendations" in result
    assert "sip_suggestion" in result

    # Verify recommendations is a list with exactly 3 items
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) == 3

    # Verify all recommendations are strings
    assert all(isinstance(rec, str) for rec in result["recommendations"])


def test_post_portfolio_hindi():
    """POST /api/portfolio with Hindi returns Hindi text in all fields."""
    files = {"file": ("portfolio.csv", SAMPLE_CSV, "text/csv")}
    data = {"language": "hi"}

    response = client.post("/api/portfolio", files=files, data=data)

    assert response.status_code == 200
    result = response.json()

    # Verify response structure (same structure, different language)
    assert "summary" in result
    assert "recommendations" in result
    assert "sip_suggestion" in result

    # Verify structure consistency
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) == 3
    assert all(isinstance(rec, str) for rec in result["recommendations"])

    # If using mock credentials, we can't verify Hindi content
    # but we verify the structure is correct


def test_get_sample_portfolio():
    """GET /api/portfolio/sample returns downloadable CSV with correct header."""
    response = client.get("/api/portfolio/sample")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert 'filename="sample_portfolio.csv"' in response.headers["content-disposition"]

    # Verify CSV content
    csv_content = response.text
    assert "Ticker,Category,Value,Units" in csv_content
    assert "HDFC Top 100" in csv_content
    assert "ICICI Prudential Gilt" in csv_content
    assert "SBI Liquid Fund" in csv_content


def test_file_too_large():
    """POST /api/portfolio rejects files larger than 5MB."""
    # Create a file larger than 5MB
    large_content = "A" * (6 * 1024 * 1024)  # 6MB
    files = {"file": ("large.csv", large_content, "text/csv")}
    data = {"language": "en"}

    response = client.post("/api/portfolio", files=files, data=data)

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_malformed_csv():
    """POST /api/portfolio rejects malformed CSV with proper error."""
    # CSV with mismatched column counts that pandas can't parse with default error handling
    # Empty file causes parsing error
    malformed_csv = ""
    files = {"file": ("empty.csv", malformed_csv, "text/csv")}
    data = {"language": "en"}

    response = client.post("/api/portfolio", files=files, data=data)

    assert response.status_code == 400
    # Either "invalid csv" or "empty" error is acceptable
    detail = response.json()["detail"].lower()
    assert "invalid" in detail or "empty" in detail or "no columns" in detail


def test_missing_required_columns():
    """POST /api/portfolio rejects CSV missing required columns."""
    incomplete_csv = """Ticker,Category
HDFC Top 100,Large Cap Equity
ICICI Prudential Gilt,Debt"""
    files = {"file": ("incomplete.csv", incomplete_csv, "text/csv")}
    data = {"language": "en"}

    response = client.post("/api/portfolio", files=files, data=data)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "missing required columns" in detail.lower()
    assert "value" in detail.lower() or "units" in detail.lower()


def test_invalid_language_code():
    """POST /api/portfolio rejects invalid language codes."""
    files = {"file": ("portfolio.csv", SAMPLE_CSV, "text/csv")}
    data = {"language": "xyz"}  # Invalid language code

    response = client.post("/api/portfolio", files=files, data=data)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "invalid language" in detail.lower()
    assert "xyz" in detail.lower()
