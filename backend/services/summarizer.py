"""
Summarization service.
Creates neutral, factual summaries from text.
"""
from typing import Optional

from backend.core.logging import get_logger
from backend.services.llm_client import llm_client

logger = get_logger(__name__)


class SummarizerService:
    """Service for creating text summaries."""

    def __init__(self):
        """Initialize summarizer service."""
        self.llm = llm_client
        self.max_summary_length = 500

    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Create a neutral 1-2 sentence summary.

        Args:
            text: Input text to summarize
            max_length: Optional maximum summary length (default: 500)

        Returns:
            Summary string (up to max_length characters)
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for summarization")
            return text.strip() if text else ""

        max_len = max_length or self.max_summary_length

        logger.info("Creating summary", text_length=len(text))

        # Use LLM for summarization
        summary = self.llm.summarize(text)

        if summary:
            # Truncate if needed
            if len(summary) > max_len:
                summary = summary[:max_len].strip()
                # Try to end at sentence boundary
                last_period = summary.rfind('.')
                if last_period > max_len * 0.7:  # If period is reasonably close to end
                    summary = summary[:last_period + 1]

            logger.info("Summary created", summary_length=len(summary))
            return summary

        # Fallback: use first sentences
        logger.warning("Summarization failed, using fallback")
        return self._fallback_summary(text, max_len)

    def _fallback_summary(self, text: str, max_length: int) -> str:
        """
        Fallback summarization method.
        Simply takes first sentences up to max_length.

        Args:
            text: Input text
            max_length: Maximum length

        Returns:
            Truncated text
        """
        text_clean = text.strip()

        if len(text_clean) <= max_length:
            return text_clean

        # Truncate and try to end at sentence
        truncated = text_clean[:max_length]
        last_period = truncated.rfind('.')

        if last_period > max_length * 0.5:
            return truncated[:last_period + 1]

        return truncated + "..."


# Global service instance
summarizer_service = SummarizerService()
