"""
Main FastAPI application entrypoint for The Good Shepherd.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging import setup_logging, get_logger
from backend.core.database import check_db_connection, check_postgis_available
from backend.core.middleware import RequestTrackingMiddleware, SecurityHeadersMiddleware
from backend.routers import auth, events, ingest, dossiers, dashboard, monitoring

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("The Good Shepherd API starting up")

    # Check database connection
    if not check_db_connection():
        logger.error("Database connection failed on startup")
    else:
        logger.info("Database connection successful")

    # Check PostGIS
    if not check_postgis_available():
        logger.warning("PostGIS not available")
    else:
        logger.info("PostGIS available")

    yield

    # Shutdown
    logger.info("The Good Shepherd API shutting down")


# Create FastAPI app
app = FastAPI(
    title="The Good Shepherd",
    description="Autonomous OSINT Intelligence Platform for Missionaries in Europe",
    version="0.8.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint.

    Returns:
        Status of the API and database
    """
    db_status = check_db_connection()
    postgis_status = check_postgis_available()

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "postgis": "available" if postgis_status else "unavailable",
    }


@app.get("/", tags=["root"])
def root():
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": "The Good Shepherd - OSINT Intelligence Platform",
        "version": "0.8.0",
        "documentation": "/docs"
    }


# Include routers
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(ingest.router)
app.include_router(dossiers.router)
app.include_router(dossiers.watchlist_router)
app.include_router(dashboard.router)
app.include_router(monitoring.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
