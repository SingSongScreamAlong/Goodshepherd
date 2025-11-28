"""ML-based threat classification and scoring.

Uses a combination of:
- Rule-based keyword matching for known threat indicators
- TF-IDF + Logistic Regression for text classification
- Ensemble scoring with credibility weighting

Threat categories:
- conflict: Armed conflict, military action, violence
- terrorism: Terrorist attacks, extremism
- disaster: Natural disasters, accidents
- health: Disease outbreaks, health emergencies
- political: Political instability, civil unrest
- humanitarian: Refugee crises, food insecurity
"""

import json
import logging
import os
import pickle
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ThreatCategory(str, Enum):
    """Threat categories."""
    CONFLICT = "conflict"
    TERRORISM = "terrorism"
    DISASTER = "disaster"
    HEALTH = "health"
    POLITICAL = "political"
    HUMANITARIAN = "humanitarian"
    UNKNOWN = "unknown"


@dataclass
class ThreatPrediction:
    """Result of threat classification."""
    threat_level: ThreatLevel
    threat_score: float  # 0.0 to 1.0
    category: ThreatCategory
    category_confidence: float
    keywords_matched: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    model_version: str = "1.0"

    def to_dict(self) -> dict:
        return {
            "threat_level": self.threat_level.value,
            "threat_score": round(self.threat_score, 3),
            "category": self.category.value,
            "category_confidence": round(self.category_confidence, 3),
            "keywords_matched": self.keywords_matched,
            "risk_factors": self.risk_factors,
            "model_version": self.model_version,
        }


# Threat indicator keywords by category
THREAT_KEYWORDS = {
    ThreatCategory.CONFLICT: {
        "critical": [
            "war declared", "invasion", "military offensive", "mass casualties",
            "genocide", "ethnic cleansing", "chemical weapons", "nuclear",
        ],
        "high": [
            "armed conflict", "military strike", "airstrikes", "bombing",
            "shelling", "artillery", "troops deployed", "combat",
            "firefight", "battle", "offensive", "counteroffensive",
        ],
        "medium": [
            "clashes", "skirmish", "gunfire", "shooting", "violence",
            "militants", "insurgents", "rebels", "armed groups",
        ],
        "low": [
            "tensions", "standoff", "military exercises", "border dispute",
        ],
    },
    ThreatCategory.TERRORISM: {
        "critical": [
            "terrorist attack", "suicide bombing", "mass shooting",
            "hostage situation", "bomb explosion", "terror attack",
        ],
        "high": [
            "explosion", "bombing", "ied", "car bomb", "attack claimed",
            "isis", "al-qaeda", "boko haram", "al-shabaab",
        ],
        "medium": [
            "threat warning", "security alert", "suspicious package",
            "extremist", "radicalization", "terror plot",
        ],
        "low": [
            "security increased", "threat level raised", "vigilance",
        ],
    },
    ThreatCategory.DISASTER: {
        "critical": [
            "earthquake magnitude 7", "earthquake magnitude 8", "tsunami",
            "category 5 hurricane", "major flood", "volcanic eruption",
            "nuclear accident", "dam collapse",
        ],
        "high": [
            "earthquake", "hurricane", "typhoon", "cyclone", "flood",
            "wildfire", "tornado", "landslide", "avalanche",
        ],
        "medium": [
            "storm", "heavy rain", "flooding", "fire", "drought",
            "heatwave", "cold wave", "severe weather",
        ],
        "low": [
            "weather warning", "advisory", "watch issued",
        ],
    },
    ThreatCategory.HEALTH: {
        "critical": [
            "pandemic", "epidemic outbreak", "ebola", "plague",
            "mass infection", "quarantine zone", "health emergency",
        ],
        "high": [
            "outbreak", "disease spread", "cholera", "measles",
            "dengue", "malaria surge", "hospital overwhelmed",
        ],
        "medium": [
            "cases reported", "infection", "virus", "disease",
            "health alert", "vaccination campaign",
        ],
        "low": [
            "health advisory", "precautions", "monitoring",
        ],
    },
    ThreatCategory.POLITICAL: {
        "critical": [
            "coup", "government overthrown", "martial law",
            "state of emergency", "civil war",
        ],
        "high": [
            "protests violent", "riots", "uprising", "revolution",
            "government collapse", "political crisis",
        ],
        "medium": [
            "protests", "demonstrations", "unrest", "strikes",
            "political tension", "opposition arrested",
        ],
        "low": [
            "election", "political dispute", "controversy",
        ],
    },
    ThreatCategory.HUMANITARIAN: {
        "critical": [
            "famine", "mass displacement", "refugee crisis",
            "humanitarian catastrophe", "starvation",
        ],
        "high": [
            "refugees", "displaced persons", "food shortage",
            "aid blocked", "humanitarian access denied",
        ],
        "medium": [
            "aid needed", "humanitarian situation", "food insecurity",
            "shelter needed", "medical supplies",
        ],
        "low": [
            "aid delivered", "humanitarian response", "relief efforts",
        ],
    },
}

