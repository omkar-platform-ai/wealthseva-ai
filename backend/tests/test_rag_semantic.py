"""
Tests for multilingual RAG: vernacular keyword expansion (active today) and
local semantic retrieval over precomputed embeddings (quota-gated).
"""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

import services.rag_service as rag
from models.schemas import Language
from services.rag_service import _keyword_matching, retrieve_context

with open(rag._LOCAL_KB_PATH) as f:
    KB_CHUNKS = json.load(f)


@pytest.fixture(autouse=True)
def reset_semantic_cache():
    rag._reset_semantic_cache()
    yield
    rag._reset_semantic_cache()


class TestVernacularKeywordRetrieval:
    """Indic-script queries must retrieve English KB chunks via the term map."""

    def test_hindi_sip_query(self):
        result = _keyword_matching("एसआईपी क्या है", KB_CHUNKS)
        assert "Systematic Investment Plan" in result

    def test_marathi_investment_query(self):
        result = _keyword_matching("गुंतवणूक कशी करावी", KB_CHUNKS)
        assert "invest" in result.lower()

    def test_tamil_tax_query(self):
        result = _keyword_matching("வரி எவ்வளவு", KB_CHUNKS)
        assert "tax" in result.lower()

    def test_bengali_risk_query(self):
        result = _keyword_matching("ঝুঁকি কতটা", KB_CHUNKS)
        assert "risk" in result.lower()

    def test_tamil_inflected_form_matches_stem(self):
        """Agglutinative suffixes (ஓய்வூதியத்திற்கு = 'for pension') must
        still hit the stem entry via prefix matching."""
        result = _keyword_matching("ஓய்வூதியத்திற்கு எவ்வளவு சேமிக்க வேண்டும்", KB_CHUNKS)
        assert "retirement" in result.lower()

    def test_hindi_suffixed_form_matches_stem(self):
        """निवेशों (plural oblique) prefix-matches the निवेश entry."""
        result = _keyword_matching("निवेशों के बारे में बताओ", KB_CHUNKS)
        assert "invest" in result.lower()

    def test_english_queries_unaffected(self):
        result = _keyword_matching("what is a sip", KB_CHUNKS)
        assert "Systematic Investment Plan" in result

    @pytest.mark.asyncio
    async def test_full_retrieve_path_hindi(self):
        """End-to-end: no Pinecone, no embeddings file → vernacular keyword."""
        result = await retrieve_context("म्यूचुअल फंड में निवेश कैसे करें", Language.HI)
        assert "mutual" in result.lower()


class TestSemanticRetrieval:
    CHUNKS = [
        {"id": "a", "text": "SIP basics text", "keywords": ["sip"]},
        {"id": "b", "text": "Tax rules text", "keywords": ["tax"]},
        {"id": "c", "text": "Gold investing text", "keywords": ["gold"]},
    ]

    def _embeddings_file(self, tmp_path, vectors, kb_hash):
        path = tmp_path / "emb.json"
        path.write_text(json.dumps({
            "model_id": "amazon.titan-embed-text-v2:0",
            "dimensions": 4,
            "kb_sha256": kb_hash,
            "embeddings": {c["id"]: v for c, v in zip(self.CHUNKS, vectors)},
        }))
        return str(path)

    @pytest.mark.asyncio
    async def test_top_match_wins_and_floor_filters(self, tmp_path):
        path = self._embeddings_file(
            tmp_path, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], "HASH")
        with patch.object(rag, "_KB_EMBEDDINGS_PATH", path), \
             patch.object(rag, "_kb_file_sha256", return_value="HASH"), \
             patch.object(rag, "_embed_query_sync", return_value=[0.1, 0.99, 0, 0]):
            result = await rag._semantic_retrieve("any query", self.CHUNKS, top_k=2)

        # Only the tax chunk clears the 0.25 cosine floor
        assert result == "Tax rules text"

    @pytest.mark.asyncio
    async def test_stale_embeddings_are_refused(self, tmp_path):
        path = self._embeddings_file(tmp_path, [[1, 0, 0, 0]] * 3, "OLD_HASH")
        embed = MagicMock()
        with patch.object(rag, "_KB_EMBEDDINGS_PATH", path), \
             patch.object(rag, "_kb_file_sha256", return_value="NEW_HASH"), \
             patch.object(rag, "_embed_query_sync", embed):
            result = await rag._semantic_retrieve("any query", self.CHUNKS)

        assert result == ""
        embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_failure_sets_cooldown(self, tmp_path):
        path = self._embeddings_file(
            tmp_path, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], "HASH")
        embed = MagicMock(side_effect=RuntimeError("ThrottlingException"))
        with patch.object(rag, "_KB_EMBEDDINGS_PATH", path), \
             patch.object(rag, "_kb_file_sha256", return_value="HASH"), \
             patch.object(rag, "_embed_query_sync", embed):
            first = await rag._semantic_retrieve("q1", self.CHUNKS)
            second = await rag._semantic_retrieve("q2", self.CHUNKS)

        assert first == "" and second == ""
        # Second call must not burn another Bedrock attempt during cooldown
        assert embed.call_count == 1
        assert rag._semantic_cooldown_until > time.time()

    @pytest.mark.asyncio
    async def test_missing_file_falls_back_to_keyword(self):
        with patch.object(rag, "_KB_EMBEDDINGS_PATH", "/nonexistent/emb.json"):
            result = await rag._local_retrieve("what is a sip")
        assert "Systematic Investment Plan" in result
