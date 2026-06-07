"""Data normalization — ingest metadata, series snapshots, improvement notes.

Revision ID: 0004
Revises: 0003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ingest_jobs", sa.Column("user_description", sa.String(512), nullable=True))
    op.add_column("ingest_jobs", sa.Column("content_hash", sa.String(64), nullable=True))
    op.add_column("ingest_jobs", sa.Column("schema_fingerprint", sa.String(64), nullable=True))
    op.add_column("ingest_jobs", sa.Column("detected_period", sa.String(16), nullable=True))
    op.add_column("ingest_jobs", sa.Column("row_count", sa.Integer(), nullable=True))
    op.add_column("ingest_jobs", sa.Column("mapping_metadata", sa.JSON(), nullable=True))
    op.add_column("ingest_jobs", sa.Column("mapping_confidence", sa.Float(), nullable=True))
    op.add_column("ingest_jobs", sa.Column("mapping_status", sa.String(32), nullable=True))
    op.add_column("ingest_jobs", sa.Column("intake_metadata", sa.JSON(), nullable=True))
    op.add_column("ingest_jobs", sa.Column("duplicate_of_job_id", sa.Uuid(), nullable=True))

    op.add_column("operational_reports", sa.Column("period_label", sa.String(16), nullable=True))
    op.add_column("operational_reports", sa.Column("improvement_notes", sa.JSON(), nullable=True))

    op.create_table(
        "data_series",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("report_type", sa.String(64), nullable=False),
        sa.Column("schema_fingerprint", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_data_series_org_fingerprint",
        "data_series",
        ["org_id", "schema_fingerprint", "report_type"],
        unique=True,
    )

    op.create_table(
        "series_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("series_id", sa.Uuid(), sa.ForeignKey("data_series.id"), nullable=False),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("period", sa.String(16), nullable=False),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("ingest_jobs.id"), nullable=True),
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("operational_reports.id"), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("kpi_summary", sa.JSON(), nullable=True),
        sa.Column("improvement_notes", sa.JSON(), nullable=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_series_snapshots_series_at",
        "series_snapshots",
        ["series_id", "snapshot_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_series_snapshots_series_at", table_name="series_snapshots")
    op.drop_table("series_snapshots")
    op.drop_index("ix_data_series_org_fingerprint", table_name="data_series")
    op.drop_table("data_series")
    op.drop_column("operational_reports", "improvement_notes")
    op.drop_column("operational_reports", "period_label")
    op.drop_column("ingest_jobs", "duplicate_of_job_id")
    op.drop_column("ingest_jobs", "intake_metadata")
    op.drop_column("ingest_jobs", "mapping_status")
    op.drop_column("ingest_jobs", "mapping_confidence")
    op.drop_column("ingest_jobs", "mapping_metadata")
    op.drop_column("ingest_jobs", "row_count")
    op.drop_column("ingest_jobs", "detected_period")
    op.drop_column("ingest_jobs", "schema_fingerprint")
    op.drop_column("ingest_jobs", "content_hash")
    op.drop_column("ingest_jobs", "user_description")
