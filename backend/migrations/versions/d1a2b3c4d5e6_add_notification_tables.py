"""Add notification and alert tables.

Revision ID: d1a2b3c4d5e6
Revises: c05c40906a55
Create Date: 2024-11-28 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d1a2b3c4d5e6"
down_revision = "c05c40906a55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Notification preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        
        # Channel enablement
        sa.Column("email_enabled", sa.Boolean(), default=True),
        sa.Column("sms_enabled", sa.Boolean(), default=False),
        sa.Column("whatsapp_enabled", sa.Boolean(), default=False),
        sa.Column("push_enabled", sa.Boolean(), default=True),
        sa.Column("webhook_enabled", sa.Boolean(), default=False),
        
        # Contact info
        sa.Column("phone_number", sa.String(32), nullable=True),
        sa.Column("webhook_url", sa.String(512), nullable=True),
        sa.Column("webhook_secret", sa.String(128), nullable=True),
        
        # Digest settings
        sa.Column("digest_frequency", sa.String(16), default="daily"),
        sa.Column("digest_time", sa.Time(), nullable=True),
        sa.Column("timezone", sa.String(64), default="UTC"),
        
        # Filtering
        sa.Column("min_priority", sa.String(16), default="medium"),
        sa.Column("watched_regions", sa.JSON(), nullable=True),
        sa.Column("watched_categories", sa.JSON(), nullable=True),
        sa.Column("muted_sources", sa.JSON(), nullable=True),
        
        # Quiet hours
        sa.Column("quiet_hours_enabled", sa.Boolean(), default=False),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.Column("quiet_hours_override_critical", sa.Boolean(), default=True),
        
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        comment="User notification channel preferences",
    )

    # Alert subscriptions table
    op.create_table(
        "alert_subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("rule_id", sa.String(36), nullable=False, index=True),
        
        sa.Column("channels", sa.JSON(), nullable=True),
        sa.Column("priority_override", sa.String(16), nullable=True),
        sa.Column("enabled", sa.Boolean(), default=True),
        
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="CASCADE"),
        comment="User subscriptions to alert rules",
    )

    # Sent notifications table
    op.create_table(
        "sent_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("event_id", sa.String(36), nullable=False, index=True),
        sa.Column("rule_id", sa.String(36), nullable=True),
        
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), default="pending"),
        
        sa.Column("recipient", sa.String(256), nullable=False),
        sa.Column("message_id", sa.String(128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="SET NULL"),
        comment="History of sent notifications",
    )

    # Alert acknowledgments table
    op.create_table(
        "alert_acknowledgments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("event_id", sa.String(36), nullable=False, index=True),
        sa.Column("rule_id", sa.String(36), nullable=True),
        
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="SET NULL"),
        comment="User acknowledgments of alerts",
    )

    # Create indexes for common queries
    op.create_index(
        "ix_sent_notifications_user_event",
        "sent_notifications",
        ["user_id", "event_id"],
    )
    op.create_index(
        "ix_sent_notifications_status_created",
        "sent_notifications",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("alert_acknowledgments")
    op.drop_table("sent_notifications")
    op.drop_table("alert_subscriptions")
    op.drop_table("notification_preferences")
