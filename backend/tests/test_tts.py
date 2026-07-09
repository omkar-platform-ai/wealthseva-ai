"""
Tests for /api/tts endpoint.
"""
import base64
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def _mock_async_client(post_result=None, post_side_effect=None):
    """Build a MagicMock that behaves like `async with httpx.AsyncClient()`."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=post_result, side_effect=post_side_effect)
    return mock_client


def _url_routed_client(handlers):
    """Build a client whose .post() branches on the request URL.

    `handlers` maps a URL substring → either a mock response (returned) or an
    Exception instance (raised). Lets one mock serve the Sarvam call and the
    ElevenLabs fallback call differently within a single request.
    """
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    def _post(url, *args, **kwargs):
        for substr, result in handlers.items():
            if substr in url:
                if isinstance(result, Exception):
                    raise result
                return result
        raise AssertionError(f"unexpected TTS URL: {url}")

    mock_client.post = AsyncMock(side_effect=_post)
    return mock_client


class TestTTSEndpoint:
    """POST /api/tts — Sarvam-primary voice chain (Sarvam → ElevenLabs →
    browser), never 500."""

    def test_without_api_key_returns_browser_fallback(self):
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}):
            response = client.post("/api/tts", json={"text": "Hello", "language": "en"})
        assert response.status_code == 200
        assert response.json() == {"fallback": "browser"}

    def test_without_voice_id_returns_browser_fallback(self):
        # Sarvam unconfigured + no ElevenLabs voice id → browser fallback.
        # (All locales are Sarvam-primary since WEA-83; unset Sarvam skips it.)
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key", "SARVAM_API_KEY": ""}), \
             patch("routers.tts.get_voice_id", return_value=""):
            response = client.post("/api/tts", json={"text": "Hello", "language": "mr"})
        assert response.status_code == 200
        assert response.json() == {"fallback": "browser"}

    def test_empty_text_rejected(self):
        response = client.post("/api/tts", json={"text": "", "language": "en"})
        assert response.status_code == 422

    def test_text_over_2000_chars_rejected(self):
        response = client.post("/api/tts", json={"text": "a" * 2001, "language": "en"})
        assert response.status_code == 422

    def test_success_returns_audio(self):
        mock_response = MagicMock()
        mock_response.content = b"mp3-bytes"
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key"}), \
             patch("routers.tts.get_voice_id", return_value="voice-hi"), \
             patch("routers.tts.httpx.AsyncClient",
                   return_value=_mock_async_client(post_result=mock_response)):
            response = client.post("/api/tts", json={"text": "नमस्ते", "language": "hi"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == b"mp3-bytes"

    def test_elevenlabs_failure_falls_back_to_browser(self):
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key"}), \
             patch("routers.tts.get_voice_id", return_value="voice-en"), \
             patch("routers.tts.httpx.AsyncClient",
                   return_value=_mock_async_client(
                       post_side_effect=httpx.ConnectError("elevenlabs down"))):
            response = client.post("/api/tts", json={"text": "Hello", "language": "en"})

        assert response.status_code == 200
        assert response.json() == {"fallback": "browser"}

    # ── Sarvam Bulbul v3 (TA/BN) — WEA-78 ────────────────────────────────────

    def test_sarvam_tamil_success(self):
        audio_bytes = b"mp3-bytes"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "audios": [base64.b64encode(audio_bytes).decode()]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = _mock_async_client(post_result=mock_response)

        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "test-sarvam-key",
            "SARVAM_VOICE_ID_TAMIL": "test-ta-speaker",
        }), patch("routers.tts.httpx.AsyncClient", return_value=mock_client):
            response = client.post(
                "/api/tts", json={"text": "வணக்கம்", "language": "ta"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == audio_bytes
        # Verify the Sarvam contract: correct URL, custom auth header, Bulbul v3 model, ta-IN.
        called_url = mock_client.post.call_args.args[0]
        called_kwargs = mock_client.post.call_args.kwargs
        assert called_url == "https://api.sarvam.ai/text-to-speech"
        assert called_kwargs["headers"]["api-subscription-key"] == "test-sarvam-key"
        assert called_kwargs["json"]["model"] == "bulbul:v3"
        assert called_kwargs["json"]["target_language_code"] == "ta-IN"
        assert called_kwargs["json"]["speaker"] == "test-ta-speaker"

    def test_sarvam_bengali_success(self):
        audio_bytes = b"mp3-bytes"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "audios": [base64.b64encode(audio_bytes).decode()]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = _mock_async_client(post_result=mock_response)

        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "test-sarvam-key",
            "SARVAM_VOICE_ID_BENGALI": "test-bn-speaker",
        }), patch("routers.tts.httpx.AsyncClient", return_value=mock_client):
            response = client.post(
                "/api/tts", json={"text": "নমস্কার", "language": "bn"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == audio_bytes
        called_kwargs = mock_client.post.call_args.kwargs
        assert called_kwargs["json"]["target_language_code"] == "bn-IN"
        assert called_kwargs["json"]["speaker"] == "test-bn-speaker"

    def test_sarvam_and_elevenlabs_unconfigured_falls_back_to_browser(self):
        # Neither provider configured for ta → browser fallback (never 500).
        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "",
            "SARVAM_VOICE_ID_TAMIL": "test-ta-speaker",
            "ELEVENLABS_API_KEY": "",
        }):
            response = client.post(
                "/api/tts", json={"text": "வணக்கம்", "language": "ta"}
            )
        assert response.status_code == 200
        assert response.json() == {"fallback": "browser"}

    def test_sarvam_failure_falls_back_to_elevenlabs(self):
        # WEA-84: Sarvam errors (e.g. credit exhausted) → ElevenLabs serves ta.
        el_response = MagicMock()
        el_response.content = b"elevenlabs-mp3"
        el_response.raise_for_status = MagicMock()
        mock_client = _url_routed_client({
            "api.sarvam.ai": httpx.ConnectError("sarvam down"),
            "api.elevenlabs.io": el_response,
        })

        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "test-sarvam-key",
            "SARVAM_VOICE_ID_TAMIL": "test-ta-speaker",
            "ELEVENLABS_API_KEY": "test-el-key",
        }), patch("routers.tts.get_voice_id", return_value="voice-ta"), \
             patch("routers.tts.httpx.AsyncClient", return_value=mock_client):
            response = client.post(
                "/api/tts", json={"text": "வணக்கம்", "language": "ta"}
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == b"elevenlabs-mp3"
        # Both providers were attempted, in order.
        called_urls = [c.args[0] for c in mock_client.post.call_args_list]
        assert any("api.sarvam.ai" in u for u in called_urls)
        assert any("api.elevenlabs.io" in u for u in called_urls)

    def test_sarvam_and_elevenlabs_both_fail_falls_back_to_browser(self):
        # WEA-84: both providers error → browser fallback (200, never 500).
        mock_client = _url_routed_client({
            "api.sarvam.ai": httpx.ConnectError("sarvam down"),
            "api.elevenlabs.io": httpx.ConnectError("elevenlabs down"),
        })
        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "test-sarvam-key",
            "SARVAM_VOICE_ID_TAMIL": "test-ta-speaker",
            "ELEVENLABS_API_KEY": "test-el-key",
        }), patch("routers.tts.get_voice_id", return_value="voice-ta"), \
             patch("routers.tts.httpx.AsyncClient", return_value=mock_client):
            response = client.post(
                "/api/tts", json={"text": "வணக்கம்", "language": "ta"}
            )
        assert response.status_code == 200
        assert response.json() == {"fallback": "browser"}

    # ── EN/HI/MR → Sarvam-primary — WEA-83 ───────────────────────────────────

    def test_english_routes_to_sarvam_when_configured(self):
        # WEA-83: en is now Sarvam-primary — must hit the Sarvam URL with en-IN.
        audio_bytes = b"mp3-bytes"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "audios": [base64.b64encode(audio_bytes).decode()]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = _mock_async_client(post_result=mock_response)

        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "test-sarvam-key",
            "SARVAM_VOICE_ID_ENGLISH": "test-en-speaker",
        }), patch("routers.tts.httpx.AsyncClient", return_value=mock_client):
            response = client.post("/api/tts", json={"text": "Hello", "language": "en"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == audio_bytes
        called_url = mock_client.post.call_args.args[0]
        called_kwargs = mock_client.post.call_args.kwargs
        assert called_url == "https://api.sarvam.ai/text-to-speech"
        assert called_kwargs["json"]["target_language_code"] == "en-IN"
        assert called_kwargs["json"]["speaker"] == "test-en-speaker"

    def test_english_falls_back_to_elevenlabs_when_sarvam_unconfigured(self):
        # WEA-83 + WEA-84: with no Sarvam speaker for en, Sarvam skips and
        # ElevenLabs serves the voice (graceful, no regression for EN/HI/MR).
        el_response = MagicMock()
        el_response.content = b"elevenlabs-mp3"
        el_response.raise_for_status = MagicMock()
        mock_client = _mock_async_client(post_result=el_response)

        with patch.dict(os.environ, {
            "SARVAM_API_KEY": "",
            "ELEVENLABS_API_KEY": "test-el-key",
        }), patch("routers.tts.get_voice_id", return_value="voice-en"), \
             patch("routers.tts.httpx.AsyncClient", return_value=mock_client):
            response = client.post("/api/tts", json={"text": "Hello", "language": "en"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == b"elevenlabs-mp3"
        called_url = mock_client.post.call_args.args[0]
        assert called_url.startswith("https://api.elevenlabs.io")
