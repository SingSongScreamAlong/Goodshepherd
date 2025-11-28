"""FastAPI application exposing Good Shepherd data services."""

from datetime import datetime
import logging
import os
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, Security, WebSocket, WebSocketDisconnect
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid

logger = logging.getLogger(__name__)

from backend.alerts.rules import AlertPriority, AlertRule, RuleEvaluator
from backend.database.repository import (
    AlertRuleCreate as RepoAlertRuleCreate,
    AlertRuleUpdate as RepoAlertRuleUpdate,
    get_event_by_id,
    get_report_by_id,
    create_alert_rule,
    delete_alert_rule,
    list_alert_rules,
    list_reports,
    list_recent_events,
    search_events as repo_search_events,
    update_alert_rule,
)
from backend.database.session import get_session
from backend.database.models import EventRecord, ReportRecord
from backend.reporting.service import generate_sitrep
from backend.reporting.pdf_export import PDFReportGenerator, generate_pdf_report
from backend.reporting.email_digest import EmailDigestService, SMTPConfig, DigestSubscription
from backend.realtime import ws_manager, get_ws_manager, WebSocketManager
from backend.location.geofencing import (
    GeofenceService,
    Coordinate,
    CircleGeofence,
    PolygonGeofence,
    ThreatZoneLevel,
    UserLocation,
)
from backend.auth.jwt import (
    Token,
    TokenData,
    UserCreate,
    UserLogin,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    get_current_user,
    get_current_user_optional,
    require_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.auth.user_repository import UserRepository
from backend.auth.password_reset import (
    create_password_reset_token,
    verify_password_reset_token,
    use_password_reset_token,
    create_email_verification_token,
    verify_email_verification_token,
    use_email_verification_token,
)
from backend.auth.email_service import auth_email_service
from backend.auth.audit_log import audit_logger, AuditEventType
from backend.auth.account_lockout import lockout_manager
from backend.auth.session_manager import session_manager, Session

# Rate limiter configuration
# Disable rate limiting in tests via environment variable
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=RATE_LIMIT_ENABLED)
app = FastAPI(title="Good Shepherd API", version="0.3.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup OpenTelemetry (optional - only if OTEL_ENABLED=true)
try:
    from backend.telemetry import setup_telemetry, RequestLoggingMiddleware
    setup_telemetry(app)
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Telemetry and request logging enabled")
except ImportError:
    logger.warning("OpenTelemetry not available - telemetry disabled")


@app.get("/api/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "version": "0.3.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Global service instances
geofence_service = GeofenceService()
email_digest_service = EmailDigestService(SMTPConfig.from_env())
pdf_generator = PDFReportGenerator()

# CORS middleware for frontend - configurable via environment
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Start background services on application startup."""
    dev_mode = os.getenv("DEV_MODE", "false").lower() in {"1", "true", "yes"}
    mode_str = "DEV MODE (SQLite)" if dev_mode else "PRODUCTION"
    logger.info(f"Starting Good Shepherd API v0.3.0 - {mode_str}")
    
    # Initialize database
    from backend.database.session import init_database
    await init_database()
    logger.info("Database initialized")
    
    # Start WebSocket manager (gracefully handles missing Redis)
    try:
        await ws_manager.start()
    except Exception as e:
        logger.warning(f"WebSocket manager startup issue (non-fatal): {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    await ws_manager.stop()


ADMIN_API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def get_admin_api_key() -> str | None:
    """Get admin API key from environment (allows runtime changes for testing)."""
    return os.getenv("ADMIN_API_KEY")


def require_admin_api_key(api_key: str | None = Security(ADMIN_API_KEY_HEADER)) -> None:
    admin_key = get_admin_api_key()
    if not admin_key:
        raise HTTPException(status_code=503, detail="Admin API key not configured")
    if api_key != admin_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


class Event(BaseModel):
    """Canonical representation of an event returned to clients."""

    id: str
    title: str
    summary: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    link: Optional[str] = None
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime
    geocode: Optional[dict[str, object]] = None
    confidence: float = 0.0
    verification_status: str
    credibility_score: float
    threat_level: Optional[str] = None
    duplicate_of: Optional[str] = None


class Report(BaseModel):
    """Canonical representation of a situational report."""

    id: str
    title: str
    summary: Optional[str] = None
    report_type: str
    region: Optional[str] = None
    generated_at: datetime
    generated_by: Optional[str] = None
    content: Optional[str] = None
    stats: Optional[dict[str, object]] = None
    source_event_ids: Optional[list[str]] = None


class SearchResponse(BaseModel):
    """Wrapper for search results."""

    count: int
    results: List[Event]


class ReportList(BaseModel):
    """Wrapper for report collections."""

    count: int
    results: List[Report]


class AlertCandidateResponse(BaseModel):
    """Representation of an alert that would be generated for an event."""

    event_id: str
    event_title: str
    rule_name: str
    priority: AlertPriority


class AlertRuleConfig(BaseModel):
    """API representation of an alert rule."""

    id: str
    name: str
    description: Optional[str] = None
    regions: list[str] | None = None
    categories: list[str] | None = None
    minimum_threat: str
    minimum_credibility: float
    lookback_minutes: int
    priority: AlertPriority
    auto_ack: bool
    created_at: datetime
    updated_at: datetime


class AlertRuleCreateRequest(BaseModel):
    """Payload for creating a new alert rule."""

    name: str
    description: Optional[str] = None
    regions: list[str] | None = None
    categories: list[str] | None = None
    minimum_threat: str = "medium"
    minimum_credibility: float = 0.6
    lookback_minutes: int = 60
    priority: AlertPriority = AlertPriority.HIGH
    auto_ack: bool = False

    @field_validator("minimum_threat")
    @classmethod
    def validate_threat(cls, value: str) -> str:
        lowered = value.lower()
        if lowered not in _ALLOWED_THREATS:
            raise ValueError(f"minimum_threat must be one of {_ALLOWED_THREATS}")
        return lowered

    @field_validator("minimum_credibility")
    @classmethod
    def validate_credibility(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("minimum_credibility must be between 0 and 1")
        return value

    @field_validator("lookback_minutes")
    @classmethod
    def validate_lookback(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("lookback_minutes must be positive")
        return value


class AlertRuleUpdateRequest(BaseModel):
    """Payload for updating an existing alert rule."""

    name: Optional[str] = None
    description: Optional[str] = None
    regions: list[str] | None = None
    categories: list[str] | None = None
    minimum_threat: Optional[str] = None
    minimum_credibility: Optional[float] = None
    lookback_minutes: Optional[int] = None
    priority: Optional[AlertPriority] = None
    auto_ack: Optional[bool] = None

    @field_validator("minimum_threat")
    @classmethod
    def validate_threat(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        lowered = value.lower()
        if lowered not in _ALLOWED_THREATS:
            raise ValueError(f"minimum_threat must be one of {_ALLOWED_THREATS}")
        return lowered

    @field_validator("minimum_credibility")
    @classmethod
    def validate_credibility(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if not 0 <= value <= 1:
            raise ValueError("minimum_credibility must be between 0 and 1")
        return value

    @field_validator("lookback_minutes")
    @classmethod
    def validate_lookback(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("lookback_minutes must be positive")
        return value


def serialize_record(record: EventRecord) -> Event:
    """Convert a SQLAlchemy record into the public API schema."""

    return Event(
        id=record.id,
        title=record.title or "Untitled event",
        summary=record.summary,
        category=record.category,
        region=record.region,
        link=record.link,
        source_url=record.source_url,
        published_at=record.published_at,
        fetched_at=record.fetched_at,
        geocode=record.geocode,
        confidence=record.confidence,
        verification_status=record.verification_status,
        credibility_score=record.credibility_score,
        threat_level=record.threat_level,
        duplicate_of=record.duplicate_of,
    )


def serialize_report(record: ReportRecord) -> Report:
    return Report(
        id=record.id,
        title=record.title,
        summary=record.summary,
        report_type=record.report_type,
        region=record.region,
        generated_at=record.generated_at,
        generated_by=record.generated_by,
        content=record.content,
        stats=record.stats,
        source_event_ids=record.source_event_ids,
    )


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    """Simple health check endpoint for uptime monitoring."""

    return {"status": "ok"}


@app.get("/api/search", response_model=SearchResponse, tags=["events"])
async def search_events(
    q: Annotated[str | None, Query(max_length=200)] = None,
    region: Annotated[str | None, Query(max_length=64)] = None,
    limit: Annotated[int, Query(le=100, ge=1)] = 25,
    session=Depends(get_session),
) -> SearchResponse:
    """Search events by keyword and region.

    Replace mock implementation with database + Meilisearch queries.
    """

    records = await repo_search_events(session, query=q, region=region, limit=limit)
    return SearchResponse(
        count=len(records),
        results=[serialize_record(record) for record in records],
    )


@app.get("/api/events/{event_id}", response_model=Event, tags=["events"])
async def get_event(event_id: str, session=Depends(get_session)) -> Event:
    """Fetch a single event by identifier.

    Replace with database lookup once repositories are implemented.
    """

    record = await get_event_by_id(session, event_id)
    if not record:
        raise HTTPException(status_code=404, detail="Event not found")
    return serialize_record(record)


@app.post(
    "/api/reports/generate",
    response_model=Report,
    tags=["reports"],
)
async def generate_report(
    lookback_hours: Annotated[int, Query(ge=1, le=168)] = 24,
    region: Annotated[str | None, Query(max_length=64)] = None,
    report_type: Annotated[str, Query(max_length=64)] = "daily_sitrep",
    title: Annotated[str | None, Query(max_length=256)] = None,
    generated_by: Annotated[str | None, Query(max_length=64)] = "system",
    session=Depends(get_session),
) -> Report:
    """Trigger generation of a situational report and return it."""

    report_id = await generate_sitrep(
        session,
        lookback_hours=lookback_hours,
        region=region,
        title=title,
        generated_by=generated_by or "system",
        report_type=report_type,
    )

    record = await get_report_by_id(session, report_id)
    if not record:
        raise HTTPException(status_code=500, detail="Report generation failed")
    return serialize_report(record)


@app.get("/api/reports", response_model=ReportList, tags=["reports"])
async def list_recent_reports(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    session=Depends(get_session),
) -> ReportList:
    """Return the most recent reports."""

    records = await list_reports(session, limit=limit)
    return ReportList(count=len(records), results=[serialize_report(record) for record in records])


@app.get("/api/reports/{report_id}", response_model=Report, tags=["reports"])
async def get_report(report_id: str, session=Depends(get_session)) -> Report:
    """Fetch a single report by identifier."""

    record = await get_report_by_id(session, report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found")
    return serialize_report(record)


@app.get("/api/alerts/evaluate", response_model=List[AlertCandidateResponse], tags=["alerts"])
async def evaluate_alerts(
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    session=Depends(get_session),
) -> List[AlertCandidateResponse]:
    """Evaluate configured alert rules against recent events. (Preview)"""

    events = await list_recent_events(session, limit=limit)

    rule_records = await list_alert_rules(session)

    rules = [_convert_rule(record) for record in rule_records]
    if not rules:
        rules = _default_rules()

    evaluator = RuleEvaluator(rules)
    candidates = evaluator.evaluate(events)

    return [
        AlertCandidateResponse(
            event_id=candidate.event.id,
            event_title=candidate.event.title or "Untitled event",
            rule_name=candidate.rule.name,
            priority=candidate.rule.priority,
        )
        for candidate in candidates
    ]


_ALLOWED_THREATS = {"low", "medium", "high", "critical"}


def _rule_to_config(record) -> AlertRuleConfig:
    return AlertRuleConfig(
        id=record.id,
        name=record.name,
        description=record.description,
        regions=record.regions,
        categories=record.categories,
        minimum_threat=record.minimum_threat,
        minimum_credibility=record.minimum_credibility,
        lookback_minutes=record.lookback_minutes,
        priority=AlertPriority(record.priority),
        auto_ack=record.auto_ack,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@app.get("/api/alerts/rules", response_model=List[AlertRuleConfig], tags=["alerts"])
async def list_alerts_rules_endpoint(session=Depends(get_session)) -> List[AlertRuleConfig]:
    """List stored alert rules."""

    records = await list_alert_rules(session)
    if not records:
        # present defaults when DB is empty for analyst context
        return [
            AlertRuleConfig(
                id="default-high-threat-europe",
                name="High Threat Europe",
                description="Fallback rule: high/critical threat events in EU",
                regions=["eu", "europe"],
                categories=None,
                minimum_threat="high",
                minimum_credibility=0.6,
                lookback_minutes=180,
                priority=AlertPriority.CRITICAL,
                auto_ack=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            AlertRuleConfig(
                id="default-violence",
                name="Violence",
                description="Fallback rule: verified violent incidents",
                regions=None,
                categories=["attack", "conflict", "riot"],
                minimum_threat="medium",
                minimum_credibility=0.5,
                lookback_minutes=120,
                priority=AlertPriority.HIGH,
                auto_ack=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

    return [
        _rule_to_config(record)
        for record in records
    ]


@app.post(
    "/api/alerts/rules",
    response_model=AlertRuleConfig,
    tags=["alerts"],
    status_code=201,
)
async def create_alert_rule_endpoint(
    payload: AlertRuleCreateRequest,
    session=Depends(get_session),
    _: None = Depends(require_admin_api_key),
) -> AlertRuleConfig:
    """Create a new alert rule."""

    repo_rule = RepoAlertRuleCreate(
        **payload.model_dump(exclude={"priority"}),
        priority=payload.priority.value,
    )
    record = await create_alert_rule(session, repo_rule)
    return _rule_to_config(record)


@app.put(
    "/api/alerts/rules/{rule_id}",
    response_model=AlertRuleConfig,
    tags=["alerts"],
)
async def update_alert_rule_endpoint(
    rule_id: str,
    payload: AlertRuleUpdateRequest,
    session=Depends(get_session),
    _: None = Depends(require_admin_api_key),
) -> AlertRuleConfig:
    """Update an existing alert rule."""

    repo_update = RepoAlertRuleUpdate(
        **payload.model_dump(exclude_none=True, exclude={"priority"}),
        **({"priority": payload.priority.value} if payload.priority is not None else {}),
    )
    record = await update_alert_rule(session, rule_id, repo_update)
    return _rule_to_config(record)


@app.delete(
    "/api/alerts/rules/{rule_id}",
    status_code=204,
    tags=["alerts"],
    response_class=Response,
)
async def delete_alert_rule_endpoint(
    rule_id: str,
    session=Depends(get_session),
    _: None = Depends(require_admin_api_key),
):
    """Delete an alert rule."""
    await delete_alert_rule(session, rule_id)
    return Response(status_code=204)


def _convert_rule(record) -> AlertRule:
    return AlertRule(
        name=record.name,
        description=record.description or "",
        regions=set(record.regions or []),
        categories=set(record.categories or []),
        minimum_threat=record.minimum_threat,
        minimum_credibility=record.minimum_credibility,
        lookback_minutes=record.lookback_minutes,
        priority=AlertPriority(record.priority),
        auto_ack=record.auto_ack,
    )


def _default_rules() -> List[AlertRule]:
    return [
        AlertRule(
            name="High Threat Europe",
            description="High or critical threat events in EU",
            regions={"eu", "europe"},
            minimum_threat="high",
            minimum_credibility=0.6,
            lookback_minutes=180,
            priority=AlertPriority.CRITICAL,
        ),
        AlertRule(
            name="Violence",
            description="Any verified violent incidents",
            categories={"attack", "conflict", "riot"},
            minimum_threat="medium",
            minimum_credibility=0.5,
            lookback_minutes=120,
            priority=AlertPriority.HIGH,
        ),
    ]


# =============================================================================
# Authentication Endpoints
# =============================================================================


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: Optional[str] = None
    roles: List[str] = []
    is_active: bool = True


@app.post("/api/auth/register", tags=["auth"], status_code=201)
@limiter.limit("5/hour")
async def register_user(
    request: Request,
    payload: UserCreate,
    session=Depends(get_session),
) -> UserResponse:
    """Register a new user account."""
    user_repo = UserRepository(session)
    client_ip = request.client.host if request.client else None
    
    # Check if user already exists
    if await user_repo.email_exists(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user in database
    user = await user_repo.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    
    # Audit log
    audit_logger.log_registration(user.id, user.email, ip_address=client_ip)
    
    # Send verification email
    verification_token = create_email_verification_token(user.email)
    await auth_email_service.send_verification_email(
        to_email=user.email,
        verification_token=verification_token,
        user_name=user.name,
    )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        roles=user.roles,
    )


@app.post("/api/auth/login", tags=["auth"])
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLogin,
    session=Depends(get_session),
) -> Token:
    """Authenticate and receive JWT tokens."""
    user_repo = UserRepository(session)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Check for account lockout
    lockout_status = lockout_manager.check_lockout(payload.email, client_ip)
    if lockout_status.is_locked:
        audit_logger.log_login_failed(
            user_email=payload.email,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="Account locked",
        )
        raise HTTPException(
            status_code=429,
            detail=lockout_status.message,
        )
    
    user = await user_repo.authenticate(payload.email, payload.password)
    
    if not user:
        # Record failed attempt and check for lockout
        lockout_status = lockout_manager.record_failed_attempt(payload.email, client_ip)
        
        # Log failed login
        audit_logger.log_login_failed(
            user_email=payload.email,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="Invalid credentials",
        )
        
        detail = "Invalid email or password"
        if lockout_status.is_locked:
            detail = lockout_status.message
        elif lockout_status.attempts_remaining <= 2:
            detail = f"Invalid email or password. {lockout_status.attempts_remaining} attempts remaining."
        
        raise HTTPException(
            status_code=401,
            detail=detail,
        )
    
    if not user.is_active:
        audit_logger.log_login_failed(
            user_email=payload.email,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="Account disabled",
        )
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Clear failed attempts on successful login
    lockout_manager.record_successful_login(payload.email, client_ip)
    
    # Log successful login
    audit_logger.log_login_success(
        user_id=user.id,
        user_email=user.email,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    
    # Create session with refresh token
    session, refresh_token = session_manager.create_session(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    
    # Create access token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "roles": user.roles or [],
        "session_id": session.session_id,
    }
    
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


@app.post("/api/auth/refresh", tags=["auth"])
async def refresh_tokens(
    request: Request,
    payload: RefreshTokenRequest,
) -> Token:
    """Refresh access token using refresh token with rotation."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Rotate the refresh token
    result = session_manager.rotate_refresh_token(
        payload.refresh_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error or "Invalid refresh token",
        )
    
    session = result.session
    
    # Create new access token
    token_data = {
        "sub": session.user_id,
        "session_id": session.session_id,
    }
    
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=result.new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get("/api/auth/me", tags=["auth"])
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
) -> UserResponse:
    """Get current authenticated user information."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(current_user.user_id)
    
    if user:
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            roles=user.roles or [],
            is_active=user.is_active,
        )
    
    # User not found in database but has valid token (fallback)
    return UserResponse(
        id=current_user.user_id,
        email=current_user.email or "",
        roles=current_user.roles,
    )


class SessionResponse(BaseModel):
    """Response model for a session."""
    session_id: str
    created_at: str
    last_used_at: str
    expires_at: str
    ip_address: Optional[str] = None
    device_name: Optional[str] = None
    is_current: bool = False


class SessionListResponse(BaseModel):
    """Response model for list of sessions."""
    sessions: list[SessionResponse]
    total: int


@app.get("/api/auth/sessions", tags=["auth"])
async def list_sessions(
    current_user: TokenData = Depends(get_current_user),
) -> SessionListResponse:
    """List all active sessions for the current user."""
    sessions = session_manager.get_user_sessions(current_user.user_id)
    current_session_id = getattr(current_user, 'session_id', None)
    
    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_id=s.session_id,
                created_at=s.created_at.isoformat(),
                last_used_at=s.last_used_at.isoformat(),
                expires_at=s.expires_at.isoformat(),
                ip_address=s.ip_address,
                device_name=s.device_name,
                is_current=s.session_id == current_session_id,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@app.delete("/api/auth/sessions/{session_id}", tags=["auth"])
async def revoke_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Revoke a specific session."""
    # Get the session to verify ownership
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this session")
    
    session_manager.revoke_session(session_id)
    
    audit_logger.log_event(
        AuditEventType.SESSION_REVOKED,
        user_id=current_user.user_id,
        details={"session_id": session_id},
    )
    
    return {"message": "Session revoked successfully"}


@app.delete("/api/auth/sessions", tags=["auth"])
async def revoke_all_sessions(
    current_user: TokenData = Depends(get_current_user),
):
    """Revoke all sessions except the current one."""
    current_session_id = getattr(current_user, 'session_id', None)
    sessions = session_manager.get_user_sessions(current_user.user_id)
    
    revoked_count = 0
    for session in sessions:
        if session.session_id != current_session_id:
            session_manager.revoke_session(session.session_id)
            revoked_count += 1
    
    audit_logger.log_event(
        AuditEventType.ALL_SESSIONS_REVOKED,
        user_id=current_user.user_id,
        details={"revoked_count": revoked_count},
    )
    
    return {"message": f"Revoked {revoked_count} sessions"}


@app.post("/api/auth/logout", tags=["auth"])
async def logout(
    current_user: TokenData = Depends(get_current_user),
):
    """Logout and revoke the current session."""
    session_id = getattr(current_user, 'session_id', None)
    
    if session_id:
        session_manager.revoke_session(session_id)
        audit_logger.log_event(
            AuditEventType.LOGOUT,
            user_id=current_user.user_id,
            details={"session_id": session_id},
        )
    
    return {"message": "Logged out successfully"}


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    email: str


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str
    new_password: str


class EmailVerificationRequest(BaseModel):
    """Request model for email verification."""
    token: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""
    current_password: str
    new_password: str


@app.post("/api/auth/password-reset/request", tags=["auth"])
@limiter.limit("3/hour")
async def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    session=Depends(get_session),
):
    """Request a password reset email."""
    user_repo = UserRepository(session)
    
    # Check if user exists (don't reveal if email exists for security)
    if await user_repo.email_exists(payload.email):
        token = create_password_reset_token(payload.email)
        # In production, send email with reset link containing token
        # For now, return success message (token would be in email)
        # TODO: Integrate with email service
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@app.post("/api/auth/password-reset/confirm", tags=["auth"])
@limiter.limit("5/hour")
async def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirm,
    session=Depends(get_session),
):
    """Reset password using the token from email."""
    email = verify_password_reset_token(payload.token)
    
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Update password
    await user_repo.update_password(user.id, payload.new_password)
    
    # Mark token as used
    use_password_reset_token(payload.token)
    
    return {"message": "Password has been reset successfully"}


