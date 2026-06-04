"""Report insights — digest, domain insights, coverage, analysis metadata.

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "operational_reports",
        sa.Column("data_digest", sa.JSON(), nullable=True),
    )
    op.add_column(
        "operational_reports",
        sa.Column("domain_insights", sa.JSON(), nullable=True),
    )
    op.add_column(
        "operational_reports",
        sa.Column("data_coverage", sa.JSON(), nullable=True),
    )
    op.add_column(
        "operational_reports",
        sa.Column("analysis_metadata", sa.JSON(), nullable=True),
    )
    op.add_column(
        "operational_reports",
        sa.Column("analyst_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "operational_reports",
        sa.Column("management_questions", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("operational_reports", "management_questions")
    op.drop_column("operational_reports", "analyst_summary")
    op.drop_column("operational_reports", "analysis_metadata")
    op.drop_column("operational_reports", "data_coverage")
    op.drop_column("operational_reports", "domain_insights")
    op.drop_column("operational_reports", "data_digest")
