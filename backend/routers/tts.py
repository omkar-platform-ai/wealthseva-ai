"""
Text-to-speech endpoint — provider chain with browser fallback.

Voice v1 architecture (deliberate): the frontend speaks Claude's finished
text replies via this endpoint, so RAG and compliance guardrails stay in the
text pipeline. We do NOT use an ElevenLabs Conversational AI agent — that
would bypass both.

Provider chain (WEA-78, WEA-84): TA/BN are synthesized by Sarvam Bulbul v3
(India-resident, Indic-native); EN/HI/MR by ElevenLabs. If the primary
provider fails for ANY reason (missing config, credit exhausted, payment
issue, rate limit, network error), the request automatically falls back to
ElevenLabs, then to the browser. Each provider helper returns a Response on
success or None to signal "try the next provider".

Graceful degradation contract: the endpoint never returns a 500 — if every
provider is unavailable it returns {"fallback": "browser"} so the frontend
uses browser speechSynthesis.
"""
import base64
import logging
import os

import httpx
from fastapi import APIRouter, Response

from models.schemas import Language, TTSRequest
from services.language_service import get_voice_id

logger = logging.getLogger("wealthseva.tts")

router = APIRouter()

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

BROWSER_FALLBACK = {"fallback": "browser"}

# Sarvam Bulbul v3 — primary for TA/BN (WEA-78, per WEA-76 partial-adopt).
# Auth is a custom `api-subscription-key` header (NOT Bearer), and the response
# is base64-encoded JSON — see _sarvam_tts. Additional locales can be moved to
# Sarvam by extending these two maps (WEA-83).
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_MODEL = "bulbul:v3"
_SARVAM_LOCALES = {"ta": "ta-IN", "bn": "bn-IN"}
_SARVAM_SPEAKER_ENV = {"ta": "SARVAM_VOICE_ID_TAMIL", "bn": "SARVAM_VOICE_ID_BENGALI"}


def _sarvam_speaker(lang_code: str) -> str:
    """Sarvam Bulbul v3 speaker name for the locale, from env."""
    return os.getenv(_SARVAM_SPEAKER_ENV.get(lang_code, ""), "").strip()


async def _sarvam_tts(text: str, lang_code: str):
    """Synthesize via Sarvam Bulbul v3. Returns a Response, or None to fall
    through to the next provider (missing config or any Sarvam failure —
    credit exhausted, payment issue, rate limit, network error).

    The response is base64-encoded JSON ({"audios": ["<b64>"]}); we decode
    audios[0]. mp3 is requested so the frontend receives audio/mpeg uniformly
    across providers (frontend/lib/voice.ts plays any audio/* content-type).
    """
    api_key = os.getenv("SARVAM_API_KEY", "")
    speaker = _sarvam_speaker(lang_code)
    if not api_key or not speaker:
        logger.warning(
            "tts provider=sarvam skip reason=missing-config lang=%s api_key_set=%s speaker_set=%s",
            lang_code, bool(api_key), bool(speaker),
        )
        return None

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
        # Surface the Sarvam error reason (e.g. rate_limit_exceeded_error,
        # payment) without exposing the key, then fall through to ElevenLabs.
        detail = getattr(getattr(exc, "response", None), "text", "")
        logger.warning(
            "tts provider=sarvam failed lang=%s: %s %s",
            lang_code, exc, detail[:200],
        )
        return None


async def _elevenlabs_tts(text: str, language: Language):
    """Synthesize via ElevenLabs. Returns a Response, or None to fall through
    (missing key/voice or any ElevenLabs failure)."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    voice_id = get_voice_id(language)

    if not api_key or not voice_id:
        logger.warning(
            "tts provider=elevenlabs skip reason=missing-config lang=%s api_key_set=%s voice_id_set=%s",
            language.value, bool(api_key), bool(voice_id),
        )
        return None

    # Log prefix of voice ID (safe — never the full ID) so prod logs confirm
    # per-language routing vs. silent EN fallback.
    logger.info("tts provider=elevenlabs lang=%s voice_prefix=%s", language.value, voice_id[:8])

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{ELEVENLABS_TTS_URL}/{voice_id}",
                headers={"xi-api-key": api_key},
                params={"output_format": "mp3_44100_128"},
                json={
                    "text": text,
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
            "tts provider=elevenlabs failed lang=%s: %s %s",
            language.value, exc, detail[:200],
        )
        return None


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert reply text to speech audio, trying providers in order:
    Sarvam (for its locales) → ElevenLabs → browser fallback."""
    lang_code = request.language.value

    # 1. Sarvam is primary for its configured locales (TA/BN today).
    if lang_code in _SARVAM_LOCALES:
        audio = await _sarvam_tts(request.text, lang_code)
        if audio is not None:
            return audio
        logger.info("tts fallback provider=sarvam->elevenlabs lang=%s", lang_code)

    # 2. ElevenLabs — primary for EN/HI/MR, fallback for Sarvam locales.
    audio = await _elevenlabs_tts(request.text, request.language)
    if audio is not None:
        return audio

    # 3. Both providers unavailable — browser speechSynthesis (never a 500).
    return BROWSER_FALLBACK
