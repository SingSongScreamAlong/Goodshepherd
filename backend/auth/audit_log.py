"""Audit logging for security-related events."""

import logging
import json
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    USER_REGISTERED = "user.registered"
    USER_LOGIN_SUCCESS = "user.login.success"
    USER_LOGIN_FAILED = "user.login.failed"
    USER_LOGOUT = "user.logout"
    TOKEN_REFRESHED = "token.refreshed"
    
    # Password events
    PASSWORD_CHANGED = "password.changed"
    PASSWORD_RESET_REQUESTED = "password.reset.requested"
    PASSWORD_RESET_COMPLETED = "password.reset.completed"
    PASSWORD_RESET_FAILED = "password.reset.failed"
    
    # Email verification events
    EMAIL_VERIFICATION_SENT = "email.verification.sent"
    EMAIL_VERIFIED = "email.verified"
    EMAIL_VERIFICATION_FAILED = "email.verification.failed"
    
    # Account events
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_DEACTIVATED = "account.deactivated"
    ACCOUNT_REACTIVATED = "account.reactivated"
    ACCOUNT_DELETED = "account.deleted"
    
    # Admin events
    ADMIN_USER_CREATED = "admin.user.created"
    ADMIN_USER_UPDATED = "admin.user.updated"
    ADMIN_USER_DELETED = "admin.user.deleted"
    ADMIN_ROLE_CHANGED = "admin.role.changed"
    
    # Session events
    SESSION_CREATED = "session.created"
    SESSION_REVOKED = "session.revoked"
    ALL_SESSIONS_REVOKED = "session.all_revoked"
    LOGOUT = "user.logout"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    INVALID_TOKEN = "security.invalid_token"
    UNAUTHORIZED_ACCESS = "security.unauthorized"
    TOKEN_REUSE_DETECTED = "security.token_reuse"


@dataclass
class AuditEvent:
    """Represents an audit log event."""
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    status: str = "success"
    details: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Logger for security audit events."""
    
    def __init__(self):
        self._events: list[AuditEvent] = []
        self._max_in_memory = 1000  # Keep last 1000 events in memory
    
    def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            status=status,
            details=details,
        )
        
        # Log to standard logger
        log_level = logging.WARNING if status == "failure" else logging.INFO
        logger.log(log_level, event.to_json())
        
        # Store in memory (for recent events API)
        self._events.append(event)
        if len(self._events) > self._max_in_memory:
            self._events = self._events[-self._max_in_memory:]
        
        return event
    
    def log_login_success(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """Log successful login."""
        return self.log(
            event_type=AuditEventType.USER_LOGIN_SUCCESS,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login",
        )
    
    def log_login_failed(
        self,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> AuditEvent:
        """Log failed login attempt."""
        return self.log(
            event_type=AuditEventType.USER_LOGIN_FAILED,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login",
            status="failure",
            details={"reason": reason} if reason else None,
        )
    
    def log_registration(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log user registration."""
        return self.log(
            event_type=AuditEventType.USER_REGISTERED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action="register",
        )
    
    def log_password_change(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log password change."""
        return self.log(
            event_type=AuditEventType.PASSWORD_CHANGED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action="password_change",
        )
    
    def log_password_reset_request(
        self,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log password reset request."""
        return self.log(
            event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
            user_email=user_email,
            ip_address=ip_address,
            action="password_reset_request",
        )
    
    def log_password_reset_completed(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log successful password reset."""
        return self.log(
            event_type=AuditEventType.PASSWORD_RESET_COMPLETED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action="password_reset",
        )
    
    def log_email_verified(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log email verification."""
        return self.log(
            event_type=AuditEventType.EMAIL_VERIFIED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action="email_verify",
        )
    
    def log_suspicious_activity(
        self,
        ip_address: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log suspicious activity."""
        return self.log(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            user_email=user_email,
            ip_address=ip_address,
            status="warning",
            details=details,
        )
    
    def log_admin_action(
        self,
        event_type: AuditEventType,
        admin_id: str,
        target_user_id: str,
        action: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log admin action on a user."""
        return self.log(
            event_type=event_type,
            user_id=admin_id,
            resource=f"user:{target_user_id}",
            action=action,
            details=details,
        )
    
    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
    ) -> list[AuditEvent]:
        """Get recent audit events with optional filtering."""
        events = self._events.copy()
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        # Return most recent first
        return list(reversed(events[-limit:]))
    
    def get_failed_logins(
        self,
        ip_address: Optional[str] = None,
        since_minutes: int = 60,
    ) -> list[AuditEvent]:
        """Get failed login attempts for rate limiting detection."""
        cutoff = datetime.utcnow()
        from datetime import timedelta
        cutoff = cutoff - timedelta(minutes=since_minutes)
        
        events = [
            e for e in self._events
            if e.event_type == AuditEventType.USER_LOGIN_FAILED
            and e.timestamp > cutoff
        ]
        
        if ip_address:
            events = [e for e in events if e.ip_address == ip_address]
        
        return events


# Global audit logger instance
audit_logger = AuditLogger()
