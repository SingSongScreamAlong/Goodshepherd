"""
Monitoring and health check endpoints for The Good Shepherd API.
Provides detailed health checks, metrics, and readiness/liveness probes.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.core.monitoring import (
    get_overall_health,
    get_readiness_status,
    get_liveness_status,
    get_system_metrics,
    HealthStatus,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health/detailed")
def detailed_health_check():
    """
    Detailed health check with component-level status.

    Returns comprehensive health information for all system components
    including database, cache, and worker processes.

    Returns:
        Detailed health status with component breakdowns
    """
    health = get_overall_health()

    # Return appropriate HTTP status code
    if health["status"] == HealthStatus.UNHEALTHY:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health,
        )
    elif health["status"] == HealthStatus.DEGRADED:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health,
        )
    else:
        return health


@router.get("/health/live")
def liveness_probe():
    """
    Liveness probe endpoint for Kubernetes/container orchestration.

    This endpoint checks if the application process is alive and responding.
    It should return 200 OK as long as the process is running.

    Returns:
        Simple liveness status
    """
    return get_liveness_status()


@router.get("/health/ready")
def readiness_probe():
    """
    Readiness probe endpoint for Kubernetes/container orchestration.

    This endpoint checks if the application is ready to serve traffic.
    It verifies that critical dependencies (database, etc.) are available.

    Returns:
        Readiness status with dependency checks
    """
    readiness = get_readiness_status()

    if not readiness["ready"]:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=readiness,
        )

    return readiness


@router.get("/metrics")
def get_metrics():
    """
    Get application metrics.

    Returns system-wide metrics including event counts, user counts,
    and recent activity statistics.

    Returns:
        Dictionary of application metrics
    """
    return get_system_metrics()


@router.get("/version")
def get_version():
    """
    Get application version information.

    Returns:
        Version and build information
    """
    return {
        "version": "0.8.0",
        "name": "The Good Shepherd",
        "description": "OSINT Intelligence Platform for Missionaries in Europe",
        "phase": "Phase 8 - Production Ready",
    }
