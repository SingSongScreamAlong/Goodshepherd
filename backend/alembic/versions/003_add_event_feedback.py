"""Add event feedback table for user feedback collection

Revision ID: 003
Revises: 002
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create event_feedback table
    op.create_table(
        'event_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for efficient querying
    op.create_index('ix_event_feedback_event_id', 'event_feedback', ['event_id'])
    op.create_index('ix_event_feedback_user_id', 'event_feedback', ['user_id'])
    op.create_index('ix_event_feedback_feedback_type', 'event_feedback', ['feedback_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_event_feedback_feedback_type', table_name='event_feedback')
    op.drop_index('ix_event_feedback_user_id', table_name='event_feedback')
    op.drop_index('ix_event_feedback_event_id', table_name='event_feedback')

    # Drop table
    op.drop_table('event_feedback')