@app.post("/api/auth/verify-email", tags=["auth"])
async def verify_email(
    payload: EmailVerificationRequest,
    session=Depends(get_session),
):
    """Verify email address using token."""
    email = verify_email_verification_token(payload.token)
    
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Mark user as verified
    await user_repo.verify_email(user.id)
    
    # Mark token as used
    use_email_verification_token(payload.token)
    
    return {"message": "Email verified successfully"}


@app.post("/api/auth/resend-verification", tags=["auth"])
@limiter.limit("3/hour")
async def resend_verification_email(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
):
    """Resend email verification link."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        return {"message": "Email is already verified"}
    
    token = create_email_verification_token(user.email)
    # TODO: Send verification email
    
    return {"message": "Verification email has been sent"}


@app.post("/api/auth/change-password", tags=["auth"])
async def change_password(
    payload: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
):
    """Change password for authenticated user."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    await user_repo.update_password(user.id, payload.new_password)
    
    return {"message": "Password changed successfully"}


# =============================================================================
# Admin User Management Endpoints
# =============================================================================


class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""
    name: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserListResponse(BaseModel):
    """Response model for user list."""
    users: List[UserResponse]
    total: int


@app.get("/api/admin/users", tags=["admin"], response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    _: str = Depends(require_admin_api_key),
    session=Depends(get_session),
):
    """List all users (admin only)."""
    user_repo = UserRepository(session)
    users = await user_repo.list_users(skip=skip, limit=limit)
    total = await user_repo.count_users()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=u.id,
                email=u.email,
                name=u.name,
                roles=u.roles or [],
                is_active=u.is_active,
            )
            for u in users
        ],
        total=total,
    )


