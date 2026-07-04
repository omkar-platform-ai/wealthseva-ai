"""
Tests for RAG service and market insights endpoint.
"""
import os
import json
import pytest
from unittest.mock import patch
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
    async def test_missing_knowledge_base_returns_empty_string_not_500(self):
        """retrieve_context() when knowledge_base.json is absent → returns '' not exception."""
        with patch("services.rag_service._PINECONE_API_KEY", None):
            # Point the knowledge base path to a non-existent file
            with patch("services.rag_service._LOCAL_KB_PATH", "/tmp/nonexistent_kb_xyz.json"):
                from services.rag_service import retrieve_context
                result = await retrieve_context("Tell me about ELSS", Language.HI)

        assert result == "", f"Expected empty string, got: {result!r}"

    @pytest.mark.asyncio
    async def test_sip_query_retrieves_sip_chunks_from_local_kb(self):
        """Without Pinecone, a SIP question retrieves SIP content from the curated KB."""
        with patch("services.rag_service._PINECONE_API_KEY", None):
            from services.rag_service import retrieve_context
            result = await retrieve_context("How much should I invest monthly through SIP?", Language.EN)

        assert result != "", "Expected non-empty context from local knowledge base"
        assert "SIP" in result or "sip" in result.lower()


class TestKnowledgeBase:
    """Integrity checks for the curated local knowledge base."""

    def _load_kb(self):
        from services.rag_service import _LOCAL_KB_PATH
        with open(_LOCAL_KB_PATH) as f:
            return json.load(f)

    def test_kb_exists_with_at_least_100_chunks(self):
        chunks = self._load_kb()
        assert len(chunks) >= 100, f"Expected >=100 chunks, got {len(chunks)}"

    def test_kb_chunks_have_unique_ids_and_required_fields(self):
        chunks = self._load_kb()
        ids = [c["id"] for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk ids must be unique"
        for c in chunks:
            assert c.get("text"), f"Chunk {c.get('id')} missing text"
            assert c.get("keywords"), f"Chunk {c.get('id')} missing keywords"
            assert c.get("topic"), f"Chunk {c.get('id')} missing topic"

    def test_keyword_field_outranks_text_only_match(self):
        """A chunk whose curated keywords match must beat a text-only match."""
        from services.rag_service import _keyword_matching
        chunks = [
            {"text": "Generic sentence mentioning retirement once.", "keywords": []},
            {"text": "Focused chunk about corpus planning.", "keywords": ["retirement", "corpus"]},
        ]
        result = _keyword_matching("retirement corpus", chunks, top_k=1)
        assert result == "Focused chunk about corpus planning."


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
