"""Multi-language translation service.

Supports:
- LibreTranslate (self-hosted, free)
- Google Cloud Translation (paid, high quality)
- Fallback to language detection only

Key languages for crisis monitoring:
- Arabic (ar), French (fr), Spanish (es), Russian (ru)
- Chinese (zh), Portuguese (pt), Swahili (sw), Hindi (hi)
"""

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class TranslationProvider(str, Enum):
    """Available translation providers."""
    LIBRETRANSLATE = "libretranslate"
    GOOGLE = "google"
    NONE = "none"


@dataclass
class TranslationConfig:
    """Translation service configuration."""
    provider: TranslationProvider = TranslationProvider.LIBRETRANSLATE
    libretranslate_url: str = "http://localhost:5000"
    libretranslate_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_project_id: Optional[str] = None
    target_language: str = "en"
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    max_text_length: int = 5000
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "TranslationConfig":
        """Load configuration from environment variables."""
        provider_str = os.getenv("TRANSLATION_PROVIDER", "libretranslate").lower()
        try:
            provider = TranslationProvider(provider_str)
        except ValueError:
            provider = TranslationProvider.NONE

        return cls(
            provider=provider,
            libretranslate_url=os.getenv("LIBRETRANSLATE_URL", "http://localhost:5000"),
            libretranslate_api_key=os.getenv("LIBRETRANSLATE_API_KEY"),
            google_api_key=os.getenv("GOOGLE_TRANSLATE_API_KEY"),
            google_project_id=os.getenv("GOOGLE_PROJECT_ID"),
            target_language=os.getenv("TRANSLATION_TARGET_LANG", "en"),
            cache_enabled=os.getenv("TRANSLATION_CACHE_ENABLED", "true").lower() == "true",
            timeout_seconds=float(os.getenv("TRANSLATION_TIMEOUT", "30")),
        )


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 1.0
    provider: str = "unknown"
    cached: bool = False


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    language: str
    confidence: float
    language_name: str = ""


# Common language codes and names
LANGUAGE_NAMES = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "es": "Spanish",
    "ru": "Russian",
    "zh": "Chinese",
    "pt": "Portuguese",
    "sw": "Swahili",
    "hi": "Hindi",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "tr": "Turkish",
    "fa": "Persian",
    "ur": "Urdu",
    "he": "Hebrew",
    "uk": "Ukrainian",
    "pl": "Polish",
    "nl": "Dutch",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
}


