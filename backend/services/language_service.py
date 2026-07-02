"""
Language detection and routing service.
Maps user input language → correct system prompt + ElevenLabs voice.
"""
import os
from langdetect import detect, LangDetectException
from models.schemas import Language


# ElevenLabs voice IDs per language — set in .env
VOICE_MAP: dict[str, str] = {
    "en": os.getenv("ELEVENLABS_VOICE_EN", ""),
    "hi": os.getenv("ELEVENLABS_VOICE_HI", ""),
    "mr": os.getenv("ELEVENLABS_VOICE_MR", ""),
    "ta": os.getenv("ELEVENLABS_VOICE_TA", ""),
    "bn": os.getenv("ELEVENLABS_VOICE_BN", ""),
}

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
    """Get ElevenLabs voice ID for the given language."""
    return VOICE_MAP.get(language.value, VOICE_MAP["en"])
