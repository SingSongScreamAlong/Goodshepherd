"""Account lockout and brute force protection."""

import os
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
FAILED_ATTEMPT_WINDOW_MINUTES = int(os.getenv("FAILED_ATTEMPT_WINDOW_MINUTES", "15"))


@dataclass
class LoginAttempt:
    """Record of a login attempt."""
    email: str
    ip_address: Optional[str]
    timestamp: datetime
    success: bool


@dataclass
class LockoutStatus:
    """Status of account lockout."""
    is_locked: bool
    attempts_remaining: int
    lockout_expires: Optional[datetime]
    message: str


class AccountLockoutManager:
    """Manages account lockout for brute force protection."""

    def __init__(self):
        # In-memory storage (use Redis in production)
        self._failed_attempts: dict[str, list[LoginAttempt]] = {}
        self._lockouts: dict[str, datetime] = {}

    def _get_key(self, email: str, ip_address: Optional[str] = None) -> str:
        """Generate a key for tracking attempts."""
        # Track by email primarily, but could also track by IP
        return email.lower().strip()

    def _cleanup_old_attempts(self, key: str) -> None:
        """Remove attempts outside the tracking window."""
        if key not in self._failed_attempts:
            return

        cutoff = datetime.utcnow() - timedelta(minutes=FAILED_ATTEMPT_WINDOW_MINUTES)
        self._failed_attempts[key] = [
            attempt for attempt in self._failed_attempts[key]
            if attempt.timestamp > cutoff
        ]

    def record_failed_attempt(
        self,
        email: str,
        ip_address: Optional[str] = None,
    ) -> LockoutStatus:
        """Record a failed login attempt and check if account should be locked."""
        key = self._get_key(email, ip_address)
        self._cleanup_old_attempts(key)

        # Record the attempt
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=False,
        )

        if key not in self._failed_attempts:
            self._failed_attempts[key] = []
        self._failed_attempts[key].append(attempt)

        # Check if we should lock the account
        recent_failures = len(self._failed_attempts[key])

        if recent_failures >= MAX_FAILED_ATTEMPTS:
            # Lock the account
            lockout_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            self._lockouts[key] = lockout_until
            logger.warning(
                f"Account locked due to {recent_failures} failed attempts: {email}"
            )
            return LockoutStatus(
                is_locked=True,
                attempts_remaining=0,
                lockout_expires=lockout_until,
                message=f"Account locked. Try again in {LOCKOUT_DURATION_MINUTES} minutes.",
            )

        attempts_remaining = MAX_FAILED_ATTEMPTS - recent_failures
        return LockoutStatus(
            is_locked=False,
            attempts_remaining=attempts_remaining,
            lockout_expires=None,
            message=f"{attempts_remaining} attempts remaining before lockout.",
        )

    def record_successful_login(
        self,
        email: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Clear failed attempts after successful login."""
        key = self._get_key(email, ip_address)
        self._failed_attempts.pop(key, None)
        self._lockouts.pop(key, None)

    def check_lockout(
        self,
        email: str,
        ip_address: Optional[str] = None,
    ) -> LockoutStatus:
        """Check if an account is currently locked out."""
        key = self._get_key(email, ip_address)

        # Check if locked
        if key in self._lockouts:
            lockout_until = self._lockouts[key]
            if datetime.utcnow() < lockout_until:
                remaining = (lockout_until - datetime.utcnow()).seconds // 60 + 1
                return LockoutStatus(
                    is_locked=True,
                    attempts_remaining=0,
                    lockout_expires=lockout_until,
                    message=f"Account locked. Try again in {remaining} minutes.",
                )
            else:
                # Lockout expired, clear it
                self._lockouts.pop(key, None)
                self._failed_attempts.pop(key, None)

        # Not locked, calculate remaining attempts
        self._cleanup_old_attempts(key)
        recent_failures = len(self._failed_attempts.get(key, []))
        attempts_remaining = MAX_FAILED_ATTEMPTS - recent_failures

        return LockoutStatus(
            is_locked=False,
            attempts_remaining=attempts_remaining,
            lockout_expires=None,
            message="Account not locked.",
        )

    def unlock_account(self, email: str) -> bool:
        """Manually unlock an account (admin function)."""
        key = self._get_key(email)
        was_locked = key in self._lockouts
        self._lockouts.pop(key, None)
        self._failed_attempts.pop(key, None)
        if was_locked:
            logger.info(f"Account manually unlocked: {email}")
        return was_locked

    def get_failed_attempts_count(
        self,
        email: str,
        ip_address: Optional[str] = None,
    ) -> int:
        """Get the number of recent failed attempts."""
        key = self._get_key(email, ip_address)
        self._cleanup_old_attempts(key)
        return len(self._failed_attempts.get(key, []))


# Global instance
lockout_manager = AccountLockoutManager()
