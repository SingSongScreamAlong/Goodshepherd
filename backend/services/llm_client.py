"""
LLM client for AI-powered enrichment.
Provides structured interfaces for entity extraction, summarization, sentiment analysis, etc.
"""
from typing import Optional, Dict, Any, List
from openai import OpenAI
import json

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with LLM providers."""

    def __init__(self):
        """Initialize LLM client."""
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

        # Initialize OpenAI client if API key is available
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.enabled = True
            logger.info("LLM client initialized", model=self.model)
        else:
            self.client = None
            self.enabled = False
            logger.warning("LLM client disabled - no API key provided")

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Make a call to the LLM.

        Args:
            system_prompt: System instructions
            user_prompt: User message
            response_format: Optional response format specification

        Returns:
            LLM response text or None if error
        """
        if not self.enabled:
            logger.warning("LLM call attempted but client is disabled")
            return None

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Build API call parameters
            call_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            # Add response format if specified (for JSON mode)
            if response_format:
                call_params["response_format"] = response_format

            response = self.client.chat.completions.create(**call_params)

            result = response.choices[0].message.content

            logger.debug(
                "LLM call successful",
                model=self.model,
                input_length=len(user_prompt),
                output_length=len(result) if result else 0
            )

            return result

        except Exception as e:
            logger.error("LLM call failed", error=str(e), exc_info=True)
            return None

    def extract_entities(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract entities from text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with entity lists or None if error

        Expected output structure:
        {
            "locations": ["Berlin", "Mitte"],
            "organizations": ["AfD", "Police"],
            "groups": ["protesters", "residents"],
            "topics": ["immigration", "refugee policy"],
            "keywords": ["march", "police presence", "tension"]
        }
        """
        if not self.enabled:
            return self._fallback_entities()

        system_prompt = """You are an intelligence analyst extracting entities from public information.
Extract the following from the text:
- locations: Cities, neighborhoods, landmarks, countries
- organizations: Government agencies, NGOs, companies, political parties
- groups: Generic groups of people (protesters, residents, migrants, etc.)
- topics: Abstract topics and themes (immigration, policy, religion, etc.)
- keywords: Important phrases that capture the essence

Output valid JSON only. Be precise and avoid speculation."""

        user_prompt = f"""Extract entities from this text in JSON format:

Text: {text[:1500]}

Output JSON with keys: locations, organizations, groups, topics, keywords (all arrays of strings)."""

        try:
            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format={"type": "json_object"}
            )

            if response:
                entities = json.loads(response)

                # Validate structure
                required_keys = ["locations", "organizations", "groups", "topics", "keywords"]
                for key in required_keys:
                    if key not in entities:
                        entities[key] = []

                logger.info("Entities extracted", entity_count=sum(len(v) for v in entities.values()))
                return entities

        except json.JSONDecodeError as e:
            logger.error("Failed to parse entity JSON", error=str(e))
        except Exception as e:
            logger.error("Entity extraction failed", error=str(e))

        return self._fallback_entities()

    def summarize(self, text: str) -> Optional[str]:
        """
        Create a neutral 1-2 sentence summary.

        Args:
            text: Input text to summarize

        Returns:
            Summary string or None if error
        """
        if not self.enabled:
            return self._fallback_summary(text)

        system_prompt = """You are an intelligence analyst creating neutral, factual summaries.
Create a 1-2 sentence summary that captures the key facts.
- Be objective and neutral
- No speculation or interpretation
- Focus on concrete facts (who, what, where, when)
- Use clear, simple language"""

        user_prompt = f"""Summarize this text in 1-2 sentences:

{text[:2000]}"""

        try:
            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if response:
                summary = response.strip()
                logger.info("Summary generated", length=len(summary))
                return summary[:500]  # Limit to 500 chars

        except Exception as e:
            logger.error("Summarization failed", error=str(e))

        return self._fallback_summary(text)

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text.

        Args:
            text: Input text to analyze

        Returns:
            One of: "positive", "neutral", "negative"
        """
        if not self.enabled:
            return "neutral"

        system_prompt = """You are an intelligence analyst assessing sentiment.
Classify the text as: positive, neutral, or negative.
- positive: Good news, improvements, cooperation, celebration
- neutral: Factual reporting, routine events, unclear sentiment
- negative: Bad news, conflict, danger, deterioration

Output only one word: positive, neutral, or negative"""

        user_prompt = f"""Classify sentiment of this text:

{text[:1000]}

Output only: positive, neutral, or negative"""

        try:
            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if response:
                sentiment = response.strip().lower()
                if sentiment in ["positive", "neutral", "negative"]:
                    logger.info("Sentiment analyzed", sentiment=sentiment)
                    return sentiment

        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e))

        return "neutral"

    def categorize(self, text: str) -> str:
        """
        Categorize text into event category.

        Args:
            text: Input text to categorize

        Returns:
            Event category string from EventCategory enum
        """
        if not self.enabled:
            return "other"

        categories = [
            "protest", "crime", "religious_freedom", "cultural_tension",
            "political", "infrastructure", "health", "migration",
            "economic", "weather", "community_event", "other"
        ]

        system_prompt = f"""You are an intelligence analyst categorizing events.
Choose the best category from this list:
- protest: Protests, demonstrations, marches
- crime: Criminal incidents, security threats
- religious_freedom: Religious persecution, restrictions, tensions
- cultural_tension: Cultural conflicts, social tensions
- political: Political events, policy changes, elections
- infrastructure: Transport, power, communications disruptions
- health: Disease, health emergencies
- migration: Refugee/migration issues
- economic: Economic events, financial issues
- weather: Natural disasters, severe weather
- community_event: Public gatherings, celebrations
- other: Anything else

Output only the category name."""

        user_prompt = f"""Categorize this text:

{text[:1000]}

Output only one category from the list above."""

        try:
            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if response:
                category = response.strip().lower()
                if category in categories:
                    logger.info("Event categorized", category=category)
                    return category

        except Exception as e:
            logger.error("Categorization failed", error=str(e))

        return "other"

    # Fallback methods when LLM is not available

    def _fallback_entities(self) -> Dict[str, List[str]]:
        """Fallback entity extraction."""
        return {
            "locations": [],
            "organizations": [],
            "groups": [],
            "topics": [],
            "keywords": []
        }

    def _fallback_summary(self, text: str) -> str:
        """Fallback summarization - just truncate."""
        return text[:200].strip() + "..." if len(text) > 200 else text.strip()


# Global LLM client instance
llm_client = LLMClient()
