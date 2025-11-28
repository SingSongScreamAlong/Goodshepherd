"""User repository for database-backed authentication."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import UserRecord
from backend.auth.jwt import get_password_hash, verify_password


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> UserRecord:
        """Create a new user with hashed password."""
        user = UserRecord(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            name=name,
            roles=roles or ["user"],
            is_active=True,
            is_verified=False,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> Optional[UserRecord]:
        """Get a user by ID."""
        result = await self.session.execute(
            select(UserRecord).where(UserRecord.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserRecord]:
        """Get a user by email."""
        result = await self.session.execute(
            select(UserRecord).where(UserRecord.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def authenticate(self, email: str, password: str) -> Optional[UserRecord]:
        """Authenticate a user by email and password."""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.session.commit()
        
        return user

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """Update a user's password."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        await self.session.commit()
        return True

    async def verify_email(self, user_id: str) -> bool:
        """Mark a user's email as verified."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_verified = True
        await self.session.commit()
        return True

    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        roles: Optional[list[str]] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
    ) -> Optional[UserRecord]:
        """Update user fields."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        if name is not None:
            user.name = name
        if roles is not None:
            user.roles = roles
        if is_active is not None:
            user.is_active = is_active
        if is_verified is not None:
            user.is_verified = is_verified
        
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        return True

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        user = await self.get_by_email(email)
        return user is not None

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserRecord]:
        """List users with pagination."""
        result = await self.session.execute(
            select(UserRecord)
            .order_by(UserRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_users(self) -> int:
        """Count total number of users."""
        result = await self.session.execute(
            select(func.count(UserRecord.id))
        )
        return result.scalar() or 0


async def get_user_repository(session: AsyncSession) -> UserRepository:
    """Dependency to get a user repository."""
    return UserRepository(session)
