"""
Tests for the Anthropic direct-API fallback (WEA-57).

Bedrock stays primary; the direct Anthropic API is used only when the Bedrock
call raises. These tests are hermetic — they patch the module-level clients and
never make a network call, so they prove the selection/fallback logic without a
real key.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import patch

from models.schemas import Language
import services.claude_service as cs


# ── Fake async clients ───────────────────────────────────────────────────────
class _FakeStreamCM:
    """Async context manager mimicking client.messages.stream(...)."""

    def __init__(self, chunks=None, raise_on_enter=False):
        self._chunks = chunks or []
        self._raise = raise_on_enter

    async def __aenter__(self):
        if self._raise:
            raise RuntimeError("Bedrock AccessDeniedException: INVALID_PAYMENT_INSTRUMENT")
        return self

    async def __aexit__(self, *args):
        return False

    @property
    def text_stream(self):
        async def _gen():
            for chunk in self._chunks:
                yield chunk
        return _gen()


def _stream_client(chunks=None, raises=False):
    def _stream(**kwargs):
        return _FakeStreamCM(chunks=chunks, raise_on_enter=raises)
    return SimpleNamespace(messages=SimpleNamespace(stream=_stream))


def _create_client(text=None, raises=False):
    async def _create(**kwargs):
        if raises:
            raise RuntimeError("Bedrock AccessDeniedException: INVALID_PAYMENT_INSTRUMENT")
        return SimpleNamespace(content=[SimpleNamespace(text=text)])
    return SimpleNamespace(messages=SimpleNamespace(create=_create))


async def _collect(agen):
    return "".join([chunk async for chunk in agen])


# ── Candidate selection ──────────────────────────────────────────────────────
class TestClientCandidates:
    def test_bedrock_first_then_anthropic(self):
        with patch.object(cs, "client", object()), patch.object(cs, "_anthropic_client", object()):
            labels = [c[2] for c in cs._get_client_candidates()]
        assert labels == ["bedrock", "anthropic"]

    def test_empty_when_no_clients(self):
        with patch.object(cs, "client", None), patch.object(cs, "_anthropic_client", None):
            assert cs._get_client_candidates() == []

    def test_anthropic_only_uses_anthropic_model(self):
        with patch.object(cs, "client", None), patch.object(cs, "_anthropic_client", object()):
            candidates = cs._get_client_candidates()
        assert [c[2] for c in candidates] == ["anthropic"]
        assert candidates[0][1] == cs.ANTHROPIC_MODEL_ID


# ── stream_chat fallback ─────────────────────────────────────────────────────
@pytest.mark.asyncio
class TestStreamChatFallback:
    async def test_falls_back_to_anthropic_when_bedrock_raises(self):
        bedrock = _stream_client(raises=True)
        direct = _stream_client(chunks=["Real ", "Claude ", "answer"])
        with patch.object(cs, "client", bedrock), patch.object(cs, "_anthropic_client", direct):
            out = await _collect(cs.stream_chat("hi", [], Language.EN))
        assert out == "Real Claude answer"
        assert "demo mode" not in out

    async def test_bedrock_used_when_healthy(self):
        bedrock = _stream_client(chunks=["Bedrock ", "answer"])
        direct = _stream_client(raises=True)  # would fail if wrongly reached
        with patch.object(cs, "client", bedrock), patch.object(cs, "_anthropic_client", direct):
            out = await _collect(cs.stream_chat("hi", [], Language.EN))
        assert out == "Bedrock answer"

    async def test_demo_when_no_clients(self):
        with patch.object(cs, "client", None), patch.object(cs, "_anthropic_client", None):
            out = await _collect(cs.stream_chat("hi", [], Language.EN))
        assert "demo mode" in out

    async def test_demo_when_all_providers_fail(self):
        with patch.object(cs, "client", _stream_client(raises=True)), \
             patch.object(cs, "_anthropic_client", _stream_client(raises=True)):
            out = await _collect(cs.stream_chat("hi", [], Language.EN))
        assert "demo mode" in out


# ── generate_market_insights fallback ────────────────────────────────────────
@pytest.mark.asyncio
class TestInsightsFallback:
    async def test_falls_back_to_anthropic(self):
        cs._insights_cache.clear()
        bedrock = _create_client(raises=True)
        direct = _create_client(text='["one", "two", "three"]')
        with patch.object(cs, "client", bedrock), patch.object(cs, "_anthropic_client", direct):
            out = await cs.generate_market_insights(Language.EN)
        assert out == ["one", "two", "three"]

    async def test_mock_when_all_providers_fail(self):
        cs._insights_cache.clear()
        with patch.object(cs, "client", _create_client(raises=True)), \
             patch.object(cs, "_anthropic_client", _create_client(raises=True)):
            out = await cs.generate_market_insights(Language.EN)
        assert out == cs._MOCK_INSIGHTS[Language.EN]
