"""
Tests for RAG service and market insights endpoint.
"""
import os
import json
import pytest
import tempfile
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from models.schemas import Language

http_client = TestClient(app)


class TestRetrieveContext:
    """Tests for rag_service.retrieve_context()."""

    @pytest.mark.asyncio
    async def test_no_pinecone_key_returns_string_not_exception(self):
        """retrieve_context() with PINECONE_API_KEY unset → returns a string, never raises."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure PINECONE_API_KEY is absent
            os.environ.pop("PINECONE_API_KEY", None)

            # Reload module-level constant that was captured at import time
            with patch("services.rag_service._PINECONE_API_KEY", None):
                from services.rag_service import retrieve_context
                result = await retrieve_context("What is SIP?", Language.EN)

            assert isinstance(result, str), "Must return str, not raise"

    @pytest.mark.asyncio
    async def test_missing_mock_index_returns_empty_string_not_500(self):
        """retrieve_context() when mock_index.json is absent → returns '' not exception."""
        with patch("services.rag_service._PINECONE_API_KEY", None):
            # Point the mock index path to a non-existent file
            with patch("services.rag_service._MOCK_INDEX_PATH", "/tmp/nonexistent_mock_index_xyz.json"):
                from services.rag_service import retrieve_context
                result = await retrieve_context("Tell me about ELSS", Language.HI)

        assert result == "", f"Expected empty string, got: {result!r}"


class TestInsightsEndpoint:
    """Tests for GET /api/insights."""

    def test_insights_english_returns_three_strings(self):
        """GET /api/insights?language=en → JSON array of 3 strings."""
        # client=None triggers mock path in generate_market_insights
        with patch("services.claude_service.client", None):
            response = http_client.get("/api/insights?language=en")

        assert response.status_code == 200
        body = response.json()
        assert "insights" in body
        insights = body["insights"]
        assert isinstance(insights, list), "insights must be a list"
        assert len(insights) == 3, f"Expected 3 insights, got {len(insights)}"
        assert all(isinstance(s, str) for s in insights), "All insights must be strings"

    def test_insights_hindi_returns_three_hindi_strings(self):
        """GET /api/insights?language=hi → JSON array of 3 Hindi strings."""
        with patch("services.claude_service.client", None):
            response = http_client.get("/api/insights?language=hi")

        assert response.status_code == 200
        body = response.json()
        assert "insights" in body
        insights = body["insights"]
        assert isinstance(insights, list)
        assert len(insights) == 3, f"Expected 3 insights, got {len(insights)}"
        # Hindi strings contain Devanagari characters (Unicode range U+0900–U+097F)
        assert all(
            any("ऀ" <= ch <= "ॿ" for ch in s) for s in insights
        ), "Expected Hindi (Devanagari) characters in all insights"
