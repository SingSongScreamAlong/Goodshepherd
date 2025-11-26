"""Add organization settings table for tenant-level configuration

Revision ID: 005
Revises: 004
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organization_settings table
    op.create_table(
        'organization_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),

        # Default Filters
        sa.Column('default_categories', postgresql.JSON(), nullable=True),
        sa.Column('default_sentiment_filter', sa.String(50), nullable=True),
        sa.Column('default_min_relevance', sa.Float(), nullable=True, server_default='0.5'),

        # Alert Thresholds
        sa.Column('high_priority_threshold', sa.Float(), nullable=True, server_default='0.8'),
        sa.Column('alert_categories', postgresql.JSON(), nullable=True),
        sa.Column('alert_sentiment_types', postgresql.JSON(), nullable=True),

        # Feature Toggles
        sa.Column('enable_email_alerts', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enable_clustering', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_feedback_collection', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_audit_logging', sa.Boolean(), nullable=False, server_default='true'),

        # Display Preferences
        sa.Column('default_map_zoom', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('default_map_center_lat', sa.Float(), nullable=True),
        sa.Column('default_map_center_lon', sa.Float(), nullable=True),
        sa.Column('events_per_page', sa.Integer(), nullable=True, server_default='20'),

        # Data Retention
        sa.Column('event_retention_days', sa.Integer(), nullable=True),
        sa.Column('audit_log_retention_days', sa.Integer(), nullable=True, server_default='365'),

        # Regional Focus
        sa.Column('focus_regions', postgresql.JSON(), nullable=True),
        sa.Column('exclude_regions', postgresql.JSON(), nullable=True),

        # Custom Configuration
        sa.Column('custom_config', postgresql.JSON(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Foreign Keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('ix_organization_settings_organization_id', 'organization_settings', ['organization_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_organization_settings_organization_id', table_name='organization_settings')

    # Drop table
    op.drop_table('organization_settings')