@app.get("/api/admin/users/{user_id}", tags=["admin"], response_model=UserResponse)
async def get_user(
    user_id: str,
    _: str = Depends(require_admin_api_key),
    session=Depends(get_session),
):
    """Get a specific user by ID (admin only)."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        roles=user.roles or [],
        is_active=user.is_active,
    )


@app.patch("/api/admin/users/{user_id}", tags=["admin"], response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    _: str = Depends(require_admin_api_key),
    session=Depends(get_session),
):
    """Update a user (admin only)."""
    user_repo = UserRepository(session)
    user = await user_repo.update_user(
        user_id,
        name=payload.name,
        roles=payload.roles,
        is_active=payload.is_active,
        is_verified=payload.is_verified,
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        roles=user.roles or [],
        is_active=user.is_active,
    )


@app.delete("/api/admin/users/{user_id}", tags=["admin"])
async def delete_user(
    user_id: str,
    _: str = Depends(require_admin_api_key),
    session=Depends(get_session),
):
    """Delete a user (admin only)."""
    user_repo = UserRepository(session)
    success = await user_repo.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


# =============================================================================
# WebSocket Endpoints
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    manager: WebSocketManager = Depends(get_ws_manager),
):
    """WebSocket endpoint for real-time event updates.
    
    Clients can subscribe to specific regions, categories, or threat levels.
    
    Message format (client -> server):
    - {"type": "subscribe", "data": {"regions": ["europe"], "threat_levels": ["high", "critical"]}}
    - {"type": "unsubscribe"}
    - {"type": "ping"}
    
    Message format (server -> client):
    - {"type": "event:new", "timestamp": "...", "data": {...}}
    - {"type": "alert:triggered", "timestamp": "...", "data": {...}}
    - {"type": "heartbeat", "timestamp": "..."}
    """
    client_id = str(uuid.uuid4())

    try:
        client = await manager.connect(websocket, client_id)

        while True:
            try:
                data = await websocket.receive_json()
                await manager.handle_client_message(client_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
    finally:
        await manager.disconnect(client_id)


@app.get("/api/ws/stats", tags=["websocket"])
async def websocket_stats(
    manager: WebSocketManager = Depends(get_ws_manager),
) -> dict:
    """Get WebSocket connection statistics."""
    return {
        "connected_clients": manager.client_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Geofencing Endpoints
# =============================================================================

class CoordinateModel(BaseModel):
    """Geographic coordinate."""
    latitude: float
    longitude: float


class CircleGeofenceCreate(BaseModel):
    """Create a circular geofence."""
    name: str
    center: CoordinateModel
    radius_km: float
    threat_level: str = "warning"
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class PolygonGeofenceCreate(BaseModel):
    """Create a polygon geofence."""
    name: str
    vertices: List[CoordinateModel]
    threat_level: str = "warning"
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class GeofenceResponse(BaseModel):
    """Geofence response model."""
    id: str
    name: str
    geofence_type: str
    threat_level: str
    description: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class UserLocationUpdate(BaseModel):
    """User location update."""
    user_id: str
    latitude: float
    longitude: float
    accuracy_meters: float = 100.0


class GeofenceAlertResponse(BaseModel):
    """Geofence alert response."""
    id: str
    user_id: str
    geofence_id: str
    geofence_name: str
    event_type: str  # "enter" or "exit"
    threat_level: str
    timestamp: datetime
    message: str


@app.get("/api/geofences", tags=["geofencing"])
@limiter.limit("100/minute")
async def list_geofences(
    request: Request,
    active_only: bool = Query(True, description="Only return active (non-expired) geofences"),
) -> List[GeofenceResponse]:
    """List all geofences."""
    fences = geofence_service.list_geofences(active_only=active_only)
    return [
        GeofenceResponse(
            id=f.id,
            name=f.name,
            geofence_type="circle" if isinstance(f, CircleGeofence) else "polygon",
            threat_level=f.threat_level.value,
            description=f.description,
            created_at=f.created_at,
            expires_at=f.expires_at,
        )
        for f in fences
    ]


@app.get("/api/geofences/{geofence_id}", tags=["geofencing"])
async def get_geofence(geofence_id: str) -> GeofenceResponse:
    """Get a specific geofence by ID."""
    fence = geofence_service.get_geofence(geofence_id)
    if not fence:
        raise HTTPException(status_code=404, detail="Geofence not found")

    return GeofenceResponse(
        id=fence.id,
        name=fence.name,
        geofence_type="circle" if isinstance(fence, CircleGeofence) else "polygon",
        threat_level=fence.threat_level.value,
        description=fence.description,
        created_at=fence.created_at,
        expires_at=fence.expires_at,
    )


@app.post("/api/geofences/circle", tags=["geofencing"], status_code=201)
async def create_circle_geofence(
    payload: CircleGeofenceCreate,
    _: None = Depends(require_admin_api_key),
) -> GeofenceResponse:
    """Create a circular geofence."""
    fence = CircleGeofence(
        id=str(uuid.uuid4()),
        name=payload.name,
        center=Coordinate(latitude=payload.center.latitude, longitude=payload.center.longitude),
        radius_km=payload.radius_km,
        threat_level=ThreatZoneLevel(payload.threat_level),
        description=payload.description,
        expires_at=payload.expires_at,
    )
    geofence_service.add_geofence(fence)

    return GeofenceResponse(
        id=fence.id,
        name=fence.name,
        geofence_type="circle",
        threat_level=fence.threat_level.value,
        description=fence.description,
        created_at=fence.created_at,
        expires_at=fence.expires_at,
    )


@app.post("/api/geofences/polygon", tags=["geofencing"], status_code=201)
async def create_polygon_geofence(
    payload: PolygonGeofenceCreate,
    _: None = Depends(require_admin_api_key),
) -> GeofenceResponse:
    """Create a polygon geofence."""
    vertices = [
        Coordinate(latitude=v.latitude, longitude=v.longitude)
        for v in payload.vertices
    ]

    fence = PolygonGeofence(
        id=str(uuid.uuid4()),
        name=payload.name,
        vertices=vertices,
        threat_level=ThreatZoneLevel(payload.threat_level),
        description=payload.description,
        expires_at=payload.expires_at,
    )
    geofence_service.add_geofence(fence)

    return GeofenceResponse(
        id=fence.id,
        name=fence.name,
        geofence_type="polygon",
        threat_level=fence.threat_level.value,
        description=fence.description,
        created_at=fence.created_at,
        expires_at=fence.expires_at,
    )


@app.delete(
    "/api/geofences/{geofence_id}",
    status_code=204,
    tags=["geofencing"],
    response_class=Response,
)
async def delete_geofence(
    geofence_id: str,
    _: None = Depends(require_admin_api_key),
):
    """Delete a geofence."""
    if not geofence_service.remove_geofence(geofence_id):
        raise HTTPException(status_code=404, detail="Geofence not found")
    return Response(status_code=204)


@app.post("/api/geofences/from-event", tags=["geofencing"], status_code=201)
async def create_geofence_from_event(
    event_id: str,
    radius_km: float = Query(10.0, description="Radius in kilometers"),
    session=Depends(get_session),
    _: None = Depends(require_admin_api_key),
) -> GeofenceResponse:
    """Create a geofence from an existing event's location."""
    event = await get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event_dict = {
        "title": event.title,
        "threat_level": event.threat_level,
        "geocode": event.geocode,
        "summary": event.summary,
    }

    fence = geofence_service.create_geofence_from_event(event_dict, radius_km=radius_km)
    if not fence:
        raise HTTPException(status_code=400, detail="Event has no geocode data")

    return GeofenceResponse(
        id=fence.id,
        name=fence.name,
        geofence_type="circle",
        threat_level=fence.threat_level.value,
        description=fence.description,
        created_at=fence.created_at,
        expires_at=fence.expires_at,
    )


