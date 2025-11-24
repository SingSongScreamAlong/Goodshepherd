"""
Sentiment analysis service.
Classifies text sentiment as positive, neutral, or negative.
"""
from typing import Literal

from backend.core.logging import get_logger
from backend.services.llm_client import llm_client
from backend.models.event import SentimentEnum

logger = get_logger(__name__)

SentimentType = Literal["positive", "neutral", "negative"]


class SentimentService:
    """Service for analyzing text sentiment."""

    def __init__(self):
        """Initialize sentiment service."""
        self.llm = llm_client

    def analyze(self, text: str) -> SentimentEnum:
        """
        Analyze sentiment of text.

        Args:
            text: Input text to analyze

        Returns:
            SentimentEnum value (POSITIVE, NEUTRAL, or NEGATIVE)
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for sentiment analysis")
            return SentimentEnum.NEUTRAL

        logger.info("Analyzing sentiment", text_length=len(text))

        # Use LLM for sentiment analysis
        sentiment_str = self.llm.analyze_sentiment(text)

        # Convert to enum
        sentiment = self._parse_sentiment(sentiment_str)

        logger.info("Sentiment analyzed", sentiment=sentiment.value)

        return sentiment

    def _parse_sentiment(self, sentiment_str: str) -> SentimentEnum:
        """
        Parse sentiment string to enum.

        Args:
            sentiment_str: Sentiment string ("positive", "neutral", "negative")

        Returns:
            SentimentEnum value
        """
        sentiment_lower = sentiment_str.lower().strip()

        if sentiment_lower == "positive":
            return SentimentEnum.POSITIVE
        elif sentiment_lower == "negative":
            return SentimentEnum.NEGATIVE
        else:
            return SentimentEnum.NEUTRAL


# Global service instance
sentiment_service = SentimentService()
