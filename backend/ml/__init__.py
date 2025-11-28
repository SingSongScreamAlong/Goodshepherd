"""Machine Learning module for Good Shepherd.

Components:
- translation: Multi-language translation service
- threat_classifier: ML-based threat scoring
- disinfo_detector: Disinformation detection
- model_service: Unified model serving API
"""

from .translation import TranslationService, TranslationConfig
from .threat_classifier import ThreatClassifier, ThreatPrediction
from .disinfo_detector import DisinfoDetector, DisinfoResult

__all__ = [
    "TranslationService",
    "TranslationConfig",
    "ThreatClassifier",
    "ThreatPrediction",
    "DisinfoDetector",
    "DisinfoResult",
]
