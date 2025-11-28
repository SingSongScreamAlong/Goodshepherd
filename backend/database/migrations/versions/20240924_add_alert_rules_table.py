"""Add alert_rules table."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20240924_add_alert_rules_table"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


THREAT_LEVEL_ENUM = sa.Enum("low", "medium", "high", "critical", name="threat_level")
PRIORITY_ENUM = sa.Enum("low", "medium", "high", "critical", name="alert_priority")


def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("regions", sa.JSON(), nullable=True),
        sa.Column("categories", sa.JSON(), nullable=True),
        sa.Column("minimum_threat", THREAT_LEVEL_ENUM, nullable=False, server_default="medium"),
        sa.Column("minimum_credibility", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("lookback_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("priority", PRIORITY_ENUM, nullable=False, server_default="high"),
        sa.Column("auto_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="Alert rules for automated notifications",
    )


def downgrade() -> None:
    op.drop_table("alert_rules")
    THREAT_LEVEL_ENUM.drop(op.get_bind(), checkfirst=False)
    PRIORITY_ENUM.drop(op.get_bind(), checkfirst=False)
