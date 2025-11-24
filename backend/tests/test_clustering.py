"""
Test cases for clustering and fusion services.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.services.clustering import clustering_service
from backend.services.fusion import fusion_service
from backend.services.scoring import scoring_service
from backend.models.event import Event, EventCategory, SentimentEnum, StabilityTrend


def create_test_event(**kwargs):
    """Helper to create test event."""
    defaults = {
        "id": uuid4(),
        "timestamp": datetime.utcnow(),
        "summary": "Test event",
        "full_text": "Test event full text",
        "category": EventCategory.OTHER,
        "confidence_score": 0.5,
        "relevance_score": 0.5,
    }
    defaults.update(kwargs)
    return Event(**defaults)


def test_location_normalization():
    """Test location name normalization."""
    loc1 = "Berlin, Germany"
    loc2 = "Berlin"

    normalized1 = clustering_service._normalize_location(loc1)
    normalized2 = clustering_service._normalize_location(loc2)

    assert normalized1 == "berlin"
    assert normalized2 == "berlin"


def test_haversine_distance():
    """Test distance calculation."""
    # Berlin to Munich (approx 504 km)
    berlin_lat, berlin_lon = 52.5200, 13.4050
    munich_lat, munich_lon = 48.1351, 11.5820

    distance = clustering_service._haversine_distance(
        berlin_lat, berlin_lon,
        munich_lat, munich_lon
    )

    # Should be around 500km
    assert 480 <= distance <= 520


def test_text_similarity():
    """Test text similarity calculation."""
    text1 = "Police reported a protest in Berlin city center"
    text2 = "Police report protest Berlin city center"

    similarity = clustering_service._calculate_text_similarity(text1, text2)

    assert similarity > 0.5  # Should be similar


def test_text_similarity_different():
    """Test text similarity with different texts."""
    text1 = "Police reported a protest in Berlin"
    text2 = "Weather forecast shows rain in London"

    similarity = clustering_service._calculate_text_similarity(text1, text2)

    assert similarity < 0.3  # Should be different


def test_should_cluster_same_location():
    """Test clustering events in same location."""
    event1 = create_test_event(
        category=EventCategory.PROTEST,
        location_name="Berlin",
        full_text="Protest in Berlin with thousands of people",
        timestamp=datetime.utcnow()
    )

    event2 = create_test_event(
        category=EventCategory.PROTEST,
        location_name="Berlin",
        full_text="Large protest Berlin thousands attending",
        timestamp=datetime.utcnow()
    )

    should_cluster = clustering_service.should_cluster(event1, event2)

    assert should_cluster is True


def test_should_not_cluster_different_category():
    """Test that events with different categories don't cluster."""
    event1 = create_test_event(
        category=EventCategory.PROTEST,
        location_name="Berlin",
        timestamp=datetime.utcnow()
    )

    event2 = create_test_event(
        category=EventCategory.CRIME,
        location_name="Berlin",
        timestamp=datetime.utcnow()
    )

    should_cluster = clustering_service.should_cluster(event1, event2)

    assert should_cluster is False


def test_should_not_cluster_old_events():
    """Test that old events don't cluster."""
    event1 = create_test_event(
        category=EventCategory.PROTEST,
        location_name="Berlin",
        timestamp=datetime.utcnow()
    )

    event2 = create_test_event(
        category=EventCategory.PROTEST,
        location_name="Berlin",
        timestamp=datetime.utcnow() - timedelta(days=2)  # 48 hours ago
    )

    should_cluster = clustering_service.should_cluster(event1, event2)

    assert should_cluster is False


def test_find_clusters():
    """Test finding clusters from events."""
    now = datetime.utcnow()

    events = [
        create_test_event(
            category=EventCategory.PROTEST,
            location_name="Berlin",
            full_text="Protest in Berlin",
            timestamp=now
        ),
        create_test_event(
            category=EventCategory.PROTEST,
            location_name="Berlin",
            full_text="Large protest Berlin",
            timestamp=now
        ),
        create_test_event(
            category=EventCategory.CRIME,
            location_name="Vienna",
            full_text="Crime in Vienna",
            timestamp=now
        ),
    ]

    clusters = clustering_service.find_clusters(events)

    # Should create at least 2 clusters (Berlin protests + Vienna crime)
    assert len(clusters) >= 2


