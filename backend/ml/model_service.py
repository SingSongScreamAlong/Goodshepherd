"""Unified ML model serving service.

Provides a single interface for all ML capabilities:
- Translation
- Threat classification
- Disinformation detection
- Event clustering (future)

Can be run as a standalone service or integrated into the main API.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

from .translation import TranslationService, TranslationResult, get_translation_service
from .threat_classifier import ThreatClassifier, ThreatPrediction, get_threat_classifier
from .disinfo_detector import DisinfoDetector, DisinfoResult, get_disinfo_detector

logger = logging.getLogger(__name__)


@dataclass
class EventAnalysis:
    """Complete ML analysis of an event."""
    event_id: Optional[str]
    original_text: str
    translated_text: str
    source_language: str
    threat: ThreatPrediction
    disinfo: DisinfoResult
    processing_time_ms: float

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "original_text": self.original_text[:500] + "..." if len(self.original_text) > 500 else self.original_text,
            "translated_text": self.translated_text[:500] + "..." if len(self.translated_text) > 500 else self.translated_text,
            "source_language": self.source_language,
            "threat": self.threat.to_dict(),
            "disinfo": self.disinfo.to_dict(),
            "processing_time_ms": round(self.processing_time_ms, 2),
        }


class ModelService:
    """Unified ML model service."""

    def __init__(
        self,
        translation_service: Optional[TranslationService] = None,
        threat_classifier: Optional[ThreatClassifier] = None,
        disinfo_detector: Optional[DisinfoDetector] = None,
    ):
        self.translation = translation_service or get_translation_service()
        self.threat = threat_classifier or get_threat_classifier()
        self.disinfo = disinfo_detector or get_disinfo_detector()
        self._initialized = False

    async def initialize(self):
        """Initialize all models."""
        if self._initialized:
            return
        
        logger.info("Initializing ML model service...")
        # Models are loaded lazily, but we can pre-warm them here
        self._initialized = True
        logger.info("ML model service ready")

    async def close(self):
        """Clean up resources."""
        await self.translation.close()

    async def analyze_event(
        self,
        text: str,
        title: Optional[str] = None,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
        source_credibility: float = 0.7,
        event_id: Optional[str] = None,
        translate: bool = True,
    ) -> EventAnalysis:
        """Perform complete ML analysis on an event."""
        import time
        start_time = time.time()

        # Translate if needed
        if translate:
            translation_result = await self.translation.translate(text)
            translated_text = translation_result.translated_text
            source_language = translation_result.source_language
        else:
            translated_text = text
            source_language = "en"

        # Classify threat
        threat_result = self.threat.classify(
            text=translated_text,
            title=title,
            source_credibility=source_credibility,
        )

        # Check for disinformation
        disinfo_result = self.disinfo.analyze(
            text=translated_text,
            source_url=source_url,
            source_name=source_name,
        )

        processing_time = (time.time() - start_time) * 1000

        return EventAnalysis(
            event_id=event_id,
            original_text=text,
            translated_text=translated_text,
            source_language=source_language,
            threat=threat_result,
            disinfo=disinfo_result,
            processing_time_ms=processing_time,
        )

    async def analyze_batch(
        self,
        events: list[dict],
        translate: bool = True,
    ) -> list[EventAnalysis]:
        """Analyze multiple events concurrently."""
        tasks = [
            self.analyze_event(
                text=event.get("text", event.get("summary", "")),
                title=event.get("title"),
                source_url=event.get("url", event.get("link")),
                source_name=event.get("source"),
                source_credibility=event.get("credibility", 0.7),
                event_id=event.get("id"),
                translate=translate,
            )
            for event in events
        ]
        return await asyncio.gather(*tasks)

    async def translate(
        self,
        text: str,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
    ) -> TranslationResult:
        """Translate text."""
        return await self.translation.translate(text, source_language, target_language)

    def classify_threat(
        self,
        text: str,
        title: Optional[str] = None,
        source_credibility: float = 0.7,
    ) -> ThreatPrediction:
        """Classify threat level."""
        return self.threat.classify(text, title, source_credibility)

    def detect_disinfo(
        self,
        text: str,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> DisinfoResult:
        """Detect disinformation."""
        return self.disinfo.analyze(text, source_url, source_name)

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "initialized": self._initialized,
            "translation": {
                "provider": self.translation.config.provider.value,
                "target_language": self.translation.config.target_language,
            },
            "threat_classifier": {
                "model_loaded": self.threat._model_loaded,
                "categories": [c.value for c in self.threat.classify("test").category.__class__],
            },
            "disinfo_detector": {
                "model_loaded": self.disinfo._model_loaded,
            },
        }


# Singleton instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get or create model service singleton."""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service


async def init_model_service() -> ModelService:
    """Initialize and return model service."""
    service = get_model_service()
    await service.initialize()
    return service
