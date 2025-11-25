"""
Tests for dashboard endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import get_db, SessionLocal
from backend.models.user import User, Organization
from backend.models.event import Event
from backend.core.auth import create_access_token


client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user_and_org(db_session):
    """Create test user and organization."""
    # Create organization
    org = Organization(
        name=f"Test Org {datetime.utcnow().timestamp()}",
        description="Test organization for dashboard tests"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Create user
    user = User(
        email=f"testdashboard{datetime.utcnow().timestamp()}@test.com",
        full_name="Test Dashboard User",
        hashed_password="fakehash",
    )
    # Associate user with organization using the many-to-many relationship
    user.organizations.append(org)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user, org


@pytest.fixture
def auth_headers(test_user_and_org):
    """Create authentication headers."""
    user, org = test_user_and_org
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_summary_unauthorized():
    """Test that dashboard summary requires authentication."""
    response = client.get("/dashboard/summary")
    assert response.status_code == 401


def test_dashboard_summary(auth_headers, test_user_and_org, db_session):
    """Test dashboard summary endpoint."""
    user, org = test_user_and_org

    # Create some test events (GLOBAL - no organization_id)
    now = datetime.utcnow()
    events = [
        Event(
            timestamp=now,
            summary="Test event 1",
            category="protest",
            sentiment="neutral",
            relevance_score=0.8,
            confidence_score=0.9,
        ),
        Event(
            timestamp=now - timedelta(days=1),
            summary="Test event 2",
            category="crime",
            sentiment="negative",
            relevance_score=0.6,
            confidence_score=0.7,
        ),
    ]
    for event in events:
        db_session.add(event)
    db_session.commit()

    # Get dashboard summary
    response = client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "timestamp" in data
    assert "total_events" in data
    assert "events_today" in data
    assert "events_week" in data
    assert "events_month" in data
    assert "high_relevance_today" in data
    assert "category_distribution" in data
    assert "sentiment_distribution" in data
    assert "top_locations" in data
    assert "total_dossiers" in data
    assert "active_dossiers" in data
    assert "recent_highlights" in data

    # Check that we got at least the events we created
    assert data["events_today"] >= 1
    assert data["events_week"] >= 2


def test_dashboard_trends_unauthorized():
    """Test that dashboard trends requires authentication."""
    response = client.get("/dashboard/trends")
    assert response.status_code == 401


def test_dashboard_trends(auth_headers):
    """Test dashboard trends endpoint."""
    response = client.get("/dashboard/trends?days=7", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "period_days" in data
    assert data["period_days"] == 7
    assert "start_date" in data
    assert "end_date" in data
    assert "daily_counts" in data
    assert "category_trends" in data
    assert "sentiment_trends" in data

    # Daily counts should be a list
    assert isinstance(data["daily_counts"], list)
    # Should have 7 days of data
    assert len(data["daily_counts"]) <= 7


def test_dashboard_trends_different_periods(auth_headers):
    """Test dashboard trends with different time periods."""
    for days in [7, 14, 30]:
        response = client.get(f"/dashboard/trends?days={days}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == days


def test_dashboard_category_analysis_unauthorized():
    """Test that category analysis requires authentication."""
    response = client.get("/dashboard/category-analysis/protest")
    assert response.status_code == 401


def test_dashboard_category_analysis(auth_headers):
    """Test dashboard category analysis endpoint."""
    response = client.get("/dashboard/category-analysis/protest", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "category" in data
    assert data["category"] == "protest"
    assert "total_events" in data
    assert "events_7d" in data
    assert "events_30d" in data
    assert "avg_relevance" in data
    assert "avg_confidence" in data
    assert "sentiment_breakdown" in data
    assert "top_locations" in data
    assert "recent_events" in data


def test_dashboard_category_analysis_invalid_category(auth_headers):
    """Test category analysis with invalid category."""
    response = client.get("/dashboard/category-analysis/invalid_category", headers=auth_headers)
    # Should still return 200 with zero counts
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "invalid_category"
