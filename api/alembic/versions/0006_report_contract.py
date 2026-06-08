"""Report generation contract JSON column.

Revision ID: 0006
Revises: 0005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "operational_reports",
        sa.Column("report_contract", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("operational_reports", "report_contract")
