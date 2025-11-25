"""
Monitoring and health check utilities for The Good Shepherd.
Provides detailed system health checks and metrics.
"""
import time
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal, check_db_connection, check_postgis_available
from backend.core.logging import get_logger

logger = get_logger(__name__)


class HealthStatus:
    """Health status constants."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and performance.

    Returns:
        Dictionary with database health status and metrics
    """
    start_time = time.time()
    status = HealthStatus.HEALTHY
    details = {}

    try:
        # Basic connection check
        is_connected = check_db_connection()
        if not is_connected:
            return {
                "status": HealthStatus.UNHEALTHY,
                "connected": False,
                "error": "Cannot connect to database",
            }

        # Check PostGIS
        has_postgis = check_postgis_available()
        details["postgis_available"] = has_postgis

        # Check query performance
        db = SessionLocal()
        try:
            # Simple query to test responsiveness
            result = db.execute(text("SELECT 1")).scalar()

            # Get connection pool stats
            pool = db.get_bind().pool
            details["pool_size"] = pool.size()
            details["checked_out"] = pool.checkedout()
            details["overflow"] = pool.overflow()

            # Check table accessibility
            result = db.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )).scalar()
            details["public_tables"] = result

        except Exception as e:
            logger.error("Database health check query failed", error=str(e))
            status = HealthStatus.DEGRADED
            details["query_error"] = str(e)
        finally:
            db.close()

        # Check response time
        duration = time.time() - start_time
        details["response_time_ms"] = round(duration * 1000, 2)

        # Consider degraded if slow
        if duration > 1.0:
            status = HealthStatus.DEGRADED

        return {
            "status": status,
            "connected": True,
            **details,
        }

    except Exception as e:
        logger.error("Database health check failed", error=str(e), exc_info=True)
        return {
            "status": HealthStatus.UNHEALTHY,
            "connected": False,
            "error": str(e),
        }


def get_system_metrics() -> Dict[str, Any]:
    """
    Collect system-wide metrics.

    Returns:
        Dictionary with system metrics
    """
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": None,  # Could be tracked with app startup time
    }

    # Database metrics
    try:
        db = SessionLocal()
        try:
            # Count events
            event_count = db.execute(
                text("SELECT COUNT(*) FROM events")
            ).scalar()
            metrics["total_events"] = event_count

            # Count users
            user_count = db.execute(
                text("SELECT COUNT(*) FROM users")
            ).scalar()
            metrics["total_users"] = user_count

            # Count organizations
            org_count = db.execute(
                text("SELECT COUNT(*) FROM organizations")
            ).scalar()
            metrics["total_organizations"] = org_count

            # Count dossiers
            dossier_count = db.execute(
                text("SELECT COUNT(*) FROM dossiers")
            ).scalar()
            metrics["total_dossiers"] = dossier_count

            # Recent events (last 24 hours)
            recent_events = db.execute(
                text(
                    "SELECT COUNT(*) FROM events "
                    "WHERE timestamp >= NOW() - INTERVAL '24 hours'"
                )
            ).scalar()
            metrics["events_last_24h"] = recent_events

        finally:
            db.close()

    except Exception as e:
        logger.error("Failed to collect system metrics", error=str(e))
        metrics["error"] = str(e)

    return metrics


def check_component_health() -> Dict[str, Dict[str, Any]]:
    """
    Check health of all system components.

    Returns:
        Dictionary mapping component names to health status
    """
    components = {}

    # Database
    components["database"] = check_database_health()

    # Redis (if configured)
    # TODO: Add Redis health check when Redis is actively used

    # Worker processes (if running)
    # TODO: Add worker health check

    return components


def get_overall_health() -> Dict[str, Any]:
    """
    Get overall system health status.

    Returns:
        Dictionary with overall health and component details
    """
    components = check_component_health()

    # Determine overall status
    statuses = [comp["status"] for comp in components.values()]

    if HealthStatus.UNHEALTHY in statuses:
        overall_status = HealthStatus.UNHEALTHY
    elif HealthStatus.DEGRADED in statuses:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": components,
    }


def get_readiness_status() -> Dict[str, Any]:
    """
    Check if the application is ready to serve requests.
    This is used for Kubernetes readiness probes.

    Returns:
        Dictionary with readiness status
    """
    # For readiness, we only care about critical components
    db_connected = check_db_connection()

    return {
        "ready": db_connected,
        "database": "connected" if db_connected else "disconnected",
    }


def get_liveness_status() -> Dict[str, Any]:
    """
    Check if the application is alive (basic health).
    This is used for Kubernetes liveness probes.

    Returns:
        Dictionary with liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
