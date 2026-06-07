"""Vendor aging bucket breakdown columns.

Revision ID: 0005
Revises: 0004
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("vendors")}
    if "days_overdue" not in cols:
        op.add_column("vendors", sa.Column("days_overdue", sa.Integer(), nullable=True))
    if "aging_bucket" not in cols:
        op.add_column("vendors", sa.Column("aging_bucket", sa.String(64), nullable=True))
    if "bucket_breakdown" not in cols:
        op.add_column("vendors", sa.Column("bucket_breakdown", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("vendors", "bucket_breakdown")
    op.drop_column("vendors", "aging_bucket")
    op.drop_column("vendors", "days_overdue")
