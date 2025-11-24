"""Initial schema for auth and events

Revision ID: 001
Revises:
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')

    # Create enum types
    op.execute("CREATE TYPE roleenum AS ENUM ('admin', 'analyst', 'viewer');")
    op.execute("""
        CREATE TYPE eventcategory AS ENUM (
            'protest', 'crime', 'religious_freedom', 'cultural_tension',
            'political', 'infrastructure', 'health', 'migration',
            'economic', 'weather', 'community_event', 'other'
        );
    """)
    op.execute("CREATE TYPE sentimentenum AS ENUM ('positive', 'neutral', 'negative');")
    op.execute("CREATE TYPE stabilitytrend AS ENUM ('increasing', 'decreasing', 'neutral');")

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('region_of_interest', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create user_organization association table
    op.create_table(
        'user_organization',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', postgresql.ENUM('admin', 'analyst', 'viewer', name='roleenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('url', sa.String(1000), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_fetch_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('fetch_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_sources_name', 'sources', ['name'])

    # Create events table
    op.create_table(
        'events',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('summary', sa.String(500), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('location_point', geoalchemy2.Geometry(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lon', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('category', postgresql.ENUM(
            'protest', 'crime', 'religious_freedom', 'cultural_tension',
            'political', 'infrastructure', 'health', 'migration',
            'economic', 'weather', 'community_event', 'other',
            name='eventcategory'
        ), nullable=False),
        sa.Column('sub_category', sa.String(100), nullable=True),
        sa.Column('sentiment', postgresql.ENUM('positive', 'neutral', 'negative', name='sentimentenum'), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('stability_trend', postgresql.ENUM('increasing', 'decreasing', 'neutral', name='stabilitytrend'), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source_list', postgresql.JSON(), nullable=True),
        sa.Column('entity_list', postgresql.JSON(), nullable=True),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_events_timestamp', 'events', ['timestamp'])
    op.create_index('ix_events_category', 'events', ['category'])
    op.create_index('ix_events_location_name', 'events', ['location_name'])
    op.create_index('ix_events_cluster_id', 'events', ['cluster_id'])
    op.create_index('idx_events_location_point', 'events', ['location_point'], postgresql_using='gist')


def downgrade() -> None:
    # Drop tables
    op.drop_table('events')
    op.drop_table('sources')
    op.drop_table('user_organization')
    op.drop_table('users')
    op.drop_table('organizations')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS stabilitytrend;')
    op.execute('DROP TYPE IF EXISTS sentimentenum;')
    op.execute('DROP TYPE IF EXISTS eventcategory;')
    op.execute('DROP TYPE IF EXISTS roleenum;')
