"""Tests for the database repository functions."""

from __future__ import annotations


import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repository import (
    AlertRuleCreate,
    EventCreate,
    ReportCreate,
    create_alert_rule,
    create_event,
    create_report,
    get_event_by_id,
    list_alert_rules,
    list_recent_events,
    list_reports,
    search_events,
)


@pytest.mark.asyncio
async def test_create_event(db_session: AsyncSession, sample_event_data: dict):
    """Test creating an event."""
    event = EventCreate(**sample_event_data)
    record = await create_event(db_session, event)
    await db_session.commit()

    assert record.id is not None
    assert record.title == sample_event_data["title"]
    assert record.region == sample_event_data["region"]
    assert record.threat_level == sample_event_data["threat_level"]


@pytest.mark.asyncio
async def test_get_event_by_id(db_session: AsyncSession, sample_event_data: dict):
    """Test retrieving an event by ID."""
    event = EventCreate(**sample_event_data)
    record = await create_event(db_session, event)
    await db_session.commit()

    retrieved = await get_event_by_id(db_session, record.id)
    assert retrieved is not None
    assert retrieved.id == record.id
    assert retrieved.title == record.title


@pytest.mark.asyncio
async def test_list_recent_events(db_session: AsyncSession, sample_event_data: dict):
    """Test listing recent events."""
    # Create a few events
    for i in range(3):
        data = sample_event_data.copy()
        data["title"] = f"Event {i}"
        await create_event(db_session, EventCreate(**data))
    await db_session.commit()

    events = await list_recent_events(db_session, limit=10)
    assert len(events) >= 3


@pytest.mark.asyncio
async def test_search_events_by_query(db_session: AsyncSession, sample_event_data: dict):
    """Test searching events by query string."""
    # Create an event with specific title
    data = sample_event_data.copy()
    data["title"] = "Unique Searchable Title XYZ123"
    await create_event(db_session, EventCreate(**data))
    await db_session.commit()

    results = await search_events(db_session, query="XYZ123")
    assert len(results) >= 1
    assert any("XYZ123" in e.title for e in results)


@pytest.mark.asyncio
async def test_search_events_by_region(db_session: AsyncSession, sample_event_data: dict):
    """Test searching events by region."""
    data = sample_event_data.copy()
    data["region"] = "test-region-unique"
    await create_event(db_session, EventCreate(**data))
    await db_session.commit()

    results = await search_events(db_session, region="test-region-unique")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_create_report(db_session: AsyncSession):
    """Test creating a report."""
    report = ReportCreate(
        title="Daily SITREP",
        summary="Summary of events",
        report_type="daily_sitrep",
        region="europe",
        generated_by="test",
        content="Full report content here.",
        stats={"total_events": 10, "critical": 2},
        source_event_ids=["event-1", "event-2"],
    )
    record = await create_report(db_session, report)
    await db_session.commit()

    assert record.id is not None
    assert record.title == "Daily SITREP"
    assert record.stats["total_events"] == 10


@pytest.mark.asyncio
async def test_list_reports(db_session: AsyncSession):
    """Test listing reports."""
    # Create a report
    report = ReportCreate(
        title="Test Report",
        report_type="daily_sitrep",
    )
    await create_report(db_session, report)
    await db_session.commit()

    reports = await list_reports(db_session, limit=10)
    assert len(reports) >= 1


@pytest.mark.asyncio
async def test_create_alert_rule(db_session: AsyncSession, sample_alert_rule_data: dict):
    """Test creating an alert rule."""
    rule = AlertRuleCreate(**sample_alert_rule_data)
    record = await create_alert_rule(db_session, rule)
    await db_session.commit()

    assert record.id is not None
    assert record.name == sample_alert_rule_data["name"]
    assert record.minimum_threat == sample_alert_rule_data["minimum_threat"]


@pytest.mark.asyncio
async def test_list_alert_rules(db_session: AsyncSession, sample_alert_rule_data: dict):
    """Test listing alert rules."""
    rule = AlertRuleCreate(**sample_alert_rule_data)
    await create_alert_rule(db_session, rule)
    await db_session.commit()

    rules = await list_alert_rules(db_session)
    assert len(rules) >= 1
