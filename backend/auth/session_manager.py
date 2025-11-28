"""Session management with refresh token rotation."""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Configuration
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))


@dataclass
class Session:
    """Represents an active user session."""
    session_id: str
    user_id: str
    refresh_token_hash: str
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_name: Optional[str] = None
    is_revoked: bool = False


@dataclass
class TokenRotationResult:
    """Result of a token rotation operation."""
    success: bool
    new_refresh_token: Optional[str] = None
    session: Optional[Session] = None
    error: Optional[str] = None


class SessionManager:
    """Manages user sessions with refresh token rotation."""

    def __init__(self):
        # In-memory storage (use Redis/database in production)
        self._sessions: dict[str, Session] = {}  # session_id -> Session
        self._user_sessions: dict[str, list[str]] = {}  # user_id -> [session_ids]
        self._token_to_session: dict[str, str] = {}  # token_hash -> session_id

    def _hash_token(self, token: str) -> str:
        """Hash a refresh token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return secrets.token_urlsafe(32)

    def _generate_refresh_token(self) -> str:
        """Generate a new refresh token."""
        return secrets.token_urlsafe(64)

    def _parse_user_agent(self, user_agent: Optional[str]) -> str:
        """Extract device name from user agent."""
        if not user_agent:
            return "Unknown Device"
        
        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            if "iphone" in ua_lower:
                return "iPhone"
            elif "android" in ua_lower:
                return "Android Device"
            return "Mobile Device"
        elif "mac" in ua_lower:
            return "Mac"
        elif "windows" in ua_lower:
            return "Windows PC"
        elif "linux" in ua_lower:
            return "Linux"
        return "Web Browser"

    def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[Session, str]:
        """
        Create a new session for a user.
        Returns the session and the refresh token.
        """
        # Enforce max sessions per user
        self._enforce_session_limit(user_id)

        session_id = self._generate_session_id()
        refresh_token = self._generate_refresh_token()
        token_hash = self._hash_token(refresh_token)
        now = datetime.utcnow()

        session = Session(
            session_id=session_id,
            user_id=user_id,
            refresh_token_hash=token_hash,
            created_at=now,
            last_used_at=now,
            expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=self._parse_user_agent(user_agent),
        )

        # Store session
        self._sessions[session_id] = session
        self._token_to_session[token_hash] = session_id

        # Track user sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)

        logger.info(f"Created session {session_id} for user {user_id}")
        return session, refresh_token

    def _enforce_session_limit(self, user_id: str) -> None:
        """Remove oldest sessions if user exceeds limit."""
        if user_id not in self._user_sessions:
            return

        user_session_ids = self._user_sessions[user_id]
        active_sessions = [
            self._sessions[sid] for sid in user_session_ids
            if sid in self._sessions and not self._sessions[sid].is_revoked
        ]

        if len(active_sessions) >= MAX_SESSIONS_PER_USER:
            # Sort by last_used_at and remove oldest
            active_sessions.sort(key=lambda s: s.last_used_at)
            sessions_to_remove = active_sessions[:len(active_sessions) - MAX_SESSIONS_PER_USER + 1]
            
            for session in sessions_to_remove:
                self.revoke_session(session.session_id)
                logger.info(f"Auto-revoked old session {session.session_id} for user {user_id}")

    def rotate_refresh_token(
        self,
        old_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenRotationResult:
        """
        Rotate a refresh token - invalidate old one and issue new one.
        This is the key security feature for refresh token rotation.
        """
        old_token_hash = self._hash_token(old_refresh_token)

        # Find session by token
        session_id = self._token_to_session.get(old_token_hash)
        if not session_id:
            logger.warning("Token rotation failed: token not found")
            return TokenRotationResult(
                success=False,
                error="Invalid refresh token",
            )

        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Token rotation failed: session {session_id} not found")
            return TokenRotationResult(
                success=False,
                error="Session not found",
            )

        # Check if session is revoked
        if session.is_revoked:
            logger.warning(f"Token rotation failed: session {session_id} is revoked")
            # Potential token reuse attack - revoke all user sessions
            self._handle_potential_token_reuse(session.user_id)
            return TokenRotationResult(
                success=False,
                error="Session has been revoked. Please login again.",
            )

        # Check if session is expired
        if datetime.utcnow() > session.expires_at:
            logger.warning(f"Token rotation failed: session {session_id} expired")
            self.revoke_session(session_id)
            return TokenRotationResult(
                success=False,
                error="Session expired. Please login again.",
            )

        # Generate new refresh token
        new_refresh_token = self._generate_refresh_token()
        new_token_hash = self._hash_token(new_refresh_token)

        # Remove old token mapping
        del self._token_to_session[old_token_hash]

        # Update session with new token
        session.refresh_token_hash = new_token_hash
        session.last_used_at = datetime.utcnow()
        if ip_address:
            session.ip_address = ip_address
        if user_agent:
            session.user_agent = user_agent
            session.device_name = self._parse_user_agent(user_agent)

        # Add new token mapping
        self._token_to_session[new_token_hash] = session_id

        logger.info(f"Rotated refresh token for session {session_id}")
        return TokenRotationResult(
            success=True,
            new_refresh_token=new_refresh_token,
            session=session,
        )

    def _handle_potential_token_reuse(self, user_id: str) -> None:
        """
        Handle potential token reuse attack by revoking all user sessions.
        This is triggered when someone tries to use an already-rotated token.
        """
        logger.warning(f"Potential token reuse detected for user {user_id}. Revoking all sessions.")
        self.revoke_all_user_sessions(user_id)

    def validate_refresh_token(self, refresh_token: str) -> Optional[Session]:
        """Validate a refresh token and return the session if valid."""
        token_hash = self._hash_token(refresh_token)
        session_id = self._token_to_session.get(token_hash)
        
        if not session_id:
            return None

        session = self._sessions.get(session_id)
        if not session or session.is_revoked:
            return None

        if datetime.utcnow() > session.expires_at:
            self.revoke_session(session_id)
            return None

        return session

    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.is_revoked = True
        
        # Remove token mapping
        if session.refresh_token_hash in self._token_to_session:
            del self._token_to_session[session.refresh_token_hash]

        logger.info(f"Revoked session {session_id}")
        return True

    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user. Returns count of revoked sessions."""
        if user_id not in self._user_sessions:
            return 0

        count = 0
        for session_id in self._user_sessions[user_id]:
            if self.revoke_session(session_id):
                count += 1

        logger.info(f"Revoked {count} sessions for user {user_id}")
        return count

    def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user."""
        if user_id not in self._user_sessions:
            return []

        sessions = []
        for session_id in self._user_sessions[user_id]:
            session = self._sessions.get(session_id)
            if session and not session.is_revoked and datetime.utcnow() < session.expires_at:
                sessions.append(session)

        # Sort by last_used_at descending
        sessions.sort(key=lambda s: s.last_used_at, reverse=True)
        return sessions

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID."""
        session = self._sessions.get(session_id)
        if session and not session.is_revoked and datetime.utcnow() < session.expires_at:
            return session
        return None

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count of cleaned sessions."""
        now = datetime.utcnow()
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.expires_at < now or session.is_revoked
        ]

        for session_id in expired_ids:
            session = self._sessions.pop(session_id, None)
            if session:
                self._token_to_session.pop(session.refresh_token_hash, None)
                if session.user_id in self._user_sessions:
                    self._user_sessions[session.user_id] = [
                        sid for sid in self._user_sessions[session.user_id]
                        if sid != session_id
                    ]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
        return len(expired_ids)


# Global instance
session_manager = SessionManager()