# Risk amplifiers
RISK_AMPLIFIERS = {
    "civilian casualties": 0.15,
    "children": 0.1,
    "hospital": 0.1,
    "school": 0.1,
    "market": 0.08,
    "mosque": 0.08,
    "church": 0.08,
    "temple": 0.08,
    "refugee camp": 0.12,
    "aid workers": 0.1,
    "journalists": 0.08,
    "un personnel": 0.1,
    "peacekeepers": 0.1,
    "embassy": 0.1,
    "capital city": 0.08,
    "international": 0.05,
    "spreading": 0.1,
    "escalating": 0.1,
    "worsening": 0.08,
    "unprecedented": 0.08,
    "worst in years": 0.1,
    "death toll rising": 0.12,
    "confirmed dead": 0.1,
    "missing": 0.08,
    "trapped": 0.1,
}


class ThreatClassifier:
    """ML-based threat classifier with rule-based fallback."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("THREAT_MODEL_PATH")
        self._vectorizer = None
        self._classifier = None
        self._model_loaded = False
        self._load_model()

    def _load_model(self):
        """Load trained model if available."""
        if not self.model_path:
            logger.info("No model path configured, using rule-based classification")
            return

        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.info(f"Model file not found at {self.model_path}, using rule-based")
            return

        try:
            with open(model_file, "rb") as f:
                data = pickle.load(f)
                self._vectorizer = data.get("vectorizer")
                self._classifier = data.get("classifier")
                self._model_loaded = True
                logger.info("Loaded threat classification model")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def classify(
        self,
        text: str,
        title: Optional[str] = None,
        source_credibility: float = 0.7,
        region: Optional[str] = None,
    ) -> ThreatPrediction:
        """Classify threat level and category from text."""
        if not text:
            return ThreatPrediction(
                threat_level=ThreatLevel.MINIMAL,
                threat_score=0.0,
                category=ThreatCategory.UNKNOWN,
                category_confidence=0.0,
            )

        # Combine title and text
        full_text = f"{title or ''} {text}".lower()

        # Rule-based classification
        rule_result = self._classify_rules(full_text)

        # ML classification if model loaded
        ml_result = None
        if self._model_loaded:
            ml_result = self._classify_ml(full_text)

        # Ensemble results
        if ml_result:
            # Weight: 60% ML, 40% rules
            combined_score = (ml_result["score"] * 0.6) + (rule_result["score"] * 0.4)
            # Use ML category if confident, else rules
            if ml_result["confidence"] > 0.7:
                category = ml_result["category"]
                category_confidence = ml_result["confidence"]
            else:
                category = rule_result["category"]
                category_confidence = rule_result["confidence"]
        else:
            combined_score = rule_result["score"]
            category = rule_result["category"]
            category_confidence = rule_result["confidence"]

        # Apply source credibility weighting
        weighted_score = combined_score * (0.5 + source_credibility * 0.5)

        # Apply risk amplifiers
        risk_factors = []
        for factor, boost in RISK_AMPLIFIERS.items():
            if factor in full_text:
                weighted_score = min(1.0, weighted_score + boost)
                risk_factors.append(factor)

        # Determine threat level
        threat_level = self._score_to_level(weighted_score)

        return ThreatPrediction(
            threat_level=threat_level,
            threat_score=weighted_score,
            category=category,
            category_confidence=category_confidence,
            keywords_matched=rule_result["keywords"],
            risk_factors=risk_factors,
        )

    def _classify_rules(self, text: str) -> dict:
        """Rule-based classification using keyword matching."""
        best_category = ThreatCategory.UNKNOWN
        best_score = 0.0
        best_confidence = 0.0
        matched_keywords = []

        for category, levels in THREAT_KEYWORDS.items():
            category_score = 0.0
            category_keywords = []

            for level, keywords in levels.items():
                level_weight = {
                    "critical": 1.0,
                    "high": 0.75,
                    "medium": 0.5,
                    "low": 0.25,
                }[level]

                for keyword in keywords:
                    if keyword in text:
                        category_score = max(category_score, level_weight)
                        category_keywords.append(keyword)

            if category_score > best_score:
                best_score = category_score
                best_category = category
                best_confidence = min(0.9, 0.5 + len(category_keywords) * 0.1)
                matched_keywords = category_keywords

        return {
            "category": best_category,
            "score": best_score,
            "confidence": best_confidence,
            "keywords": matched_keywords[:10],  # Limit to top 10
        }

    def _classify_ml(self, text: str) -> Optional[dict]:
        """ML-based classification using trained model."""
        if not self._model_loaded or not self._vectorizer or not self._classifier:
            return None

        try:
            # Vectorize text
            features = self._vectorizer.transform([text])

            # Predict category
            prediction = self._classifier.predict(features)[0]
            probabilities = self._classifier.predict_proba(features)[0]

            # Get confidence
            max_prob = max(probabilities)
            category = ThreatCategory(prediction)

            # Estimate threat score from probability distribution
            score = max_prob * 0.8  # Scale down slightly

            return {
                "category": category,
                "score": score,
                "confidence": max_prob,
            }
        except Exception as e:
            logger.error(f"ML classification failed: {e}")
            return None

    def _score_to_level(self, score: float) -> ThreatLevel:
        """Convert numeric score to threat level."""
        if score >= 0.85:
            return ThreatLevel.CRITICAL
        elif score >= 0.65:
            return ThreatLevel.HIGH
        elif score >= 0.4:
            return ThreatLevel.MEDIUM
        elif score >= 0.2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.MINIMAL

    def classify_batch(
        self,
        items: list[dict],
        text_field: str = "text",
        title_field: str = "title",
    ) -> list[ThreatPrediction]:
        """Classify multiple items."""
        return [
            self.classify(
                text=item.get(text_field, ""),
                title=item.get(title_field),
                source_credibility=item.get("credibility", 0.7),
                region=item.get("region"),
            )
            for item in items
        ]


class ThreatModelTrainer:
    """Train threat classification model from labeled data."""

    def __init__(self):
        self.vectorizer = None
        self.classifier = None

    def train(
        self,
        texts: list[str],
        labels: list[str],
        output_path: str,
    ) -> dict:
        """Train model on labeled data."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score
        except ImportError:
            raise ImportError("scikit-learn required for training. Install with: pip install scikit-learn")

        logger.info(f"Training on {len(texts)} samples...")

        # Vectorize
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
        )
        X = self.vectorizer.fit_transform(texts)

        # Train classifier
        self.classifier = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            multi_class="multinomial",
        )
        self.classifier.fit(X, labels)

        # Evaluate
        scores = cross_val_score(self.classifier, X, labels, cv=5)
        accuracy = scores.mean()

        # Save model
        model_data = {
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
            "accuracy": accuracy,
            "classes": list(self.classifier.classes_),
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {output_path}, accuracy: {accuracy:.2%}")

        return {
            "accuracy": accuracy,
            "classes": list(self.classifier.classes_),
            "samples": len(texts),
        }


# Singleton instance
_threat_classifier: Optional[ThreatClassifier] = None


def get_threat_classifier() -> ThreatClassifier:
    """Get or create threat classifier singleton."""
    global _threat_classifier
    if _threat_classifier is None:
        _threat_classifier = ThreatClassifier()
    return _threat_classifier
