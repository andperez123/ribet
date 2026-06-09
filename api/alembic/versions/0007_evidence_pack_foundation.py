"""Evidence pack foundation — finding IDs and evidence_packs table.

Revision ID: 0007
Revises: 0006
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "operational_findings",
        sa.Column("finding_id", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "operational_findings",
        sa.Column("finding_instance_id", sa.String(length=64), nullable=True),
    )
    op.create_table(
        "evidence_packs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("period_label", sa.String(length=16), nullable=False),
        sa.Column("pack", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False, server_default="evidence_pack.v1"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["operational_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
    )
    op.create_index("ix_evidence_packs_report", "evidence_packs", ["report_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_evidence_packs_report", table_name="evidence_packs")
    op.drop_table("evidence_packs")
    op.drop_column("operational_findings", "finding_instance_id")
    op.drop_column("operational_findings", "finding_id")
