"""
Text-to-speech endpoint — ElevenLabs proxy with browser fallback.

Voice v1 architecture (deliberate): the frontend speaks Claude's finished
text replies via this endpoint, so RAG and compliance guardrails stay in the
text pipeline. We do NOT use an ElevenLabs Conversational AI agent — that
would bypass both.

Graceful degradation contract: if ELEVENLABS_API_KEY or a voice ID is not
configured, or the ElevenLabs call fails, return {"fallback": "browser"} so
the frontend uses browser speechSynthesis — never a 500.
"""
import logging
import os

import httpx
from fastapi import APIRouter, Response

from models.schemas import TTSRequest
from services.language_service import get_voice_id

logger = logging.getLogger("wealthseva.tts")

router = APIRouter()

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

BROWSER_FALLBACK = {"fallback": "browser"}


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert reply text to speech audio in the user's language."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    voice_id = get_voice_id(request.language)

    if not api_key or not voice_id:
        # Log booleans only — never the key or voice ID values.
        logger.warning(
            "tts path=browser-fallback reason=missing-config lang=%s api_key_set=%s voice_id_set=%s",
            request.language.value, bool(api_key), bool(voice_id),
        )
        return BROWSER_FALLBACK

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{ELEVENLABS_TTS_URL}/{voice_id}",
                headers={"xi-api-key": api_key},
                params={"output_format": "mp3_44100_128"},
                json={
                    "text": request.text,
                    "model_id": "eleven_multilingual_v2",
                },
            )
            response.raise_for_status()
            return Response(content=response.content, media_type="audio/mpeg")
    except Exception as exc:
        # Surface the ElevenLabs reason (e.g. ip_not_allowed, quota_exceeded) so this
        # doesn't silently masquerade as "voices don't work". response.text carries
        # the actionable detail on HTTP errors; the API key never appears in it.
        detail = getattr(getattr(exc, "response", None), "text", "")
        logger.warning(
            "tts path=browser-fallback lang=%s elevenlabs failed: %s %s",
            request.language.value, exc, detail[:200],
        )
        return BROWSER_FALLBACK
