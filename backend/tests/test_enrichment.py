"""
Test cases for enrichment services.
"""
import pytest
from backend.services.enrichment import enrichment_pipeline
from backend.services.entity_extraction import entity_extraction_service
from backend.services.summarizer import summarizer_service
from backend.services.sentiment import sentiment_service
from backend.services.categorization import categorization_service
from backend.models.event import EventCategory, SentimentEnum


def test_entity_extraction_empty_text():
    """Test entity extraction with empty text."""
    result = entity_extraction_service.extract("")
    assert result is not None
    assert "locations" in result
    assert "organizations" in result
    assert "groups" in result
    assert "topics" in result
    assert "keywords" in result


def test_entity_extraction_short_text():
    """Test entity extraction with short text."""
    result = entity_extraction_service.extract("Short")
    assert result is not None
    assert isinstance(result["locations"], list)


def test_summarizer_empty_text():
    """Test summarizer with empty text."""
    result = summarizer_service.summarize("")
    assert result == ""


def test_summarizer_short_text():
    """Test summarizer with short text."""
    text = "This is a short text."
    result = summarizer_service.summarize(text)
    assert result is not None
    assert len(result) > 0


def test_summarizer_long_text():
    """Test summarizer with long text."""
    text = "This is a much longer text. " * 100
    result = summarizer_service.summarize(text, max_length=200)
    assert result is not None
    assert len(result) <= 200


def test_sentiment_analysis_empty():
    """Test sentiment analysis with empty text."""
    result = sentiment_service.analyze("")
    assert result == SentimentEnum.NEUTRAL


def test_sentiment_analysis_returns_enum():
    """Test sentiment analysis returns proper enum."""
    text = "This is a test event about something happening."
    result = sentiment_service.analyze(text)
    assert isinstance(result, SentimentEnum)
    assert result in [SentimentEnum.POSITIVE, SentimentEnum.NEUTRAL, SentimentEnum.NEGATIVE]


def test_categorization_empty():
    """Test categorization with empty text."""
    result = categorization_service.categorize("")
    assert result == EventCategory.OTHER


def test_categorization_returns_enum():
    """Test categorization returns proper enum."""
    text = "Police reported a theft incident in the city center."
    result = categorization_service.categorize(text)
    assert isinstance(result, EventCategory)


def test_categorization_keyword_fallback():
    """Test categorization keyword fallback."""
    # Test protest keyword
    text = "Protesters gathered for a demonstration."
    result = categorization_service._keyword_categorize(text)
    assert result == EventCategory.PROTEST

    # Test crime keyword
    text = "A robbery occurred last night."
    result = categorization_service._keyword_categorize(text)
    assert result == EventCategory.CRIME

    # Test health keyword
    text = "Health officials reported a disease outbreak."
    result = categorization_service._keyword_categorize(text)
    assert result == EventCategory.HEALTH


def test_enrichment_pipeline_basic():
    """Test enrichment pipeline with basic text."""
    text = "Police reported an incident in Berlin. Several protesters gathered."

    result = enrichment_pipeline.enrich(text)

    assert result is not None
    assert "summary" in result
    assert "category" in result
    assert "sentiment" in result
    assert "entity_list" in result
    assert "confidence_score" in result
    assert "relevance_score" in result

    assert isinstance(result["category"], EventCategory)
    assert isinstance(result["sentiment"], SentimentEnum)
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert 0.0 <= result["relevance_score"] <= 1.0


def test_enrichment_pipeline_with_title():
    """Test enrichment pipeline with title."""
    title = "Major Protest in Vienna"
    text = "Thousands gathered in Vienna city center for a demonstration."

    result = enrichment_pipeline.enrich(text, title=title)

    assert result is not None
    assert len(result["summary"]) > 0


def test_enrichment_pipeline_empty_text():
    """Test enrichment pipeline with empty text."""
    result = enrichment_pipeline.enrich("")

    # Should return fallback enrichment
    assert result is not None
    assert result["category"] == EventCategory.OTHER
    assert result["sentiment"] == SentimentEnum.NEUTRAL


def test_confidence_score_calculation():
    """Test confidence score calculation."""
    # Short text, few entities
    enrichment = {
        "entity_list": {"locations": [], "organizations": [], "groups": [], "topics": [], "keywords": []},
        "category": EventCategory.OTHER
    }
    score = enrichment_pipeline._calculate_confidence(enrichment, "Short text")
    assert 0.0 <= score <= 1.0
    assert score < 0.7  # Should be lower confidence

    # Longer text, more entities
    enrichment = {
        "entity_list": {
            "locations": ["Berlin", "Vienna"],
            "organizations": ["Police", "Government"],
            "groups": ["protesters"],
            "topics": ["demonstration", "policy"],
            "keywords": ["march", "tension"]
        },
        "category": EventCategory.PROTEST
    }
    long_text = "This is a much longer text with more details. " * 20
    score = enrichment_pipeline._calculate_confidence(enrichment, long_text)
    assert 0.0 <= score <= 1.0
    assert score > 0.7  # Should be higher confidence


def test_relevance_score_calculation():
    """Test relevance score calculation."""
    # Low relevance category
    enrichment = {
        "category": EventCategory.COMMUNITY_EVENT,
        "sentiment": SentimentEnum.POSITIVE
    }
    score = enrichment_pipeline._calculate_relevance(enrichment, "Community festival")
    assert 0.0 <= score <= 1.0

    # High relevance category
    enrichment = {
        "category": EventCategory.CRIME,
        "sentiment": SentimentEnum.NEGATIVE
    }
    score = enrichment_pipeline._calculate_relevance(enrichment, "Crime incident")
    assert 0.0 <= score <= 1.0
    assert score > 0.7  # Should be high relevance for safety


def test_fallback_enrichment():
    """Test fallback enrichment."""
    result = enrichment_pipeline._fallback_enrichment("Test text", "Test title", None)

    assert result is not None
    assert result["summary"] == "Test title"
    assert result["category"] == EventCategory.OTHER
    assert result["sentiment"] == SentimentEnum.NEUTRAL
    assert result["confidence_score"] == 0.3
    assert result["relevance_score"] == 0.5
