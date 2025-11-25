"""Add dossiers and watchlists tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE dossiertype AS ENUM (
            'location', 'organization', 'group', 'topic', 'person'
        );
    """)
    op.execute("""
        CREATE TYPE watchlistpriority AS ENUM (
            'low', 'medium', 'high', 'critical'
        );
    """)

    # Create dossiers table
    op.create_table(
        'dossiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('dossier_type', postgresql.ENUM('location', 'organization', 'group', 'topic', 'person', name='dossiertype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('aliases', postgresql.JSON(), nullable=True),
        sa.Column('location_lat', sa.String(20), nullable=True),
        sa.Column('location_lon', sa.String(20), nullable=True),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('event_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_event_timestamp', sa.DateTime(), nullable=True),
        sa.Column('first_event_timestamp', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_dossiers_organization_id', 'dossiers', ['organization_id'])
    op.create_index('ix_dossiers_name', 'dossiers', ['name'])
    op.create_index('ix_dossiers_dossier_type', 'dossiers', ['dossier_type'])
    op.create_index('ix_dossiers_location_name', 'dossiers', ['location_name'])

    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', postgresql.ENUM('low', 'medium', 'high', 'critical', name='watchlistpriority'), nullable=False, server_default='medium'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('notification_enabled', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_watchlists_organization_id', 'watchlists', ['organization_id'])
    op.create_index('ix_watchlists_user_id', 'watchlists', ['user_id'])

    # Create association table for watchlist-dossier many-to-many
    op.create_table(
        'watchlist_dossier',
        sa.Column('watchlist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dossier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dossier_id'], ['dossiers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('watchlist_id', 'dossier_id')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('watchlist_dossier')
    op.drop_table('watchlists')
    op.drop_table('dossiers')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS watchlistpriority;')
    op.execute('DROP TYPE IF EXISTS dossiertype;')
