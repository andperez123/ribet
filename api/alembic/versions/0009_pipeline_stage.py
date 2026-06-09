"""Add pipeline_stage to ingest_jobs for upload progress UI."""

from alembic import op
import sqlalchemy as sa

revision = "0009_pipeline_stage"
down_revision = "0008_report_narratives"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ingest_jobs",
        sa.Column("pipeline_stage", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ingest_jobs", "pipeline_stage")
