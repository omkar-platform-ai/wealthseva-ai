"""
Tests for per-language ElevenLabs voice selection (WEA-65).

The reported bug: the same (browser default) voice played for every language
because the production secret stored voice IDs under different key names than
the code read, leaving VOICE_MAP empty. These tests lock in that each language
resolves to its own distinct voice ID under BOTH naming conventions, with a
graceful fallback chain (language voice → English voice → browser TTS).
"""
import importlib

import pytest

from models.schemas import Language
from services import language_service

# All five canonical env keys and their legacy production-secret equivalents.
CANONICAL_KEYS = {
    "en": "ELEVENLABS_VOICE_EN",
    "hi": "ELEVENLABS_VOICE_HI",
    "mr": "ELEVENLABS_VOICE_MR",
    "ta": "ELEVENLABS_VOICE_TA",
    "bn": "ELEVENLABS_VOICE_BN",
}
LEGACY_KEYS = {
    "en": "ELEVENLABS_VOICE_ID_ENGLISH",
    "hi": "ELEVENLABS_VOICE_ID_HINDI",
    "mr": "ELEVENLABS_VOICE_ID_MARATHI",
    "ta": "ELEVENLABS_VOICE_ID_TAMIL",
    "bn": "ELEVENLABS_VOICE_ID_BENGALI",
}
ALL_VOICE_KEYS = list(CANONICAL_KEYS.values()) + list(LEGACY_KEYS.values())


@pytest.fixture
def clean_voice_env(monkeypatch):
    """Start from a clean slate: no voice env vars set."""
    for key in ALL_VOICE_KEYS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


class TestResolveVoiceId:
    """_resolve_voice_id reads env at call time, canonical before legacy."""

    def test_canonical_keys_resolve(self, clean_voice_env):
        for lang, key in CANONICAL_KEYS.items():
            clean_voice_env.setenv(key, f"canonical-{lang}")
        for lang in CANONICAL_KEYS:
            assert language_service._resolve_voice_id(lang) == f"canonical-{lang}"

    def test_legacy_keys_resolve_when_canonical_absent(self, clean_voice_env):
        # Reproduces the production secret: only the ELEVENLABS_VOICE_ID_* names.
        for lang, key in LEGACY_KEYS.items():
            clean_voice_env.setenv(key, f"legacy-{lang}")
        for lang in LEGACY_KEYS:
            assert language_service._resolve_voice_id(lang) == f"legacy-{lang}"

    def test_canonical_takes_precedence_over_legacy(self, clean_voice_env):
        clean_voice_env.setenv(CANONICAL_KEYS["hi"], "canonical-hi")
        clean_voice_env.setenv(LEGACY_KEYS["hi"], "legacy-hi")
        assert language_service._resolve_voice_id("hi") == "canonical-hi"

    def test_blank_canonical_falls_through_to_legacy(self, clean_voice_env):
        clean_voice_env.setenv(CANONICAL_KEYS["ta"], "   ")  # whitespace only
        clean_voice_env.setenv(LEGACY_KEYS["ta"], "legacy-ta")
        assert language_service._resolve_voice_id("ta") == "legacy-ta"

    def test_unset_returns_empty_string(self, clean_voice_env):
        assert language_service._resolve_voice_id("bn") == ""


class TestGetVoiceId:
    """get_voice_id maps Language → distinct voice, with EN fallback."""

    def test_each_language_gets_distinct_voice(self, monkeypatch):
        voices = {"en": "v-en", "hi": "v-hi", "mr": "v-mr", "ta": "v-ta", "bn": "v-bn"}
        monkeypatch.setattr(language_service, "VOICE_MAP", voices)
        selected = [language_service.get_voice_id(lang) for lang in Language]
        assert selected == ["v-en", "v-hi", "v-mr", "v-ta", "v-bn"]
        assert len(set(selected)) == 5  # all distinct — the core WEA-65 guarantee

    def test_missing_language_voice_falls_back_to_english(self, monkeypatch):
        voices = {"en": "v-en", "hi": "", "mr": "", "ta": "", "bn": ""}
        monkeypatch.setattr(language_service, "VOICE_MAP", voices)
        assert language_service.get_voice_id(Language.MR) == "v-en"

    def test_all_unset_returns_empty_for_browser_fallback(self, monkeypatch):
        voices = {"en": "", "hi": "", "mr": "", "ta": "", "bn": ""}
        monkeypatch.setattr(language_service, "VOICE_MAP", voices)
        assert language_service.get_voice_id(Language.HI) == ""


def test_voice_map_built_from_legacy_prod_keys(clean_voice_env):
    """End-to-end: with only the production (legacy) keys set, a reimport of the
    module builds a fully-populated, distinct VOICE_MAP — proving the prod
    secret would now be read correctly."""
    for lang, key in LEGACY_KEYS.items():
        clean_voice_env.setenv(key, f"prod-{lang}")
    reloaded = importlib.reload(language_service)
    try:
        assert reloaded.VOICE_MAP == {
            "en": "prod-en", "hi": "prod-hi", "mr": "prod-mr",
            "ta": "prod-ta", "bn": "prod-bn",
        }
        assert len(set(reloaded.VOICE_MAP.values())) == 5
    finally:
        importlib.reload(language_service)  # restore module-level snapshot