def test_scoring_relevance():
    """Test relevance scoring."""
    # High relevance event
    score = scoring_service.calculate_relevance(
        category=EventCategory.CRIME,
        sentiment=SentimentEnum.NEGATIVE,
        entity_list={"locations": ["Berlin"], "organizations": []},
        text_length=500
    )

    assert score >= 0.8  # Should be high relevance


def test_scoring_confidence():
    """Test confidence scoring."""
    score = scoring_service.calculate_confidence(
        text_length=1000,
        entity_count=10,
        has_location=True,
        has_specific_category=True,
        has_source=True
    )

    assert score >= 0.8  # Should be high confidence


def test_scoring_priority():
    """Test priority scoring."""
    # Recent, high relevance, high confidence
    score = scoring_service.calculate_priority(
        relevance=0.9,
        confidence=0.9,
        recency_hours=2,
        cluster_size=3
    )

    assert score >= 0.8  # Should be high priority


def test_fuse_single_event():
    """Test fusing a single event."""
    event = create_test_event()

    fused = fusion_service.fuse_events([event])

    assert fused["summary"] == event.summary
    assert fused["category"] == event.category


def test_fuse_multiple_events():
    """Test fusing multiple events."""
    now = datetime.utcnow()

    events = [
        create_test_event(
            summary="First report of protest",
            full_text="Protest in Berlin city center",
            category=EventCategory.PROTEST,
            sentiment=SentimentEnum.NEUTRAL,
            confidence_score=0.7,
            relevance_score=0.8,
            timestamp=now,
            source_list=[{"name": "Source A", "url": "http://a.com"}],
            entity_list={"locations": ["Berlin"], "organizations": ["Police"]}
        ),
        create_test_event(
            summary="Second report of protest",
            full_text="Large protest Berlin with thousands",
            category=EventCategory.PROTEST,
            sentiment=SentimentEnum.NEGATIVE,
            confidence_score=0.8,
            relevance_score=0.9,
            timestamp=now + timedelta(hours=1),
            source_list=[{"name": "Source B", "url": "http://b.com"}],
            entity_list={"locations": ["Berlin"], "organizations": ["Police", "City Council"]}
        ),
    ]

    fused = fusion_service.fuse_events(events)

    # Should have combined data
    assert fused["category"] == EventCategory.PROTEST
    assert len(fused["source_list"]) == 2
    assert "berlin" in fused["entity_list"]["locations"]
    assert fused["confidence_score"] >= 0.7  # Boosted by multiple sources
    assert fused["relevance_score"] >= 0.8


def test_merge_entities():
    """Test entity merging."""
    events = [
        create_test_event(
            entity_list={"locations": ["Berlin", "Mitte"], "organizations": ["Police"]}
        ),
        create_test_event(
            entity_list={"locations": ["Berlin", "Prenzlauer Berg"], "organizations": ["Fire Department"]}
        ),
    ]

    merged = fusion_service._merge_entities(events)

    assert "berlin" in merged["locations"]
    assert "mitte" in merged["locations"]
    assert "police" in merged["organizations"]
    assert "fire department" in merged["organizations"]


def test_stability_trend_assessment():
    """Test stability trend assessment."""
    # Events getting worse
    events = [
        create_test_event(sentiment=SentimentEnum.NEUTRAL, timestamp=datetime.utcnow()),
        create_test_event(sentiment=SentimentEnum.NEGATIVE, timestamp=datetime.utcnow() + timedelta(hours=1)),
    ]

    trend = fusion_service._assess_stability_trend(events)

    assert trend == StabilityTrend.DECREASING


def test_empty_clustering():
    """Test clustering with empty list."""
    clusters = clustering_service.find_clusters([])

    assert clusters == {}


def test_empty_fusion():
    """Test fusion with empty list."""
    fused = fusion_service.fuse_events([])

    assert fused == {}
