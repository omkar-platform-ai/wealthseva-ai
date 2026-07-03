"""
Tests for risk profiler endpoint and scoring logic.
"""
import pytest
from models.schemas import RiskQuizAnswer, RiskProfile
from services.risk_service import score_quiz, ALLOCATIONS


def test_all_d_answers_aggressive():
    """All D answers (score 20) should return aggressive profile."""
    answers = [
        RiskQuizAnswer(question_id=1, answer="D"),
        RiskQuizAnswer(question_id=2, answer="D"),
        RiskQuizAnswer(question_id=3, answer="D"),
        RiskQuizAnswer(question_id=4, answer="D"),
        RiskQuizAnswer(question_id=5, answer="D"),
    ]

    profile, score = score_quiz(answers)

    assert profile == RiskProfile.AGGRESSIVE
    assert score == 20
    assert ALLOCATIONS[profile] == {"Equity": 70, "Mid/Small Cap": 20, "Debt": 10}


def test_all_a_answers_conservative():
    """All A answers (score 5) should return conservative profile."""
    answers = [
        RiskQuizAnswer(question_id=1, answer="A"),
        RiskQuizAnswer(question_id=2, answer="A"),
        RiskQuizAnswer(question_id=3, answer="A"),
        RiskQuizAnswer(question_id=4, answer="A"),
        RiskQuizAnswer(question_id=5, answer="A"),
    ]

    profile, score = score_quiz(answers)

    assert profile == RiskProfile.CONSERVATIVE
    assert score == 5
    assert ALLOCATIONS[profile] == {"Debt": 60, "Large Cap": 30, "Gold": 10}


def test_mixed_answers_moderate():
    """Mixed answers (score 12) should return moderate profile."""
    answers = [
        RiskQuizAnswer(question_id=1, answer="B"),
        RiskQuizAnswer(question_id=2, answer="C"),
        RiskQuizAnswer(question_id=3, answer="B"),
        RiskQuizAnswer(question_id=4, answer="C"),
        RiskQuizAnswer(question_id=5, answer="B"),
    ]

    profile, score = score_quiz(answers)

    assert profile == RiskProfile.MODERATE
    assert score == 12  # 2+3+2+3+2 = 12
    assert ALLOCATIONS[profile] == {"Equity Diversified": 40, "Debt": 40, "Balanced": 20}


def test_four_answers_validation_error():
    """Submitting only 4 answers should raise 422 validation error."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)

    response = client.post("/api/risk-profile", json={
        "answers": [
            {"question_id": 1, "answer": "A"},
            {"question_id": 2, "answer": "B"},
            {"question_id": 3, "answer": "C"},
            {"question_id": 4, "answer": "D"},
        ],
        "language": "en"
    })

    assert response.status_code == 422


def test_risk_profile_response_includes_trace():
    """Endpoint returns a deterministic trace: per-answer points, score, bands."""
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)

    with patch('services.claude_service.client', None):
        response = client.post("/api/risk-profile", json={
            "answers": [
                {"question_id": 1, "answer": "B"},
                {"question_id": 2, "answer": "C"},
                {"question_id": 3, "answer": "B"},
                {"question_id": 4, "answer": "C"},
                {"question_id": 5, "answer": "B"},
            ],
            "language": "en"
        })

    assert response.status_code == 200
    trace = response.json()["trace"]
    assert trace["answer_points"] == [2, 3, 2, 3, 2]
    assert trace["score"] == sum(trace["answer_points"]) == 12
    assert trace["max_score"] == 20
    assert trace["bands"] == {
        "conservative": [5, 8],
        "moderate": [9, 14],
        "aggressive": [15, 20],
    }


@pytest.mark.asyncio
async def test_generate_risk_explanation_without_credentials():
    """Test that generate_risk_explanation falls back gracefully when client is None."""
    from unittest.mock import patch
    from services.claude_service import generate_risk_explanation
    from models.schemas import Language

    with patch('services.claude_service.client', None):
        explanation = await generate_risk_explanation(
            profile="aggressive",
            score=20,
            allocation={"Equity": 70, "Mid/Small Cap": 20, "Debt": 10},
            language=Language.EN
        )

        assert explanation == "Your risk profile is aggressive with a score of 20. We recommend an allocation of {'Equity': 70, 'Mid/Small Cap': 20, 'Debt': 10}."


@pytest.mark.asyncio
async def test_generate_risk_explanation_with_bedrock():
    """Test that generate_risk_explanation calls Bedrock when client is available."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from services.claude_service import generate_risk_explanation
    from models.schemas import Language

    mock_bedrock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="As an aggressive investor, this high-growth allocation maximizes your returns.")]
    mock_bedrock.messages.create = AsyncMock(return_value=mock_response)

    with patch('services.claude_service.client', mock_bedrock):
        explanation = await generate_risk_explanation(
            profile="aggressive",
            score=20,
            allocation={"Equity": 70, "Mid/Small Cap": 20, "Debt": 10},
            language=Language.EN
        )

        assert explanation == "As an aggressive investor, this high-growth allocation maximizes your returns."
        mock_bedrock.messages.create.assert_called_once()
