"""
Database connection and session management for The Good Shepherd.
Supports PostgreSQL with PostGIS extension for geospatial queries.
"""
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from geoalchemy2 import Geometry

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


@event.listens_for(engine, "connect")
def enable_postgis(dbapi_connection, connection_record):
    """Enable PostGIS extension on database connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        dbapi_connection.commit()
        logger.info("PostGIS extension enabled")
    except Exception as e:
        logger.warning("Could not enable PostGIS", error=str(e))
    finally:
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Database session that is automatically closed after use.

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in models.

    Note: In production, use Alembic migrations instead.
    """
    logger.info("Initializing database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False


def check_postgis_available() -> bool:
    """
    Check if PostGIS extension is available and enabled.

    Returns:
        True if PostGIS is available, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT PostGIS_version();")
            )
            version = result.scalar()
            logger.info("PostGIS available", version=version)
            return True
    except Exception as e:
        logger.error("PostGIS not available", error=str(e))
        return False
