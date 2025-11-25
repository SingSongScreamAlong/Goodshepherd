"""
Tests for event feedback endpoints.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.user import User, Organization
from backend.models.event import Event
from backend.models.feedback import EventFeedback
from backend.core.security import create_access_token


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
        name=f"Test Org Feedback {datetime.utcnow().timestamp()}",
        description="Test organization for feedback tests"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Create user
    user = User(
        email=f"testfeedback{datetime.utcnow().timestamp()}@test.com",
        full_name="Test Feedback User",
        hashed_password="fakehash",
    )
    # Associate user with organization using the many-to-many relationship
    user.organizations.append(org)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user, org


@pytest.fixture
def test_event(db_session):
    """Create a test event (GLOBAL - no organization_id)."""
    event = Event(
        timestamp=datetime.utcnow(),
        summary="Test event for feedback",
        category="protest",
        sentiment="neutral",
        relevance_score=0.8,
        confidence_score=0.9,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def auth_headers(test_user_and_org):
    """Create authentication headers."""
    user, org = test_user_and_org
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_submit_feedback_unauthorized(test_event):
    """Test that feedback submission requires authentication."""
    response = client.post(
        "/feedback/event",
        json={
            "event_id": str(test_event.id),
            "feedback_type": "relevant",
            "comment": "This is relevant"
        }
    )
    assert response.status_code == 401


def test_submit_feedback_success(auth_headers, test_user_and_org, test_event, db_session):
    """Test successful feedback submission."""
    user, org = test_user_and_org

    response = client.post(
        "/feedback/event",
        headers=auth_headers,
        json={
            "event_id": str(test_event.id),
            "feedback_type": "relevant",
            "comment": "This event is highly relevant"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Feedback submitted successfully"
    assert "feedback_id" in data
    assert data["event_id"] == str(test_event.id)
    assert data["feedback_type"] == "relevant"

    # Verify feedback was stored in database
    feedback = db_session.query(EventFeedback).filter(
        EventFeedback.event_id == test_event.id
    ).first()
    assert feedback is not None
    assert feedback.user_id == user.id
    assert feedback.feedback_type == "relevant"
    assert feedback.comment == "This event is highly relevant"


def test_submit_feedback_event_not_found(auth_headers):
    """Test feedback submission for non-existent event."""
    fake_event_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        "/feedback/event",
        headers=auth_headers,
        json={
            "event_id": fake_event_id,
            "feedback_type": "relevant"
        }
    )

    assert response.status_code == 404
    assert "Event not found" in response.json()["detail"]


def test_submit_feedback_without_comment(auth_headers, test_event, db_session):
    """Test feedback submission without optional comment."""
    response = client.post(
        "/feedback/event",
        headers=auth_headers,
        json={
            "event_id": str(test_event.id),
            "feedback_type": "irrelevant"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["feedback_type"] == "irrelevant"

    # Verify in database
    feedback = db_session.query(EventFeedback).filter(
        EventFeedback.event_id == test_event.id
    ).first()
    assert feedback is not None
    assert feedback.comment is None


def test_submit_multiple_feedback_types(auth_headers, test_user_and_org, test_event, db_session):
    """Test submitting different types of feedback."""
    user, org = test_user_and_org
    feedback_types = ["relevant", "irrelevant", "misclassified", "important"]

    for feedback_type in feedback_types:
        # Create a new event for each feedback type
        event = Event(
            timestamp=datetime.utcnow(),
            summary=f"Test event for {feedback_type}",
            category="crime",
            sentiment="negative",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.post(
            "/feedback/event",
            headers=auth_headers,
            json={
                "event_id": str(event.id),
                "feedback_type": feedback_type,
                "comment": f"Testing {feedback_type} feedback"
            }
        )

        assert response.status_code == 200
        assert response.json()["feedback_type"] == feedback_type


def test_get_feedback_stats_unauthorized():
    """Test that feedback stats requires authentication."""
    response = client.get("/feedback/stats")
    assert response.status_code == 401


def test_get_feedback_stats_empty(auth_headers):
    """Test feedback stats with no feedback."""
    response = client.get("/feedback/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_feedback"] == 0
    assert "feedback_by_type" in data
    assert data["feedback_by_type"]["relevant"] == 0
    assert data["feedback_by_type"]["irrelevant"] == 0
    assert data["feedback_by_type"]["misclassified"] == 0
    assert data["feedback_by_type"]["important"] == 0


def test_get_feedback_stats_with_data(auth_headers, test_user_and_org, db_session):
    """Test feedback stats with actual feedback data."""
    user, org = test_user_and_org

    # Create multiple events with feedback
    feedback_data = [
        ("relevant", 3),
        ("irrelevant", 2),
        ("misclassified", 1),
        ("important", 4),
    ]

    for feedback_type, count in feedback_data:
        for i in range(count):
            # Create event
            event = Event(
                timestamp=datetime.utcnow(),
                summary=f"Event for {feedback_type} {i}",
                category="political",
            )
            db_session.add(event)
            db_session.flush()

            # Create feedback
            feedback = EventFeedback(
                event_id=event.id,
                user_id=user.id,
                feedback_type=feedback_type,
                comment=f"Test comment {i}"
            )
            db_session.add(feedback)

    db_session.commit()

    # Get stats
    response = client.get("/feedback/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_feedback"] == 10  # 3 + 2 + 1 + 4
    assert data["feedback_by_type"]["relevant"] == 3
    assert data["feedback_by_type"]["irrelevant"] == 2
    assert data["feedback_by_type"]["misclassified"] == 1
    assert data["feedback_by_type"]["important"] == 4
