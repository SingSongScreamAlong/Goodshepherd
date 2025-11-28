"""Tests for the alert rules evaluation system."""

from __future__ import annotations

from datetime import datetime, timedelta


from backend.alerts.rules import AlertPriority, AlertRule, RuleEvaluator
from backend.database.models import EventRecord


def make_event(
    *,
    title: str = "Test Event",
    region: str = "europe",
    category: str = "security",
    threat_level: str = "high",
    credibility_score: float = 0.8,
    verification_status: str = "verified",
    fetched_at: datetime | None = None,
) -> EventRecord:
    """Create a mock event record for testing."""
    record = EventRecord()
    record.id = "test-event-id"
    record.title = title
    record.region = region
    record.category = category
    record.threat_level = threat_level
    record.credibility_score = credibility_score
    record.verification_status = verification_status
    record.fetched_at = fetched_at or datetime.utcnow()
    return record


def test_rule_matches_event():
    """Test that a rule correctly matches an event."""
    rule = AlertRule(
        name="Test Rule",
        description="Test",
        regions={"europe"},
        categories={"security"},
        minimum_threat="medium",
        minimum_credibility=0.6,
        lookback_minutes=60,
        priority=AlertPriority.HIGH,
    )

    event = make_event(
        region="europe",
        category="security",
        threat_level="high",
        credibility_score=0.8,
        verification_status="verified",
    )

    evaluator = RuleEvaluator([rule])
    candidates = evaluator.evaluate([event])

    assert len(candidates) == 1
    assert candidates[0].event == event
    assert candidates[0].rule == rule


def test_rule_filters_by_region():
    """Test that rules filter by region correctly."""
    rule = AlertRule(
        name="Europe Only",
        description="Test",
        regions={"europe"},
        minimum_threat="low",
        minimum_credibility=0.0,
    )

    europe_event = make_event(region="europe")
    asia_event = make_event(region="asia")

    evaluator = RuleEvaluator([rule])

    candidates = evaluator.evaluate([europe_event])
    assert len(candidates) == 1

    candidates = evaluator.evaluate([asia_event])
    assert len(candidates) == 0


def test_rule_filters_by_threat_level():
    """Test that rules filter by minimum threat level."""
    rule = AlertRule(
        name="High Threat Only",
        description="Test",
        minimum_threat="high",
        minimum_credibility=0.0,
    )

    high_event = make_event(threat_level="high")
    medium_event = make_event(threat_level="medium")
    critical_event = make_event(threat_level="critical")

    evaluator = RuleEvaluator([rule])

    # High should match
    assert len(evaluator.evaluate([high_event])) == 1

    # Medium should not match (below threshold)
    assert len(evaluator.evaluate([medium_event])) == 0

    # Critical should match (above threshold)
    assert len(evaluator.evaluate([critical_event])) == 1


def test_rule_filters_by_credibility():
    """Test that rules filter by minimum credibility score."""
    rule = AlertRule(
        name="High Credibility",
        description="Test",
        minimum_threat="low",
        minimum_credibility=0.7,
    )

    high_cred = make_event(credibility_score=0.9)
    low_cred = make_event(credibility_score=0.5)

    evaluator = RuleEvaluator([rule])

    assert len(evaluator.evaluate([high_cred])) == 1
    assert len(evaluator.evaluate([low_cred])) == 0


def test_rule_filters_by_lookback():
    """Test that rules filter by lookback time window."""
    rule = AlertRule(
        name="Recent Only",
        description="Test",
        minimum_threat="low",
        minimum_credibility=0.0,
        lookback_minutes=60,
    )

    now = datetime.utcnow()
    recent_event = make_event(fetched_at=now - timedelta(minutes=30))
    old_event = make_event(fetched_at=now - timedelta(minutes=120))

    evaluator = RuleEvaluator([rule])

    assert len(evaluator.evaluate([recent_event], now=now)) == 1
    assert len(evaluator.evaluate([old_event], now=now)) == 0


def test_rule_filters_by_verification_status():
    """Test that rules only match verified events."""
    rule = AlertRule(
        name="Verified Only",
        description="Test",
        minimum_threat="low",
        minimum_credibility=0.0,
    )

    verified = make_event(verification_status="verified")
    pending = make_event(verification_status="pending")

    evaluator = RuleEvaluator([rule])

    assert len(evaluator.evaluate([verified])) == 1
    assert len(evaluator.evaluate([pending])) == 0


def test_multiple_rules_can_match():
    """Test that multiple rules can match the same event."""
    rule1 = AlertRule(
        name="Rule 1",
        description="Test",
        regions={"europe"},
        minimum_threat="low",
        minimum_credibility=0.0,
    )
    rule2 = AlertRule(
        name="Rule 2",
        description="Test",
        categories={"security"},
        minimum_threat="low",
        minimum_credibility=0.0,
    )

    event = make_event(region="europe", category="security")

    evaluator = RuleEvaluator([rule1, rule2])
    candidates = evaluator.evaluate([event])

    assert len(candidates) == 2
    rule_names = {c.rule.name for c in candidates}
    assert rule_names == {"Rule 1", "Rule 2"}
