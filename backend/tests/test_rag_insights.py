"""
Tests for RAG pipeline and market insights endpoint.
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from models.schemas import Language
from services.rag_service import retrieve_context
from main import app


@pytest.mark.asyncio
async def test_retrieve_context_no_pinecone_key_returns_string():
    """retrieve_context() with PINECONE_API_KEY missing → returns string, not exception."""
    with patch('services.rag_service._PINECONE_API_KEY', None):
        result = await retrieve_context("test query", Language.EN)
        assert isinstance(result, str)


@pytest.mark.asyncio
async def test_retrieve_context_no_mock_index_returns_empty():
    """retrieve_context() with no Pinecone key → returns '' not 500."""
    with patch('services.rag_service._PINECONE_API_KEY', None):
        result = await retrieve_context("test query", Language.EN)
        assert result == ""


@pytest.mark.asyncio
async def test_get_insights_english_returns_array():
    """GET /api/insights?language=en → array of 3 strings."""
    mock_insights = [
        "SIP returns are strong this quarter.",
        "Gold prices rising — consider rebalancing.",
        "IT sector showing 12% YoY growth.",
    ]
    with patch(
        'routers.insights.generate_market_insights',
        new=AsyncMock(return_value=mock_insights),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/insights?language=en")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) == 3
        assert all(isinstance(s, str) for s in data["insights"])


@pytest.mark.asyncio
async def test_get_insights_hindi_returns_array():
    """GET /api/insights?language=hi → array of 3 Hindi strings."""
    mock_insights = [
        "इस तिमाही में SIP रिटर्न मजबूत हैं।",
        "सोने की कीमतें बढ़ रही हैं — पोर्टफोलियो पुनर्संतुलन पर विचार करें।",
        "IT क्षेत्र में 12% वार्षिक वृद्धि दिख रही है।",
    ]
    with patch(
        'routers.insights.generate_market_insights',
        new=AsyncMock(return_value=mock_insights),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/insights?language=hi")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) == 3
        assert all(isinstance(s, str) for s in data["insights"])
