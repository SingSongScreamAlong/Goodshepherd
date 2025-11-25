"""
Shared dependencies for FastAPI routes.
Provides authentication and authorization utilities.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import decode_access_token
from backend.models.user import User, Organization

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def get_current_organization(
    current_user: Annotated[User, Depends(get_current_user)]
) -> Organization:
    """
    Get the current user's active organization.

    For now, uses the first organization in the user's organizations list.
    Future enhancement: Allow users to select which org context they're in.

    Args:
        current_user: Current authenticated user

    Returns:
        Organization object

    Raises:
        HTTPException: If user not associated with any organization
    """
    if not current_user.organizations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any organization. Please contact your administrator."
        )

    # For now, use first organization
    # TODO: Future enhancement - allow user to switch between organizations
    return current_user.organizations[0]


def get_current_org_id(
    organization: Annotated[Organization, Depends(get_current_organization)]
) -> UUID:
    """
    Get the current user's organization ID.

    Convenience dependency for endpoints that just need the org ID.

    Args:
        organization: Current organization

    Returns:
        Organization UUID
    """
    return organization.id
