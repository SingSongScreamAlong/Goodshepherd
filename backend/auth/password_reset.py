"""Password reset and email verification token management."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr


# Token expiration settings
PASSWORD_RESET_EXPIRE_HOURS = int(os.getenv("PASSWORD_RESET_EXPIRE_HOURS", "24"))
EMAIL_VERIFICATION_EXPIRE_HOURS = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_HOURS", "48"))


class PasswordResetToken(BaseModel):
    """Password reset token data."""
    token: str
    email: str
    expires_at: datetime
    used: bool = False


class EmailVerificationToken(BaseModel):
    """Email verification token data."""
    token: str
    email: str
    expires_at: datetime
    used: bool = False


# In-memory token storage (replace with Redis/database in production)
_password_reset_tokens: dict[str, PasswordResetToken] = {}
_email_verification_tokens: dict[str, EmailVerificationToken] = {}


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token for the given email.
    
    Args:
        email: User's email address
        
    Returns:
        The generated token string
    """
    # Invalidate any existing tokens for this email
    invalidate_password_reset_tokens(email)
    
    token = generate_secure_token()
    expires_at = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    
    _password_reset_tokens[token] = PasswordResetToken(
        token=token,
        email=email.lower().strip(),
        expires_at=expires_at,
    )
    
    return token


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and return the associated email.
    
    Args:
        token: The token to verify
        
    Returns:
        The email address if valid, None otherwise
    """
    token_data = _password_reset_tokens.get(token)
    
    if not token_data:
        return None
    
    if token_data.used:
        return None
    
    if datetime.utcnow() > token_data.expires_at:
        # Token expired, clean it up
        del _password_reset_tokens[token]
        return None
    
    return token_data.email


def use_password_reset_token(token: str) -> bool:
    """
    Mark a password reset token as used.
    
    Args:
        token: The token to mark as used
        
    Returns:
        True if successful, False if token not found
    """
    token_data = _password_reset_tokens.get(token)
    
    if not token_data:
        return False
    
    token_data.used = True
    return True


def invalidate_password_reset_tokens(email: str) -> int:
    """
    Invalidate all password reset tokens for an email.
    
    Args:
        email: The email address
        
    Returns:
        Number of tokens invalidated
    """
    email = email.lower().strip()
    tokens_to_remove = [
        t for t, data in _password_reset_tokens.items()
        if data.email == email
    ]
    
    for t in tokens_to_remove:
        del _password_reset_tokens[t]
    
    return len(tokens_to_remove)


def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.
    
    Args:
        email: User's email address
        
    Returns:
        The generated token string
    """
    # Invalidate any existing tokens for this email
    invalidate_email_verification_tokens(email)
    
    token = generate_secure_token()
    expires_at = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
    
    _email_verification_tokens[token] = EmailVerificationToken(
        token=token,
        email=email.lower().strip(),
        expires_at=expires_at,
    )
    
    return token


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token and return the associated email.
    
    Args:
        token: The token to verify
        
    Returns:
        The email address if valid, None otherwise
    """
    token_data = _email_verification_tokens.get(token)
    
    if not token_data:
        return None
    
    if token_data.used:
        return None
    
    if datetime.utcnow() > token_data.expires_at:
        # Token expired, clean it up
        del _email_verification_tokens[token]
        return None
    
    return token_data.email


def use_email_verification_token(token: str) -> bool:
    """
    Mark an email verification token as used.
    
    Args:
        token: The token to mark as used
        
    Returns:
        True if successful, False if token not found
    """
    token_data = _email_verification_tokens.get(token)
    
    if not token_data:
        return False
    
    token_data.used = True
    return True


def invalidate_email_verification_tokens(email: str) -> int:
    """
    Invalidate all email verification tokens for an email.
    
    Args:
        email: The email address
        
    Returns:
        Number of tokens invalidated
    """
    email = email.lower().strip()
    tokens_to_remove = [
        t for t, data in _email_verification_tokens.items()
        if data.email == email
    ]
    
    for t in tokens_to_remove:
        del _email_verification_tokens[t]
    
    return len(tokens_to_remove)


def cleanup_expired_tokens() -> dict[str, int]:
    """
    Remove all expired tokens from storage.
    
    Returns:
        Dict with counts of removed tokens by type
    """
    now = datetime.utcnow()
    
    # Clean password reset tokens
    expired_reset = [
        t for t, data in _password_reset_tokens.items()
        if data.expires_at < now
    ]
    for t in expired_reset:
        del _password_reset_tokens[t]
    
    # Clean email verification tokens
    expired_verify = [
        t for t, data in _email_verification_tokens.items()
        if data.expires_at < now
    ]
    for t in expired_verify:
        del _email_verification_tokens[t]
    
    return {
        "password_reset": len(expired_reset),
        "email_verification": len(expired_verify),
    }