class TranslationService:
    """Multi-provider translation service."""

    def __init__(self, config: Optional[TranslationConfig] = None):
        self.config = config or TranslationConfig.from_env()
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: dict[str, TranslationResult] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout_seconds)
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        # Use first 100 chars + hash for long texts
        text_key = text[:100] if len(text) <= 100 else f"{text[:50]}...{hash(text)}"
        return f"{source_lang}:{target_lang}:{text_key}"

    async def detect_language(self, text: str) -> LanguageDetectionResult:
        """Detect the language of text."""
        if not text or not text.strip():
            return LanguageDetectionResult(language="en", confidence=0.0)

        # Try provider-specific detection
        if self.config.provider == TranslationProvider.LIBRETRANSLATE:
            return await self._detect_libretranslate(text)
        elif self.config.provider == TranslationProvider.GOOGLE:
            return await self._detect_google(text)
        
        # Fallback to heuristic detection
        return self._detect_heuristic(text)

    async def _detect_libretranslate(self, text: str) -> LanguageDetectionResult:
        """Detect language using LibreTranslate."""
        try:
            client = await self._get_client()
            payload = {"q": text[:500]}  # Limit text for detection
            if self.config.libretranslate_api_key:
                payload["api_key"] = self.config.libretranslate_api_key

            response = await client.post(
                f"{self.config.libretranslate_url}/detect",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                result = data[0]
                lang = result.get("language", "en")
                return LanguageDetectionResult(
                    language=lang,
                    confidence=result.get("confidence", 0.5),
                    language_name=LANGUAGE_NAMES.get(lang, lang),
                )
        except Exception as e:
            logger.warning(f"LibreTranslate detection failed: {e}")

        return self._detect_heuristic(text)

    async def _detect_google(self, text: str) -> LanguageDetectionResult:
        """Detect language using Google Cloud Translation."""
        if not self.config.google_api_key:
            return self._detect_heuristic(text)

        try:
            client = await self._get_client()
            response = await client.post(
                "https://translation.googleapis.com/language/translate/v2/detect",
                params={"key": self.config.google_api_key},
                json={"q": text[:500]},
            )
            response.raise_for_status()
            data = response.json()

            detections = data.get("data", {}).get("detections", [[]])
            if detections and detections[0]:
                result = detections[0][0]
                lang = result.get("language", "en")
                return LanguageDetectionResult(
                    language=lang,
                    confidence=result.get("confidence", 0.5),
                    language_name=LANGUAGE_NAMES.get(lang, lang),
                )
        except Exception as e:
            logger.warning(f"Google detection failed: {e}")

        return self._detect_heuristic(text)

    def _detect_heuristic(self, text: str) -> LanguageDetectionResult:
        """Simple heuristic language detection based on character ranges."""
        if not text:
            return LanguageDetectionResult(language="en", confidence=0.0)

        # Count character types
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        cyrillic_chars = len(re.findall(r'[\u0400-\u04FF]', text))
        hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', text))
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
        thai_chars = len(re.findall(r'[\u0E00-\u0E7F]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
        korean_chars = len(re.findall(r'[\uAC00-\uD7AF]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))

        total = len(text)
        if total == 0:
            return LanguageDetectionResult(language="en", confidence=0.0)

        # Determine dominant script
        char_counts = [
            (arabic_chars, "ar", "Arabic"),
            (chinese_chars, "zh", "Chinese"),
            (cyrillic_chars, "ru", "Russian"),
            (hebrew_chars, "he", "Hebrew"),
            (devanagari_chars, "hi", "Hindi"),
            (thai_chars, "th", "Thai"),
            (japanese_chars, "ja", "Japanese"),
            (korean_chars, "ko", "Korean"),
            (latin_chars, "en", "English"),  # Default for Latin
        ]

        max_count, lang, name = max(char_counts, key=lambda x: x[0])
        confidence = max_count / total if total > 0 else 0.0

        return LanguageDetectionResult(
            language=lang,
            confidence=min(confidence * 2, 1.0),  # Scale up confidence
            language_name=name,
        )

    async def translate(
        self,
        text: str,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
    ) -> TranslationResult:
        """Translate text to target language."""
        target_language = target_language or self.config.target_language

        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language="en",
                target_language=target_language,
                confidence=0.0,
                provider="none",
            )

        # Truncate if too long
        if len(text) > self.config.max_text_length:
            text = text[:self.config.max_text_length] + "..."

        # Detect source language if not provided
        if not source_language:
            detection = await self.detect_language(text)
            source_language = detection.language

        # Skip if already in target language
        if source_language == target_language:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0,
                provider="passthrough",
            )

        # Check cache
        if self.config.cache_enabled:
            cache_key = self._cache_key(text, source_language, target_language)
            if cache_key in self._cache:
                result = self._cache[cache_key]
                result.cached = True
                return result

        # Translate using configured provider
        if self.config.provider == TranslationProvider.LIBRETRANSLATE:
            result = await self._translate_libretranslate(text, source_language, target_language)
        elif self.config.provider == TranslationProvider.GOOGLE:
            result = await self._translate_google(text, source_language, target_language)
        else:
            # No translation available
            result = TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.0,
                provider="none",
            )

        # Cache result
        if self.config.cache_enabled and result.confidence > 0:
            cache_key = self._cache_key(text, source_language, target_language)
            self._cache[cache_key] = result

        return result

    async def _translate_libretranslate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate using LibreTranslate."""
        try:
            client = await self._get_client()
            payload = {
                "q": text,
                "source": source_language,
                "target": target_language,
                "format": "text",
            }
            if self.config.libretranslate_api_key:
                payload["api_key"] = self.config.libretranslate_api_key

            response = await client.post(
                f"{self.config.libretranslate_url}/translate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return TranslationResult(
                original_text=text,
                translated_text=data.get("translatedText", text),
                source_language=source_language,
                target_language=target_language,
                confidence=0.9,
                provider="libretranslate",
            )
        except Exception as e:
            logger.error(f"LibreTranslate failed: {e}")
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.0,
                provider="libretranslate_error",
            )

    async def _translate_google(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate using Google Cloud Translation."""
        if not self.config.google_api_key:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.0,
                provider="google_not_configured",
            )

        try:
            client = await self._get_client()
            response = await client.post(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": self.config.google_api_key},
                json={
                    "q": text,
                    "source": source_language,
                    "target": target_language,
                    "format": "text",
                },
            )
            response.raise_for_status()
            data = response.json()

            translations = data.get("data", {}).get("translations", [])
            if translations:
                return TranslationResult(
                    original_text=text,
                    translated_text=translations[0].get("translatedText", text),
                    source_language=source_language,
                    target_language=target_language,
                    confidence=0.95,
                    provider="google",
                )
        except Exception as e:
            logger.error(f"Google Translate failed: {e}")

        return TranslationResult(
            original_text=text,
            translated_text=text,
            source_language=source_language,
            target_language=target_language,
            confidence=0.0,
            provider="google_error",
        )

    async def translate_batch(
        self,
        texts: list[str],
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
    ) -> list[TranslationResult]:
        """Translate multiple texts concurrently."""
        tasks = [
            self.translate(text, source_language, target_language)
            for text in texts
        ]
        return await asyncio.gather(*tasks)


# Singleton instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get or create translation service singleton."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
