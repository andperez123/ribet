"""Report narratives table for versioned AI analyst output.

Revision ID: 0008
Revises: 0007
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_narratives",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False, server_default="analyst_output.v1"),
        sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default="ai_analyst.v1"),
        sa.Column("verification_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("verification_failures", sa.JSON(), nullable=True),
        sa.Column("model_name", sa.String(length=64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="ai"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["operational_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
    )
    op.create_index("ix_report_narratives_report", "report_narratives", ["report_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_report_narratives_report", table_name="report_narratives")
    op.drop_table("report_narratives")
