"""Initial schema for Good Shepherd

Revision ID: 0001
Revises: 
Create Date: 2025-11-26

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Events table
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("link", sa.String(length=2048), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("geocode", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("raw", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("credibility_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("threat_level", sa.String(length=32), nullable=True),
        sa.Column("duplicate_of", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_fetched_at", "events", ["fetched_at"], unique=False)
    op.create_index("ix_events_region", "events", ["region"], unique=False)
    op.create_index("ix_events_threat_level", "events", ["threat_level"], unique=False)
    op.create_index("ix_events_verification_status", "events", ["verification_status"], unique=False)

    # Reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("report_type", sa.String(length=64), nullable=False, server_default="daily_sitrep"),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("generated_by", sa.String(length=128), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_event_ids", postgresql.ARRAY(sa.String(length=36)), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_generated_at", "reports", ["generated_at"], unique=False)
    op.create_index("ix_reports_report_type", "reports", ["report_type"], unique=False)

    # Alert rules table
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("regions", postgresql.ARRAY(sa.String(length=128)), nullable=True),
        sa.Column("categories", postgresql.ARRAY(sa.String(length=64)), nullable=True),
        sa.Column("minimum_threat", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("minimum_credibility", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("lookback_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="high"),
        sa.Column("auto_ack", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_rules_enabled", "alert_rules", ["enabled"], unique=False)
    op.create_index("ix_alert_rules_priority", "alert_rules", ["priority"], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_alert_rules_priority", table_name="alert_rules")
    op.drop_index("ix_alert_rules_enabled", table_name="alert_rules")
    op.drop_table("alert_rules")

    op.drop_index("ix_reports_report_type", table_name="reports")
    op.drop_index("ix_reports_generated_at", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_events_verification_status", table_name="events")
    op.drop_index("ix_events_threat_level", table_name="events")
    op.drop_index("ix_events_region", table_name="events")
    op.drop_index("ix_events_fetched_at", table_name="events")
    op.drop_table("events")
