"""Disinformation and misinformation detection.

Detects potential disinformation using:
- Linguistic patterns (sensationalism, emotional manipulation)
- Source credibility signals
- Claim verification indicators
- Bot/coordinated behavior patterns

This is a heuristic-based system with optional ML enhancement.
"""

import logging
import os
import pickle
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DisinfoRisk(str, Enum):
    """Disinformation risk levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class DisinfoResult:
    """Result of disinformation analysis."""
    risk_level: DisinfoRisk
    risk_score: float  # 0.0 to 1.0
    indicators: list[str] = field(default_factory=list)
    credibility_score: float = 0.5
    verification_status: str = "unverified"
    recommendations: list[str] = field(default_factory=list)
    model_version: str = "1.0"

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level.value,
            "risk_score": round(self.risk_score, 3),
            "indicators": self.indicators,
            "credibility_score": round(self.credibility_score, 3),
            "verification_status": self.verification_status,
            "recommendations": self.recommendations,
            "model_version": self.model_version,
        }


# Sensationalism indicators
SENSATIONAL_PATTERNS = [
    r"\b(shocking|unbelievable|you won't believe|mind-blowing)\b",
    r"\b(exposed|revealed|leaked|secret)\b",
    r"\b(breaking|urgent|alert|warning)\b",
    r"!{2,}",  # Multiple exclamation marks
    r"\?{2,}",  # Multiple question marks
    r"[A-Z]{5,}",  # ALL CAPS words
    r"\b(they don't want you to know|mainstream media won't tell)\b",
    r"\b(wake up|open your eyes|truth)\b",
]

# Emotional manipulation patterns
EMOTIONAL_PATTERNS = [
    r"\b(outrage|fury|anger|hate|fear|terror)\b",
    r"\b(disgusting|horrifying|terrifying|shocking)\b",
    r"\b(betrayal|conspiracy|cover-up|scandal)\b",
    r"\b(evil|corrupt|criminal|traitor)\b",
    r"\b(hero|patriot|warrior|fighter)\b",
    r"\b(destroy|annihilate|eliminate|crush)\b",
]

# Credibility red flags
CREDIBILITY_RED_FLAGS = [
    r"\b(anonymous source|sources say|reportedly)\b",
    r"\b(some people say|many believe|experts claim)\b",
    r"\b(according to rumors|unconfirmed reports)\b",
    r"\b(could be|might be|possibly|allegedly)\b",
    r"\b(no evidence but|despite no proof)\b",
    r"\b(do your own research|look it up)\b",
]

# Claim patterns that need verification
UNVERIFIED_CLAIM_PATTERNS = [
    r"\b(100%|guaranteed|proven|confirmed)\b.*\b(cure|treatment|solution)\b",
    r"\b(government|officials|they)\b.*\b(hiding|covering up|lying)\b",
    r"\b(exposed|revealed)\b.*\b(truth|secret|conspiracy)\b",
    r"\b(mainstream media|msm)\b.*\b(won't|refuse|hiding)\b",
    r"\b(big pharma|big tech|elites)\b.*\b(control|manipulate|suppress)\b",
]

# Known disinformation domains (sample - would be much larger in production)
SUSPICIOUS_DOMAINS = {
    "infowars.com",
    "naturalnews.com",
    "beforeitsnews.com",
    "yournewswire.com",
    "worldnewsdailyreport.com",
    "theonion.com",  # Satire
    "babylonbee.com",  # Satire
}

# Trusted news sources (sample)
TRUSTED_SOURCES = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "npr.org",
    "pbs.org",
    "aljazeera.com",
    "france24.com",
    "dw.com",
    "theguardian.com",
    "nytimes.com",
    "washingtonpost.com",
    "economist.com",
}

# Bot/coordinated behavior indicators
BOT_INDICATORS = [
    r"^RT @\w+:",  # Retweet pattern
    r"#\w+\s*#\w+\s*#\w+\s*#\w+",  # Excessive hashtags
    r"https?://\S+\s+https?://\S+\s+https?://\S+",  # Multiple links
    r"(\b\w+\b)(\s+\1){3,}",  # Repeated words
]


class DisinfoDetector:
    """Disinformation detection service."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("DISINFO_MODEL_PATH")
        self._classifier = None
        self._vectorizer = None
        self._model_loaded = False
        self._load_model()

        # Compile regex patterns
        self._sensational_re = [re.compile(p, re.IGNORECASE) for p in SENSATIONAL_PATTERNS]
        self._emotional_re = [re.compile(p, re.IGNORECASE) for p in EMOTIONAL_PATTERNS]
        self._credibility_re = [re.compile(p, re.IGNORECASE) for p in CREDIBILITY_RED_FLAGS]
        self._claim_re = [re.compile(p, re.IGNORECASE) for p in UNVERIFIED_CLAIM_PATTERNS]
        self._bot_re = [re.compile(p, re.IGNORECASE) for p in BOT_INDICATORS]

    def _load_model(self):
        """Load trained model if available."""
        if not self.model_path:
            return

        model_file = Path(self.model_path)
        if not model_file.exists():
            return

        try:
            with open(model_file, "rb") as f:
                data = pickle.load(f)
                self._vectorizer = data.get("vectorizer")
                self._classifier = data.get("classifier")
                self._model_loaded = True
                logger.info("Loaded disinformation detection model")
        except Exception as e:
            logger.error(f"Failed to load disinfo model: {e}")

    def analyze(
        self,
        text: str,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
        author: Optional[str] = None,
        publish_date: Optional[str] = None,
    ) -> DisinfoResult:
        """Analyze content for disinformation indicators."""
        if not text:
            return DisinfoResult(
                risk_level=DisinfoRisk.MINIMAL,
                risk_score=0.0,
                credibility_score=0.5,
            )

        indicators = []
        risk_score = 0.0

        # Check sensationalism
        sensational_count = sum(
            1 for pattern in self._sensational_re if pattern.search(text)
        )
        if sensational_count > 0:
            risk_score += min(0.2, sensational_count * 0.05)
            indicators.append(f"Sensational language ({sensational_count} patterns)")

        # Check emotional manipulation
        emotional_count = sum(
            1 for pattern in self._emotional_re if pattern.search(text)
        )
        if emotional_count > 0:
            risk_score += min(0.15, emotional_count * 0.04)
            indicators.append(f"Emotional manipulation ({emotional_count} patterns)")

        # Check credibility red flags
        credibility_flags = sum(
            1 for pattern in self._credibility_re if pattern.search(text)
        )
        if credibility_flags > 0:
            risk_score += min(0.2, credibility_flags * 0.05)
            indicators.append(f"Credibility concerns ({credibility_flags} flags)")

        # Check unverified claims
        claim_count = sum(
            1 for pattern in self._claim_re if pattern.search(text)
        )
        if claim_count > 0:
            risk_score += min(0.25, claim_count * 0.08)
            indicators.append(f"Unverified claims ({claim_count} detected)")

        # Check bot indicators
        bot_count = sum(
            1 for pattern in self._bot_re if pattern.search(text)
        )
        if bot_count > 0:
            risk_score += min(0.15, bot_count * 0.05)
            indicators.append(f"Bot-like patterns ({bot_count} detected)")

        # Check source credibility
        source_credibility = self._assess_source(source_url, source_name)
        if source_credibility < 0.3:
            risk_score += 0.2
            indicators.append("Low source credibility")
        elif source_credibility > 0.8:
            risk_score = max(0, risk_score - 0.15)

        # ML classification if available
        if self._model_loaded:
            ml_result = self._classify_ml(text)
            if ml_result:
                # Blend ML and rule-based scores
                risk_score = (risk_score * 0.4) + (ml_result["score"] * 0.6)
                if ml_result["is_disinfo"]:
                    indicators.append(f"ML classifier flagged (conf: {ml_result['confidence']:.0%})")

        # Cap score at 1.0
        risk_score = min(1.0, risk_score)

        # Determine risk level
        risk_level = self._score_to_level(risk_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(indicators, risk_level)

        # Determine verification status
        verification_status = self._determine_verification_status(
            risk_score, source_credibility, indicators
        )

        return DisinfoResult(
            risk_level=risk_level,
            risk_score=risk_score,
            indicators=indicators,
            credibility_score=source_credibility,
            verification_status=verification_status,
            recommendations=recommendations,
        )

    def _assess_source(
        self,
        source_url: Optional[str],
        source_name: Optional[str],
    ) -> float:
        """Assess source credibility."""
        if not source_url and not source_name:
            return 0.5  # Unknown

        # Extract domain from URL
        domain = None
        if source_url:
            match = re.search(r"https?://(?:www\.)?([^/]+)", source_url)
            if match:
                domain = match.group(1).lower()

        # Check against known lists
        if domain:
            if domain in SUSPICIOUS_DOMAINS:
                return 0.1
            if domain in TRUSTED_SOURCES:
                return 0.9

        # Check source name
        if source_name:
            source_lower = source_name.lower()
            if any(trusted in source_lower for trusted in ["reuters", "ap news", "bbc", "npr"]):
                return 0.85
            if any(sus in source_lower for sus in ["blog", "wordpress", "anonymous"]):
                return 0.3

        return 0.5  # Default unknown

    def _classify_ml(self, text: str) -> Optional[dict]:
        """ML-based classification."""
        if not self._model_loaded or not self._vectorizer or not self._classifier:
            return None

        try:
            features = self._vectorizer.transform([text])
            prediction = self._classifier.predict(features)[0]
            probabilities = self._classifier.predict_proba(features)[0]
            confidence = max(probabilities)

            return {
                "is_disinfo": prediction == 1,
                "score": probabilities[1] if len(probabilities) > 1 else 0.5,
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"ML classification failed: {e}")
            return None

    def _score_to_level(self, score: float) -> DisinfoRisk:
        """Convert score to risk level."""
        if score >= 0.7:
            return DisinfoRisk.HIGH
        elif score >= 0.4:
            return DisinfoRisk.MEDIUM
        elif score >= 0.2:
            return DisinfoRisk.LOW
        else:
            return DisinfoRisk.MINIMAL

    def _generate_recommendations(
        self,
        indicators: list[str],
        risk_level: DisinfoRisk,
    ) -> list[str]:
        """Generate verification recommendations."""
        recommendations = []

        if risk_level in [DisinfoRisk.HIGH, DisinfoRisk.MEDIUM]:
            recommendations.append("Cross-reference with trusted news sources")
            recommendations.append("Check original source and author credentials")

        if any("claim" in i.lower() for i in indicators):
            recommendations.append("Verify specific claims with fact-checking sites")

        if any("source" in i.lower() for i in indicators):
            recommendations.append("Research the publication's track record")

        if any("emotional" in i.lower() for i in indicators):
            recommendations.append("Look for less emotionally charged coverage")

        if risk_level == DisinfoRisk.HIGH:
            recommendations.append("Consider waiting for official confirmation")
            recommendations.append("Do not share until verified")

        return recommendations[:5]  # Limit to 5 recommendations

    def _determine_verification_status(
        self,
        risk_score: float,
        source_credibility: float,
        indicators: list[str],
    ) -> str:
        """Determine verification status."""
        if source_credibility > 0.8 and risk_score < 0.3:
            return "likely_credible"
        elif risk_score > 0.7:
            return "likely_false"
        elif risk_score > 0.4:
            return "needs_verification"
        elif source_credibility > 0.6:
            return "probably_credible"
        else:
            return "unverified"

    def analyze_batch(self, items: list[dict]) -> list[DisinfoResult]:
        """Analyze multiple items."""
        return [
            self.analyze(
                text=item.get("text", ""),
                source_url=item.get("url"),
                source_name=item.get("source"),
                author=item.get("author"),
            )
            for item in items
        ]


class DisinfoModelTrainer:
    """Train disinformation detection model."""

    def __init__(self):
        self.vectorizer = None
        self.classifier = None

    def train(
        self,
        texts: list[str],
        labels: list[int],  # 0 = credible, 1 = disinfo
        output_path: str,
    ) -> dict:
        """Train model on labeled data."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score
            from sklearn.metrics import classification_report
        except ImportError:
            raise ImportError("scikit-learn required for training")

        logger.info(f"Training disinfo model on {len(texts)} samples...")

        # Vectorize
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words="english",
        )
        X = self.vectorizer.fit_transform(texts)

        # Train
        self.classifier = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
        )
        self.classifier.fit(X, labels)

        # Evaluate
        scores = cross_val_score(self.classifier, X, labels, cv=5)
        accuracy = scores.mean()

        # Save
        model_data = {
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
            "accuracy": accuracy,
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Disinfo model saved, accuracy: {accuracy:.2%}")

        return {"accuracy": accuracy, "samples": len(texts)}


# Singleton instance
_disinfo_detector: Optional[DisinfoDetector] = None


def get_disinfo_detector() -> DisinfoDetector:
    """Get or create disinfo detector singleton."""
    global _disinfo_detector
    if _disinfo_detector is None:
        _disinfo_detector = DisinfoDetector()
    return _disinfo_detector
