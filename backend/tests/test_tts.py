"""
Tests for /api/tts endpoint.
"""
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


class TestTTSEndpoint:
    """POST /api/tts — ElevenLabs proxy with browser fallback, never 500."""

    def test_without_api_key_returns_browser_fallback(self):
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}):
            response = client.post("/api/tts", json={"text": "Hello", "language": "en"})
        assert response.status_code == 200
        assert response.json() == {"fallback": "browser"}

    def test_without_voice_id_returns_browser_fallback(self):
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key"}), \
             patch("routers.tts.get_voice_id", return_value=""):
            response = client.post("/api/tts", json={"text": "Hello", "language": "ta"})
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
