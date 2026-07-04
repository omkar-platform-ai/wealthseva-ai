"""
Language detection and routing service.
Maps user input language → correct system prompt + ElevenLabs voice.
"""
import os
from langdetect import detect, LangDetectException
from models.schemas import Language


# ElevenLabs voice IDs per language — provisioned via environment / AWS Secrets
# Manager. Two key-naming conventions exist across environments, so we read the
# canonical name (documented in .env.example) first and fall back to the legacy
# name used in the production secret. Reading only one convention leaves
# VOICE_MAP empty in the other environment, which collapses every language to a
# single browser-TTS voice (WEA-65).
_VOICE_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "en": ("ELEVENLABS_VOICE_EN", "ELEVENLABS_VOICE_ID_ENGLISH"),
    "hi": ("ELEVENLABS_VOICE_HI", "ELEVENLABS_VOICE_ID_HINDI"),
    "mr": ("ELEVENLABS_VOICE_MR", "ELEVENLABS_VOICE_ID_MARATHI"),
    "ta": ("ELEVENLABS_VOICE_TA", "ELEVENLABS_VOICE_ID_TAMIL"),
    "bn": ("ELEVENLABS_VOICE_BN", "ELEVENLABS_VOICE_ID_BENGALI"),
}


def _resolve_voice_id(lang_code: str) -> str:
    """Return the first non-empty voice ID configured for `lang_code`."""
    for env_key in _VOICE_ENV_KEYS.get(lang_code, ()):
        value = os.getenv(env_key, "").strip()
        if value:
            return value
    return ""


VOICE_MAP: dict[str, str] = {lang: _resolve_voice_id(lang) for lang in _VOICE_ENV_KEYS}

# Map langdetect codes → our Language enum
LANGDETECT_MAP: dict[str, Language] = {
    "en": Language.EN,
    "hi": Language.HI,
    "mr": Language.MR,
    "ta": Language.TA,
    "bn": Language.BN,
}

SYSTEM_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "../../ai/system_prompts")


def detect_language(text: str, fallback: Language = Language.EN) -> Language:
    """Detect language of input text, fall back to user preference on failure."""
    try:
        detected = detect(text)
        return LANGDETECT_MAP.get(detected, fallback)
    except LangDetectException:
        return fallback


def get_system_prompt(language: Language) -> str:
    """Load the per-language wealth advisor system prompt."""
    # Prompt is always read from ai/system_prompts/wealth_advisor_{lang}.md — never hardcoded.
    # RBI FREE-AI compliance text (AI disclosure + financial figures guardrail) lives in those files.
    prompt_file = os.path.join(SYSTEM_PROMPT_DIR, f"wealth_advisor_{language.value}.md")
    fallback_file = os.path.join(SYSTEM_PROMPT_DIR, "wealth_advisor_en.md")

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        with open(fallback_file, "r", encoding="utf-8") as f:
            return f.read()


def get_voice_id(language: Language) -> str:
    """Get the ElevenLabs voice ID for the given language.

    Falls back to the English voice when the requested language has no voice ID
    configured; if English is also unset, returns "" and the /api/tts router
    drops to browser speechSynthesis (never a 500). The ``or`` handles the
    empty-string case, which ``dict.get(key, default)`` alone would not.
    """
    return VOICE_MAP.get(language.value) or VOICE_MAP.get("en", "")
