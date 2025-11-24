"""
User model for authentication and authorization.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from backend.core.database import Base


class RoleEnum(str, enum.Enum):
    """User roles within an organization."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


# Association table for many-to-many relationship between users and organizations
user_organization = Table(
    'user_organization',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('organization_id', UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True),
    Column('role', SQLEnum(RoleEnum), nullable=False, default=RoleEnum.VIEWER),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
)


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    organizations = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Organization(Base):
    """Organization model for multi-tenancy."""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Region of interest (e.g., "Europe", "Berlin", "Vienna, Austria")
    region_of_interest = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship(
        "User",
        secondary=user_organization,
        back_populates="organizations"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
