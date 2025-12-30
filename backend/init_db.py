#!/usr/bin/env python3
"""
Minimal database initialization script - creates core tables only.
Uses direct SQLAlchemy without importing the full application.
"""

import os
from sqlalchemy import create_engine, text, Column, String, Boolean, DateTime, Float, Text, Integer, ForeignKey, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM

# Get database URL from environment or default
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://conradweeden@localhost:5432/goodshepherd'
)

print(f"Connecting to: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define minimal models directly here
class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))
    last_login = Column(DateTime, nullable=True)

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    region_of_interest = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

user_organization = Table(
    'user_organization', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('organization_id', UUID(as_uuid=True), ForeignKey('organizations.id'), primary_key=True),
    Column('role', String(50), nullable=False),
    Column('created_at', DateTime, server_default=text('now()'))
)

class Source(Base):
    __tablename__ = 'sources'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    trust_baseline = Column(Integer, default=50)
    last_fetch_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class Region(Base):
    __tablename__ = 'regions'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    iso_code = Column(String(10), nullable=True)
    region_type = Column(String(50), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=True)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    status = Column(String(20), default='green')
    status_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class Event(Base):
    __tablename__ = 'events'
    event_id = Column(UUID(as_uuid=True), primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    summary = Column(String(500), nullable=False)
    full_text = Column(Text, nullable=True)
    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default='unverified')
    severity = Column(String(20), default='medium')
    confidence_score = Column(Float, nullable=True)
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class RawObservation(Base):
    __tablename__ = 'raw_observations'
    id = Column(UUID(as_uuid=True), primary_key=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey('sources.id'), nullable=False)
    collected_at = Column(DateTime, nullable=False)
    content_type = Column(String(20), nullable=False)
    raw_text = Column(Text, nullable=True)
    title = Column(String(500), nullable=True)
    original_url = Column(String(2000), nullable=True)
    content_hash = Column(String(64), nullable=False, unique=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class IncidentEvidence(Base):
    __tablename__ = 'incident_evidence'
    id = Column(UUID(as_uuid=True), primary_key=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey('events.event_id'), nullable=False)
    observation_id = Column(UUID(as_uuid=True), ForeignKey('raw_observations.id'), nullable=False)
    evidence_type = Column(String(20), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class Indicator(Base):
    __tablename__ = 'indicators'
    id = Column(UUID(as_uuid=True), primary_key=True)
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=False)
    name = Column(String(255), nullable=False)
    domain = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    value = Column(Float, default=50.0)
    delta_24h = Column(Float, nullable=True)
    delta_7d = Column(Float, nullable=True)
    confidence = Column(Float, default=50.0)
    measured_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class Report(Base):
    __tablename__ = 'reports'
    id = Column(UUID(as_uuid=True), primary_key=True)
    report_type = Column(String(20), nullable=False)
    title = Column(String(300), nullable=False)
    status = Column(String(20), default='draft')
    executive_summary = Column(Text, nullable=True)
    narrative_markdown = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))
    published_at = Column(DateTime, nullable=True)

def init_database():
    """Create all tables."""
    print("Testing connection...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Set alembic version
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) PRIMARY KEY
            )
        """))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('006_world_awareness_models')"))
        conn.commit()
    print("Alembic version set.")
    
    return True

if __name__ == "__main__":
    import sys
    success = init_database()
    sys.exit(0 if success else 1)
