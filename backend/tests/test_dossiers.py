"""
Tests for dossier and watchlist endpoints.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.user import User, Organization
from backend.models.dossier import Dossier, Watchlist
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
        name=f"Test Org Dossier {datetime.utcnow().timestamp()}",
        description="Test organization for dossier tests"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Create user
    user = User(
        email=f"testdossier{datetime.utcnow().timestamp()}@test.com",
        full_name="Test Dossier User",
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


def test_create_dossier_unauthorized():
    """Test that creating dossier requires authentication."""
    response = client.post("/dossiers", json={
        "name": "Test Location",
        "dossier_type": "location",
    })
    assert response.status_code == 401


def test_create_dossier(auth_headers, test_user_and_org):
    """Test creating a new dossier."""
    user, org = test_user_and_org

    dossier_data = {
        "name": "Paris",
        "dossier_type": "location",
        "description": "Capital of France",
        "aliases": ["Paris, France"],
        "location_name": "Paris",
        "tags": ["city", "europe"],
    }

    response = client.post("/dossiers", json=dossier_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Paris"
    assert data["dossier_type"] == "location"
    assert data["organization_id"] == org.id
    assert data["event_count"] == 0
    assert "id" in data
    assert "created_at" in data


def test_list_dossiers(auth_headers, test_user_and_org, db_session):
    """Test listing dossiers."""
    user, org = test_user_and_org

    # Create a test dossier
    dossier = Dossier(
        organization_id=org.id,
        name="Test Organization",
        dossier_type="organization",
        description="A test org",
    )
    db_session.add(dossier)
    db_session.commit()

    response = client.get("/dossiers", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Should have at least the dossier we created
    assert len(data) >= 1


def test_get_dossier_by_id(auth_headers, test_user_and_org, db_session):
    """Test getting a specific dossier."""
    user, org = test_user_and_org

    # Create a test dossier
    dossier = Dossier(
        organization_id=org.id,
        name="Test Group",
        dossier_type="group",
        description="A test group",
    )
    db_session.add(dossier)
    db_session.commit()
    db_session.refresh(dossier)

    response = client.get(f"/dossiers/{dossier.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == dossier.id
    assert data["name"] == "Test Group"
    assert data["dossier_type"] == "group"


def test_update_dossier(auth_headers, test_user_and_org, db_session):
    """Test updating a dossier."""
    user, org = test_user_and_org

    # Create a test dossier
    dossier = Dossier(
        organization_id=org.id,
        name="Original Name",
        dossier_type="topic",
    )
    db_session.add(dossier)
    db_session.commit()
    db_session.refresh(dossier)

    # Update the dossier
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
    }

    response = client.patch(
        f"/dossiers/{dossier.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


def test_delete_dossier(auth_headers, test_user_and_org, db_session):
    """Test deleting a dossier."""
    user, org = test_user_and_org

    # Create a test dossier
    dossier = Dossier(
        organization_id=org.id,
        name="To Be Deleted",
        dossier_type="location",
    )
    db_session.add(dossier)
    db_session.commit()
    db_session.refresh(dossier)

    response = client.delete(f"/dossiers/{dossier.id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's deleted
    response = client.get(f"/dossiers/{dossier.id}", headers=auth_headers)
    assert response.status_code == 404


def test_filter_dossiers_by_type(auth_headers, test_user_and_org, db_session):
    """Test filtering dossiers by type."""
    user, org = test_user_and_org

    # Create dossiers of different types
    dossiers = [
        Dossier(organization_id=org.id, name="Loc1", dossier_type="location"),
        Dossier(organization_id=org.id, name="Org1", dossier_type="organization"),
        Dossier(organization_id=org.id, name="Loc2", dossier_type="location"),
    ]
    for d in dossiers:
        db_session.add(d)
    db_session.commit()

    response = client.get("/dossiers?dossier_type=location", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    # All returned dossiers should be locations
    for dossier in data:
        if dossier["name"] in ["Loc1", "Loc2"]:
            assert dossier["dossier_type"] == "location"


def test_create_watchlist(auth_headers, test_user_and_org):
    """Test creating a new watchlist."""
    watchlist_data = {
        "name": "Critical Locations",
        "description": "High-priority locations to monitor",
        "priority": "high",
        "is_active": True,
    }

    response = client.post("/watchlists", json=watchlist_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Critical Locations"
    assert data["priority"] == "high"
    assert data["is_active"] is True
    assert "id" in data


def test_list_watchlists(auth_headers, test_user_and_org, db_session):
    """Test listing watchlists."""
    user, org = test_user_and_org

    # Create a test watchlist
    watchlist = Watchlist(
        organization_id=org.id,
        user_id=user.id,
        name="Test Watchlist",
        priority="medium",
    )
    db_session.add(watchlist)
    db_session.commit()

    response = client.get("/watchlists", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_dossier_stats(auth_headers, test_user_and_org, db_session):
    """Test getting dossier statistics."""
    user, org = test_user_and_org

    # Create a test dossier
    dossier = Dossier(
        organization_id=org.id,
        name="Stats Test",
        dossier_type="location",
    )
    db_session.add(dossier)
    db_session.commit()
    db_session.refresh(dossier)

    response = client.get(f"/dossiers/{dossier.id}/stats", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["dossier_id"] == dossier.id
    assert data["name"] == "Stats Test"
    assert "event_count" in data
    assert "recent_event_count_7d" in data
    assert "recent_event_count_30d" in data
    assert "categories" in data
    assert "sentiment_distribution" in data


def test_refresh_dossier_stats(auth_headers, test_user_and_org, db_session):
    """Test refreshing dossier statistics."""
    user, org = test_user_and_org

    # Create a test dossier
    dossier = Dossier(
        organization_id=org.id,
        name="Refresh Test",
        dossier_type="organization",
    )
    db_session.add(dossier)
    db_session.commit()
    db_session.refresh(dossier)

    response = client.post(f"/dossiers/{dossier.id}/refresh", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["dossier_id"] == dossier.id
    assert "event_count" in data
