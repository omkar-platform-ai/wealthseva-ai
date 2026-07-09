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
import base64
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

# Sarvam Bulbul v3 — TA/BN only (WEA-78, per WEA-76 partial-adopt). EN/HI/MR
# stay on ElevenLabs below. Auth is a custom `api-subscription-key` header (NOT
# Bearer), and the response is base64-encoded JSON — see _sarvam_text_to_speech.
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_MODEL = "bulbul:v3"
_SARVAM_LOCALES = {"ta": "ta-IN", "bn": "bn-IN"}
_SARVAM_SPEAKER_ENV = {"ta": "SARVAM_VOICE_ID_TAMIL", "bn": "SARVAM_VOICE_ID_BENGALI"}


def _sarvam_speaker(lang_code: str) -> str:
    """Sarvam Bulbul v3 speaker name for the locale, from env."""
    return os.getenv(_SARVAM_SPEAKER_ENV.get(lang_code, ""), "").strip()


async def _sarvam_text_to_speech(text: str, lang_code: str):
    """Synthesize TA/BN via Sarvam Bulbul v3; browser fallback on any failure.

    Mirrors the ElevenLabs graceful-degradation contract: missing config or a
    Sarvam error returns {"fallback": "browser"} — never a 500. The response is
    base64-encoded JSON ({"audios": ["<b64>"]}); we decode audios[0]. mp3 is
    requested so the frontend receives audio/mpeg uniformly across providers
    (frontend/lib/voice.ts plays any audio/* content-type).
    """
    api_key = os.getenv("SARVAM_API_KEY", "")
    speaker = _sarvam_speaker(lang_code)
    if not api_key or not speaker:
        logger.warning(
            "tts path=browser-fallback reason=missing-sarvam-config lang=%s api_key_set=%s speaker_set=%s",
            lang_code, bool(api_key), bool(speaker),
        )
        return BROWSER_FALLBACK

    logger.info("tts provider=sarvam lang=%s speaker_prefix=%s", lang_code, speaker[:8])

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                SARVAM_TTS_URL,
                headers={"api-subscription-key": api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "target_language_code": _SARVAM_LOCALES[lang_code],
                    "model": SARVAM_MODEL,
                    "speaker": speaker,
                    "output_audio_codec": "mp3",
                },
            )
            response.raise_for_status()
            audio_b64 = response.json()["audios"][0]
            return Response(content=base64.b64decode(audio_b64), media_type="audio/mpeg")
    except Exception as exc:
        # Same diagnostic pattern as the ElevenLabs branch — surface the Sarvam
        # error reason (e.g. rate_limit_exceeded_error) without exposing the key.
        detail = getattr(getattr(exc, "response", None), "text", "")
        logger.warning(
            "tts path=browser-fallback lang=%s sarvam failed: %s %s",
            lang_code, exc, detail[:200],
        )
        return BROWSER_FALLBACK


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert reply text to speech audio in the user's language."""
    # TA/BN route to Sarvam Bulbul v3 (WEA-78); EN/HI/MR use ElevenLabs below.
    if request.language.value in _SARVAM_LOCALES:
        return await _sarvam_text_to_speech(request.text, request.language.value)

    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    voice_id = get_voice_id(request.language)

    if not api_key or not voice_id:
        logger.warning(
            "tts path=browser-fallback reason=missing-config lang=%s api_key_set=%s voice_id_set=%s",
            request.language.value, bool(api_key), bool(voice_id),
        )
        return BROWSER_FALLBACK

    # Log prefix of voice ID (safe — never the full ID) so prod logs confirm
    # per-language routing vs. silent EN fallback.
    logger.info("tts lang=%s voice_prefix=%s", request.language.value, voice_id[:8])

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
