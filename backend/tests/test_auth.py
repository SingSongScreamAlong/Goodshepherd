"""Tests for JWT authentication endpoints."""

import os
# Set environment variables BEFORE importing app
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["OTEL_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"

import uuid
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from backend.processing.api_main import app, limiter, get_session
from backend.auth.jwt import get_password_hash


# In-memory user storage for tests
_test_users: dict[str, dict] = {}


class MockUserRecord:
    """Mock user record for testing."""
    def __init__(self, id: str, email: str, hashed_password: str, name: Optional[str] = None,
                 roles: list = None, is_active: bool = True, is_verified: bool = False):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.name = name
        self.roles = roles or ["user"]
        self.is_active = is_active
        self.is_verified = is_verified
        self.last_login = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class MockUserRepository:
    """Mock user repository for testing."""
    
    def __init__(self, session):
        self.session = session
    
    async def create_user(self, email: str, password: str, name: Optional[str] = None,
                          roles: Optional[list] = None) -> MockUserRecord:
        user_id = str(uuid.uuid4())
        user = MockUserRecord(
            id=user_id,
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            name=name,
            roles=roles or ["user"],
        )
        _test_users[email.lower().strip()] = user
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[MockUserRecord]:
        for user in _test_users.values():
            if user.id == user_id:
                return user
        return None
    
    async def get_by_email(self, email: str) -> Optional[MockUserRecord]:
        return _test_users.get(email.lower().strip())
    
    async def authenticate(self, email: str, password: str) -> Optional[MockUserRecord]:
        from backend.auth.jwt import verify_password
        user = await self.get_by_email(email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        user.last_login = datetime.utcnow()
        return user
    
    async def email_exists(self, email: str) -> bool:
        return email.lower().strip() in _test_users

    async def update_password(self, user_id: str, new_password: str) -> bool:
        for user in _test_users.values():
            if user.id == user_id:
                user.hashed_password = get_password_hash(new_password)
                return True
        return False

    async def verify_email(self, user_id: str) -> bool:
        for user in _test_users.values():
            if user.id == user_id:
                user.is_verified = True
                return True
        return False


# Patch UserRepository in api_main
import backend.processing.api_main as api_main_module
_original_user_repository = api_main_module.UserRepository


async def mock_get_session():
    """Mock session that yields a MagicMock."""
    yield MagicMock()


@pytest.fixture
async def client():
    """Create an async HTTP client for testing."""
    # Clear test users
    _test_users.clear()
    
    # Patch UserRepository
    api_main_module.UserRepository = MockUserRepository
    
    # Override session dependency
    app.dependency_overrides[get_session] = mock_get_session
    
    # Reset rate limiter state
    limiter.reset()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Restore original
    api_main_module.UserRepository = _original_user_repository
    app.dependency_overrides.clear()
    _test_users.clear()


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client):
        """Test user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
                "name": "Test User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "user" in data["roles"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        # Register first user
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )

        # Try to register again
        response = await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "different123"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """Test successful login."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )

        # Login
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client):
        """Test login with wrong password."""
        # Register user
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )

        # Try to login with wrong password
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client):
        """Test getting current user info with valid token."""
        # Register and login
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123", "name": "Test"},
        )
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client):
        """Test getting current user without token fails."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client):
        """Test token refresh."""
        # Register and login
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Refresh token using the new endpoint format
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data  # New refresh token due to rotation
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_invalid_token(self, client):
        """Test request with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401


class TestPasswordReset:
    """Tests for password reset functionality."""

    @pytest.mark.asyncio
    async def test_request_password_reset(self, client):
        """Test requesting a password reset."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )

        # Request password reset
        response = await client.post(
            "/api/auth/password-reset/request",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_email(self, client):
        """Test password reset request for non-existent email (should not reveal)."""
        response = await client.post(
            "/api/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
        )

        # Should return success to prevent email enumeration
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password(self, client):
        """Test changing password for authenticated user."""
        # Register and login
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "oldpassword123"},
        )
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "oldpassword123"},
        )
        token = login_response.json()["access_token"]

        # Change password
        response = await client.post(
            "/api/auth/change-password",
            json={"current_password": "oldpassword123", "new_password": "newpassword456"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        # Verify new password works
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "newpassword456"},
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client):
        """Test changing password with wrong current password."""
        # Register and login
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = login_response.json()["access_token"]

        # Try to change with wrong current password
        response = await client.post(
            "/api/auth/change-password",
            json={"current_password": "wrongpassword", "new_password": "newpassword456"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()


class TestEmailVerification:
    """Tests for email verification functionality."""

    @pytest.mark.asyncio
    async def test_resend_verification(self, client):
        """Test resending verification email."""
        # Register and login
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = login_response.json()["access_token"]

        # Request verification email
        response = await client.post(
            "/api/auth/resend-verification",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()
