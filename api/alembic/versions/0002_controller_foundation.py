"""Controller foundation — data_gap_requests table.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_gap_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("gap_type", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("recommended_uploads", sa.JSON(), nullable=True),
        sa.Column("requested_report_types", sa.JSON(), nullable=True),
        sa.Column("requested_sector", sa.String(32), nullable=True),
        sa.Column("confidence_if_uploaded", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_gap_org_status", "data_gap_requests", ["org_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_data_gap_org_status", table_name="data_gap_requests")
    op.drop_table("data_gap_requests")
