"""Add audit logs table for governance and accountability

Revision ID: 004
Revises: 003
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('object_type', sa.String(50), nullable=False),
        sa.Column('object_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # Create indexes for efficient querying
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_organization_id', 'audit_logs', ['organization_id'])
    op.create_index('ix_audit_logs_action_type', 'audit_logs', ['action_type'])
    op.create_index('ix_audit_logs_object_type', 'audit_logs', ['object_type'])
    op.create_index('ix_audit_logs_object_id', 'audit_logs', ['object_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_object_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_object_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_organization_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')

    # Drop table
    op.drop_table('audit_logs')