# =============================================================================
# Location Tracking Endpoints
# =============================================================================

@app.post("/api/location/update", tags=["location"])
@limiter.limit("60/minute")
async def update_user_location(
    request: Request,
    payload: UserLocationUpdate,
    manager: WebSocketManager = Depends(get_ws_manager),
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """Update a user's location and check for geofence alerts."""
    location = UserLocation(
        user_id=payload.user_id,
        coordinate=Coordinate(latitude=payload.latitude, longitude=payload.longitude),
        accuracy_meters=payload.accuracy_meters,
        timestamp=datetime.utcnow(),
    )

    alerts = geofence_service.update_user_location(location)
    threat_level = geofence_service.get_user_threat_level(payload.user_id)

    # Broadcast alerts via WebSocket
    for alert in alerts:
        await manager.broadcast_alert({
            "type": "geofence_alert",
            "id": alert.id,
            "user_id": alert.user_id,
            "geofence_id": alert.geofence_id,
            "geofence_name": alert.geofence_name,
            "event_type": alert.event_type,
            "threat_level": alert.threat_level.value,
            "message": alert.message,
        })

    return {
        "user_id": payload.user_id,
        "current_threat_level": threat_level.value if threat_level else "safe",
        "alerts": [
            GeofenceAlertResponse(
                id=a.id,
                user_id=a.user_id,
                geofence_id=a.geofence_id,
                geofence_name=a.geofence_name,
                event_type=a.event_type,
                threat_level=a.threat_level.value,
                timestamp=a.timestamp,
                message=a.message,
            ).model_dump()
            for a in alerts
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/location/{user_id}/threat-level", tags=["location"])
async def get_user_threat_level(user_id: str) -> dict:
    """Get the current threat level for a user based on their location."""
    threat_level = geofence_service.get_user_threat_level(user_id)
    return {
        "user_id": user_id,
        "threat_level": threat_level.value if threat_level else "safe",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/location/nearby-threats", tags=["location"])
async def get_nearby_threats(
    latitude: float,
    longitude: float,
    radius_km: float = Query(50.0, description="Search radius in kilometers"),
) -> List[dict]:
    """Get nearby threat zones for a given location."""
    location = Coordinate(latitude=latitude, longitude=longitude)
    threats = geofence_service.get_nearby_threats(location, radius_km=radius_km)

    return [
        {
            "geofence_id": fence.id,
            "name": fence.name,
            "threat_level": fence.threat_level.value,
            "distance_km": round(distance, 2),
            "description": fence.description,
        }
        for fence, distance in threats
    ]


# =============================================================================
# PDF Report Endpoints
# =============================================================================

class PDFReportRequest(BaseModel):
    """Request for PDF report generation."""
    title: str
    region: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_events: bool = True
    max_events: int = 100


@app.post("/api/reports/pdf", tags=["reports"])
async def generate_pdf_report_endpoint(
    payload: PDFReportRequest,
    session=Depends(get_session),
) -> Response:
    """Generate a PDF situational report."""
    # Fetch events for the report
    events = await list_recent_events(session, limit=payload.max_events)

    # Filter by region if specified
    if payload.region:
        events = [e for e in events if e.region and payload.region.lower() in e.region.lower()]

    # Convert to dict format
    event_dicts = [
        {
            "title": e.title,
            "summary": e.summary,
            "region": e.region,
            "category": e.category,
            "threat_level": e.threat_level,
            "published_at": e.published_at.isoformat() if e.published_at else None,
            "link": e.link,
        }
        for e in events
    ]

    # Generate PDF
    pdf_bytes = generate_pdf_report(
        title=payload.title,
        events=event_dicts,
        region=payload.region,
    )

    filename = f"sitrep_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/reports/{report_id}/pdf", tags=["reports"])
async def get_report_as_pdf(
    report_id: str,
    session=Depends(get_session),
) -> Response:
    """Download an existing report as PDF."""
    report = await get_report_by_id(session, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Generate PDF from report content
    pdf_bytes = generate_pdf_report(
        title=report.title,
        events=[],  # Report already has content
        region=report.region,
    )

    filename = f"report_{report_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# =============================================================================
# Email Digest Endpoints
# =============================================================================

class DigestSubscriptionCreate(BaseModel):
    """Create an email digest subscription."""
    email: str
    name: Optional[str] = None
    frequency: str = "daily"  # daily, weekly
    regions: List[str] = []
    min_threat_level: str = "medium"
    include_pdf: bool = True


class DigestSubscriptionResponse(BaseModel):
    """Email digest subscription response."""
    email: str
    name: Optional[str] = None
    frequency: str
    regions: List[str]
    min_threat_level: str
    include_pdf: bool
    enabled: bool
    last_sent: Optional[datetime] = None


@app.get("/api/digests/subscriptions", tags=["digests"])
async def list_digest_subscriptions(
    _: None = Depends(require_admin_api_key),
) -> List[DigestSubscriptionResponse]:
    """List all email digest subscriptions."""
    subs = email_digest_service.list_subscriptions()
    return [
        DigestSubscriptionResponse(
            email=s.email,
            name=s.name,
            frequency=s.frequency,
            regions=list(s.regions),
            min_threat_level=s.min_threat_level,
            include_pdf=s.include_pdf,
            enabled=s.enabled,
            last_sent=s.last_sent,
        )
        for s in subs
    ]


@app.post("/api/digests/subscriptions", tags=["digests"], status_code=201)
@limiter.limit("10/hour")
async def create_digest_subscription(
    request: Request,
    payload: DigestSubscriptionCreate,
    current_user: TokenData = Depends(get_current_user),
) -> DigestSubscriptionResponse:
    """Create a new email digest subscription."""
    sub = DigestSubscription(
        email=payload.email,
        name=payload.name or "",
        frequency=payload.frequency,
        regions=list(payload.regions),
        min_threat_level=payload.min_threat_level,
        include_pdf=payload.include_pdf,
    )
    email_digest_service.add_subscription(sub)

    return DigestSubscriptionResponse(
        email=sub.email,
        name=sub.name,
        frequency=sub.frequency,
        regions=list(sub.regions),
        min_threat_level=sub.min_threat_level,
        include_pdf=sub.include_pdf,
        enabled=sub.enabled,
        last_sent=sub.last_sent,
    )


@app.get("/api/digests/subscriptions/{email}", tags=["digests"])
async def get_digest_subscription(
    email: str,
    current_user: TokenData = Depends(get_current_user),
) -> DigestSubscriptionResponse:
    """Get a specific subscription by email."""
    sub = email_digest_service.get_subscription(email)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return DigestSubscriptionResponse(
        email=sub.email,
        name=sub.name,
        frequency=sub.frequency,
        regions=list(sub.regions),
        min_threat_level=sub.min_threat_level,
        include_pdf=sub.include_pdf,
        enabled=sub.enabled,
        last_sent=sub.last_sent,
    )


@app.delete(
    "/api/digests/subscriptions/{email}",
    status_code=204,
    tags=["digests"],
    response_class=Response,
)
async def delete_digest_subscription(
    email: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Unsubscribe from email digests."""
    if not email_digest_service.remove_subscription(email):
        raise HTTPException(status_code=404, detail="Subscription not found")
    return Response(status_code=204)


@app.post("/api/digests/send-test", tags=["digests"])
async def send_test_digest(
    email: str,
    session=Depends(get_session),
    _: None = Depends(require_admin_api_key),
) -> dict:
    """Send a test digest email."""
    sub = email_digest_service.get_subscription(email)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Get recent events
    events = await list_recent_events(session, limit=50)
    event_dicts = [
        {
            "title": e.title,
            "summary": e.summary,
            "region": e.region,
            "category": e.category,
            "threat_level": e.threat_level,
            "published_at": e.published_at.isoformat() if e.published_at else None,
        }
        for e in events
    ]

    from datetime import timedelta
    result = await email_digest_service.send_digest(
        sub,
        event_dicts,
        datetime.utcnow() - timedelta(days=1),
        datetime.utcnow(),
    )

    return {
        "success": result.success,
        "message_id": result.message_id,
        "error": result.error,
    }


# =============================================================================
# Notification Preferences API
# =============================================================================

class NotificationPreferencesCreate(BaseModel):
    """Create notification preferences."""
    email_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    push_enabled: bool = True
    webhook_enabled: bool = False
    phone_number: Optional[str] = None
    webhook_url: Optional[str] = None
    digest_frequency: str = "daily"
    min_priority: str = "medium"
    watched_regions: Optional[List[str]] = None
    watched_categories: Optional[List[str]] = None
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None


class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences."""
    id: str
    user_id: str
    email_enabled: bool
    sms_enabled: bool
    whatsapp_enabled: bool
    push_enabled: bool
    webhook_enabled: bool
    phone_number: Optional[str]
    webhook_url: Optional[str]
    digest_frequency: str
    min_priority: str
    watched_regions: Optional[List[str]]
    watched_categories: Optional[List[str]]
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]


@app.get("/api/notifications/preferences", tags=["notifications"])
async def get_notification_preferences(
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
) -> NotificationPreferencesResponse:
    """Get current user's notification preferences."""
    from sqlalchemy import select
    from backend.alerts.notification_preferences import NotificationPreferencesRecord
    
    result = await session.execute(
        select(NotificationPreferencesRecord)
        .where(NotificationPreferencesRecord.user_id == current_user.user_id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        # Return defaults
        return NotificationPreferencesResponse(
            id="",
            user_id=current_user.user_id,
            email_enabled=True,
            sms_enabled=False,
            whatsapp_enabled=False,
            push_enabled=True,
            webhook_enabled=False,
            phone_number=None,
            webhook_url=None,
            digest_frequency="daily",
            min_priority="medium",
            watched_regions=None,
            watched_categories=None,
            quiet_hours_enabled=False,
            quiet_hours_start=None,
            quiet_hours_end=None,
        )
    
    return NotificationPreferencesResponse(
        id=prefs.id,
        user_id=prefs.user_id,
        email_enabled=prefs.email_enabled,
        sms_enabled=prefs.sms_enabled,
        whatsapp_enabled=prefs.whatsapp_enabled,
        push_enabled=prefs.push_enabled,
        webhook_enabled=prefs.webhook_enabled,
        phone_number=prefs.phone_number,
        webhook_url=prefs.webhook_url,
        digest_frequency=prefs.digest_frequency,
        min_priority=prefs.min_priority,
        watched_regions=prefs.watched_regions,
        watched_categories=prefs.watched_categories,
        quiet_hours_enabled=prefs.quiet_hours_enabled,
        quiet_hours_start=prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        quiet_hours_end=prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
    )


@app.put("/api/notifications/preferences", tags=["notifications"])
async def update_notification_preferences(
    payload: NotificationPreferencesCreate,
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
) -> NotificationPreferencesResponse:
    """Update current user's notification preferences."""
    from sqlalchemy import select
    from backend.alerts.notification_preferences import NotificationPreferencesRecord
    from datetime import time
    
    result = await session.execute(
        select(NotificationPreferencesRecord)
        .where(NotificationPreferencesRecord.user_id == current_user.user_id)
    )
    prefs = result.scalar_one_or_none()
    
    # Parse quiet hours
    quiet_start = None
    quiet_end = None
    if payload.quiet_hours_start:
        try:
            h, m = map(int, payload.quiet_hours_start.split(":"))
            quiet_start = time(h, m)
        except ValueError:
            pass
    if payload.quiet_hours_end:
        try:
            h, m = map(int, payload.quiet_hours_end.split(":"))
            quiet_end = time(h, m)
        except ValueError:
            pass
    
    if prefs:
        # Update existing
        prefs.email_enabled = payload.email_enabled
        prefs.sms_enabled = payload.sms_enabled
        prefs.whatsapp_enabled = payload.whatsapp_enabled
        prefs.push_enabled = payload.push_enabled
        prefs.webhook_enabled = payload.webhook_enabled
        prefs.phone_number = payload.phone_number
        prefs.webhook_url = payload.webhook_url
        prefs.digest_frequency = payload.digest_frequency
        prefs.min_priority = payload.min_priority
        prefs.watched_regions = payload.watched_regions
        prefs.watched_categories = payload.watched_categories
        prefs.quiet_hours_enabled = payload.quiet_hours_enabled
        prefs.quiet_hours_start = quiet_start
        prefs.quiet_hours_end = quiet_end
    else:
        # Create new
        prefs = NotificationPreferencesRecord(
            user_id=current_user.user_id,
            email_enabled=payload.email_enabled,
            sms_enabled=payload.sms_enabled,
            whatsapp_enabled=payload.whatsapp_enabled,
            push_enabled=payload.push_enabled,
            webhook_enabled=payload.webhook_enabled,
            phone_number=payload.phone_number,
            webhook_url=payload.webhook_url,
            digest_frequency=payload.digest_frequency,
            min_priority=payload.min_priority,
            watched_regions=payload.watched_regions,
            watched_categories=payload.watched_categories,
            quiet_hours_enabled=payload.quiet_hours_enabled,
            quiet_hours_start=quiet_start,
            quiet_hours_end=quiet_end,
        )
        session.add(prefs)
    
    await session.commit()
    await session.refresh(prefs)
    
    return NotificationPreferencesResponse(
        id=prefs.id,
        user_id=prefs.user_id,
        email_enabled=prefs.email_enabled,
        sms_enabled=prefs.sms_enabled,
        whatsapp_enabled=prefs.whatsapp_enabled,
        push_enabled=prefs.push_enabled,
        webhook_enabled=prefs.webhook_enabled,
        phone_number=prefs.phone_number,
        webhook_url=prefs.webhook_url,
        digest_frequency=prefs.digest_frequency,
        min_priority=prefs.min_priority,
        watched_regions=prefs.watched_regions,
        watched_categories=prefs.watched_categories,
        quiet_hours_enabled=prefs.quiet_hours_enabled,
        quiet_hours_start=prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        quiet_hours_end=prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
    )


# =============================================================================
# Alert Acknowledgment API
# =============================================================================

class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""
    event_id: str
    notes: Optional[str] = None


@app.post("/api/alerts/acknowledge", tags=["alerts"])
async def acknowledge_alert(
    payload: AcknowledgeAlertRequest,
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
) -> dict:
    """Acknowledge an alert for the current user."""
    from backend.alerts.alert_engine import alert_engine
    
    success = await alert_engine.acknowledge_alert(
        session,
        user_id=current_user.user_id,
        event_id=payload.event_id,
        notes=payload.notes,
    )
    
    if success:
        return {"message": "Alert acknowledged"}
    else:
        raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/api/alerts/unacknowledged", tags=["alerts"])
async def get_unacknowledged_alerts(
    current_user: TokenData = Depends(get_current_user),
    session=Depends(get_session),
    limit: int = Query(default=50, le=100),
) -> List[dict]:
    """Get unacknowledged alerts for the current user."""
    from sqlalchemy import select, and_
    from backend.alerts.notification_preferences import SentNotificationRecord
    
    result = await session.execute(
        select(SentNotificationRecord)
        .where(and_(
            SentNotificationRecord.user_id == current_user.user_id,
            SentNotificationRecord.status == "sent",
            SentNotificationRecord.acknowledged_at.is_(None),
        ))
        .order_by(SentNotificationRecord.created_at.desc())
        .limit(limit)
    )
    
    notifications = result.scalars().all()
    
    # Get event details
    alerts = []
    for notification in notifications:
        event = await get_event_by_id(session, notification.event_id)
        if event:
            alerts.append({
                "notification_id": notification.id,
                "event_id": notification.event_id,
                "channel": notification.channel,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "event": {
                    "title": event.title,
                    "summary": event.summary[:200] if event.summary else None,
                    "region": event.region,
                    "category": event.category,
                    "threat_level": event.threat_level,
                    "link": event.link,
                },
            })
    
    return alerts


# =============================================================================
# Data Sources Status API
# =============================================================================

@app.get("/api/sources/status", tags=["sources"])
async def get_data_sources_status() -> dict:
    """Get status of all data sources."""
    import os
    
    sources = {
        "gdacs": {
            "name": "GDACS Disasters",
            "enabled": os.getenv("GDACS_ENABLED", "true").lower() == "true",
            "description": "Global Disaster Alert and Coordination System",
            "url": "https://www.gdacs.org",
            "requires_api_key": False,
        },
        "reliefweb": {
            "name": "ReliefWeb",
            "enabled": os.getenv("RELIEFWEB_ENABLED", "true").lower() == "true",
            "description": "Humanitarian information on global crises",
            "url": "https://reliefweb.int",
            "requires_api_key": False,
        },
        "who": {
            "name": "WHO Outbreaks",
            "enabled": os.getenv("WHO_ENABLED", "true").lower() == "true",
            "description": "Disease outbreak news from WHO",
            "url": "https://www.who.int",
            "requires_api_key": False,
        },
        "acled": {
            "name": "ACLED Conflicts",
            "enabled": os.getenv("ACLED_ENABLED", "true").lower() == "true" and bool(os.getenv("ACLED_API_KEY")),
            "description": "Armed Conflict Location & Event Data",
            "url": "https://acleddata.com",
            "requires_api_key": True,
            "api_key_configured": bool(os.getenv("ACLED_API_KEY")),
        },
        "social": {
            "name": "Social Media",
            "enabled": os.getenv("SOCIAL_ENABLED", "true").lower() == "true",
            "description": "Twitter/Telegram crisis monitoring",
            "requires_api_key": False,
        },
    }
    
    return {
        "sources": sources,
        "total_enabled": sum(1 for s in sources.values() if s["enabled"]),
    }


# =============================================================================
# ML Model API
# =============================================================================

class TranslateRequest(BaseModel):
    """Translation request."""
    text: str
    source_language: Optional[str] = None
    target_language: Optional[str] = None


class ThreatClassifyRequest(BaseModel):
    """Threat classification request."""
    text: str
    title: Optional[str] = None
    source_credibility: float = 0.7


class DisinfoCheckRequest(BaseModel):
    """Disinformation check request."""
    text: str
    source_url: Optional[str] = None
    source_name: Optional[str] = None


class AnalyzeEventRequest(BaseModel):
    """Full event analysis request."""
    text: str
    title: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    source_credibility: float = 0.7
    translate: bool = True


class AnalyzeBatchRequest(BaseModel):
    """Batch analysis request."""
    events: list[dict]
    translate: bool = True


@app.post("/api/ml/translate", tags=["ml"])
async def translate_text(request: TranslateRequest) -> dict:
    """Translate text to target language."""
    from backend.ml.model_service import get_model_service
    
    service = get_model_service()
    result = await service.translate(
        text=request.text,
        source_language=request.source_language,
        target_language=request.target_language,
    )
    
    return {
        "original_text": result.original_text,
        "translated_text": result.translated_text,
        "source_language": result.source_language,
        "target_language": result.target_language,
        "confidence": result.confidence,
        "provider": result.provider,
        "cached": result.cached,
    }


@app.post("/api/ml/detect-language", tags=["ml"])
async def detect_language(text: str = Query(..., min_length=1)) -> dict:
    """Detect the language of text."""
    from backend.ml.translation import get_translation_service
    
    service = get_translation_service()
    result = await service.detect_language(text)
    
    return {
        "language": result.language,
        "language_name": result.language_name,
        "confidence": result.confidence,
    }


@app.post("/api/ml/classify-threat", tags=["ml"])
async def classify_threat(request: ThreatClassifyRequest) -> dict:
    """Classify threat level and category."""
    from backend.ml.model_service import get_model_service
    
    service = get_model_service()
    result = service.classify_threat(
        text=request.text,
        title=request.title,
        source_credibility=request.source_credibility,
    )
    
    return result.to_dict()


@app.post("/api/ml/check-disinfo", tags=["ml"])
async def check_disinformation(request: DisinfoCheckRequest) -> dict:
    """Check content for disinformation indicators."""
    from backend.ml.model_service import get_model_service
    
    service = get_model_service()
    result = service.detect_disinfo(
        text=request.text,
        source_url=request.source_url,
        source_name=request.source_name,
    )
    
    return result.to_dict()


@app.post("/api/ml/analyze", tags=["ml"])
async def analyze_event(request: AnalyzeEventRequest) -> dict:
    """Perform complete ML analysis on an event."""
    from backend.ml.model_service import get_model_service
    
    service = get_model_service()
    result = await service.analyze_event(
        text=request.text,
        title=request.title,
        source_url=request.source_url,
        source_name=request.source_name,
        source_credibility=request.source_credibility,
        translate=request.translate,
    )
    
    return result.to_dict()


@app.post("/api/ml/analyze-batch", tags=["ml"])
async def analyze_events_batch(request: AnalyzeBatchRequest) -> dict:
    """Analyze multiple events in batch."""
    from backend.ml.model_service import get_model_service
    
    if len(request.events) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 events per batch")
    
    service = get_model_service()
    results = await service.analyze_batch(
        events=request.events,
        translate=request.translate,
    )
    
    return {
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }


@app.get("/api/ml/status", tags=["ml"])
async def get_ml_status() -> dict:
    """Get ML service status."""
    from backend.ml.model_service import get_model_service
    
    service = get_model_service()
    return service.get_status()


# =============================================================================
# Analytics API (Phase 3: Analyst Dashboard)
# =============================================================================

@app.get("/api/analytics/summary", tags=["analytics"])
async def get_analytics_summary(period: str = Query("7d", regex="^(24h|7d|30d|90d)$")) -> dict:
    """Get analytics summary for the specified period."""
    from backend.analytics.service import get_analytics_service
    
    service = get_analytics_service()
    return await service.get_summary(period=period)


@app.get("/api/analytics/trends", tags=["analytics"])
async def get_threat_trends(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    granularity: str = Query("day", regex="^(hour|day)$"),
) -> dict:
    """Get event trends over time."""
    from backend.analytics.service import get_analytics_service
    
    service = get_analytics_service()
    return await service.get_trends(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )


@app.get("/api/analytics/regions", tags=["analytics"])
async def get_regional_breakdown(period: str = Query("7d", regex="^(24h|7d|30d|90d)$")) -> dict:
    """Get breakdown by region."""
    from backend.analytics.service import get_analytics_service
    
    service = get_analytics_service()
    return await service.get_regional_breakdown(period=period)


@app.get("/api/events/timeline", tags=["analytics"])
async def get_timeline_events(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    category: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(200, le=500),
) -> dict:
    """Get events for timeline visualization."""
    from backend.analytics.service import get_analytics_service
    
    service = get_analytics_service()
    return await service.get_timeline_events(
        start_date=start_date,
        end_date=end_date,
        category=category,
        region=region,
        limit=limit,
    )


@app.get("/api/analyst/review-queue", tags=["analytics"])
async def get_review_queue(
    status: str = Query("pending", regex="^(pending|flagged|verified)$"),
    priority: Optional[str] = Query(None, regex="^(urgent|high|normal|low)$"),
    limit: int = Query(50, le=100),
) -> dict:
    """Get events for analyst review queue."""
    from backend.analytics.service import get_analytics_service
    
    service = get_analytics_service()
    return await service.get_review_queue(
        status=status,
        priority=priority,
        limit=limit,
    )


class ValidationRequest(BaseModel):
    """Event validation request."""
    status: str
    notes: Optional[str] = None


@app.post("/api/analyst/validate/{event_id}", tags=["analytics"])
async def validate_event(
    event_id: str,
    request: ValidationRequest,
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """Submit event validation (human-in-loop)."""
    from backend.database.repository import update_event_verification, VerificationUpdate
    from backend.database.session import session_scope
    from uuid import UUID
    
    async with session_scope() as session:
        await update_event_verification(
            session,
            UUID(event_id),
            VerificationUpdate(
                verification_status=request.status,
            ),
        )
    
    return {
        "success": True,
        "event_id": event_id,
        "status": request.status,
        "validated_by": current_user.username,
    }


class MLFeedbackRequest(BaseModel):
    """ML feedback request."""
    event_id: str
    corrected_category: Optional[str] = None
    corrected_threat_level: Optional[str] = None
    is_disinformation: bool = False
    analyst_notes: Optional[str] = None


@app.post("/api/ml/feedback", tags=["analytics"])
async def submit_ml_feedback(
    request: MLFeedbackRequest,
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """Submit ML feedback for model improvement."""
    from backend.analytics.ml_feedback import get_ml_feedback_service
    
    service = get_ml_feedback_service()
    return await service.submit_feedback(
        event_id=request.event_id,
        feedback={
            "corrected_category": request.corrected_category,
            "corrected_threat_level": request.corrected_threat_level,
            "is_disinformation": request.is_disinformation,
            "analyst_notes": request.analyst_notes,
        },
        analyst_id=current_user.username,
    )


@app.get("/api/ml/feedback/stats", tags=["analytics"])
async def get_ml_feedback_stats() -> dict:
    """Get ML feedback statistics."""
    from backend.analytics.ml_feedback import get_ml_feedback_service
    
    service = get_ml_feedback_service()
    stats = service.get_feedback_stats()
    
    return {
        "total_feedback": stats.total_feedback,
        "category_corrections": stats.category_corrections,
        "threat_corrections": stats.threat_corrections,
        "disinfo_flags": stats.disinfo_flags,
        "accuracy_by_category": stats.accuracy_by_category,
        "accuracy_by_threat": stats.accuracy_by_threat,
    }


# =============================================================================
# Mobile/Field API (Phase 4: Field Deployment)
# =============================================================================

class CheckInRequest(BaseModel):
    """Check-in request from mobile app."""
    status: str  # safe, caution, help
    note: Optional[str] = None
    location: Optional[dict] = None
    timestamp: Optional[str] = None


class CheckInResponse(BaseModel):
    """Check-in response."""
    success: bool
    check_in_id: str
    message: str


@app.post("/api/checkin", tags=["mobile"], response_model=CheckInResponse)
async def submit_checkin(
    request: CheckInRequest,
    current_user: TokenData = Depends(get_current_user),
) -> CheckInResponse:
    """Submit a safety check-in from mobile app."""
    import uuid
    from datetime import datetime
    
    check_in_id = str(uuid.uuid4())
    
    # In production, this would save to database and notify coordinators
    # For now, just log and return success
    logger.info(
        f"Check-in received: user={current_user.username}, "
        f"status={request.status}, location={request.location}"
    )
    
    # If status is 'help', trigger emergency notification
    if request.status == "help":
        logger.warning(f"EMERGENCY CHECK-IN from {current_user.username}")
        # Would trigger SMS/push to coordinators
    
    return CheckInResponse(
        success=True,
        check_in_id=check_in_id,
        message=f"Check-in recorded as {request.status}",
    )


@app.get("/api/events/recent", tags=["mobile"])
async def get_recent_events(
    limit: int = Query(50, le=100),
    region: Optional[str] = None,
    threat_level: Optional[str] = None,
) -> dict:
    """Get recent events for mobile dashboard (optimized for low bandwidth)."""
    from backend.analytics.service import get_analytics_service
    from datetime import datetime, timedelta
    
    service = get_analytics_service()
    
    # Get events from last 7 days
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    result = await service.get_timeline_events(
        start_date=start_date,
        end_date=end_date,
        category=None,
        region=region,
        limit=limit,
    )
    
    # Filter by threat level if specified
    events = result.get("events", [])
    if threat_level:
        events = [e for e in events if e.get("threat_level") == threat_level]
    
    # Return minimal data for bandwidth optimization
    return {
        "events": [
            {
                "id": e["id"],
                "title": e["title"],
                "summary": e.get("summary", "")[:200],  # Truncate for bandwidth
                "threat_level": e.get("threat_level"),
                "category": e.get("category"),
                "region": e.get("region"),
                "fetched_at": e.get("fetched_at"),
            }
            for e in events
        ],
        "total": len(events),
        "cached_at": datetime.utcnow().isoformat(),
    }


class SMSAlertRequest(BaseModel):
    """SMS alert request."""
    phone_numbers: list[str]
    message: str
    threat_level: str = "medium"


@app.post("/api/notifications/sms", tags=["mobile"])
async def send_sms_alert(
    request: SMSAlertRequest,
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """Send SMS alert (admin only)."""
    # Check admin role
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from backend.notifications.sms_service import get_sms_service
        
        sms_service = get_sms_service()
        results = await sms_service.send_emergency_broadcast(
            phone_numbers=request.phone_numbers,
            message_body=request.message,
        )
        
        return results
    except ImportError:
        return {
            "success": False,
            "error": "SMS service not configured",
        }


@app.get("/api/notifications/sms/status", tags=["mobile"])
async def get_sms_status() -> dict:
    """Get SMS service status."""
    try:
        from backend.notifications.sms_service import get_sms_service
        
        sms_service = get_sms_service()
        return sms_service.get_status()
    except ImportError:
        return {
            "configured": False,
            "error": "SMS service not available",
        }
