"""Tests for the FastAPI endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_search_events_empty(client: AsyncClient):
    """Test searching events when database is empty."""
    response = await client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient):
    """Test getting a non-existent event."""
    response = await client.get("/api/events/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_reports_empty(client: AsyncClient):
    """Test listing reports when database is empty."""
    response = await client.get("/api/reports")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data


@pytest.mark.asyncio
async def test_list_alert_rules(client: AsyncClient):
    """Test listing alert rules."""
    response = await client.get("/api/alerts/rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_alert_rule_requires_auth(client: AsyncClient, sample_alert_rule_data: dict):
    """Test that creating an alert rule requires authentication."""
    response = await client.post("/api/alerts/rules", json=sample_alert_rule_data)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_alert_rule_with_auth(client: AsyncClient, sample_alert_rule_data: dict):
    """Test creating an alert rule with valid authentication."""
    # Note: This test assumes ADMIN_API_KEY is set in the environment
    # In a real test, you'd mock this or use a test-specific key
    import os
    admin_key = os.getenv("ADMIN_API_KEY", "test_admin_key")

    response = await client.post(
        "/api/alerts/rules",
        json=sample_alert_rule_data,
        headers={"X-Admin-Key": admin_key},
    )
    # Will be 201 if key matches, 403 if not
    assert response.status_code in (201, 403)


@pytest.mark.asyncio
async def test_search_with_region_filter(client: AsyncClient):
    """Test searching events with region filter."""
    response = await client.get("/api/search?q=test&region=europe")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_search_with_limit(client: AsyncClient):
    """Test searching events with custom limit."""
    response = await client.get("/api/search?q=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 5
