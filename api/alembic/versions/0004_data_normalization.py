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


def _insp():
    return sa.inspect(op.get_bind())


def _table_exists(name: str) -> bool:
    return _insp().has_table(name)


def _column_exists(table: str, column: str) -> bool:
    if not _table_exists(table):
        return False
    return column in {c["name"] for c in _insp().get_columns(table)}


def _add_column_if_missing(table: str, column: str, col: sa.Column) -> None:
    if not _column_exists(table, column):
        op.add_column(table, col)


def upgrade() -> None:
    # 0003 columns may be missing on DBs bootstrapped via create_all fallback.
    for col_name, col in (
        ("data_digest", sa.Column("data_digest", sa.JSON(), nullable=True)),
        ("domain_insights", sa.Column("domain_insights", sa.JSON(), nullable=True)),
        ("data_coverage", sa.Column("data_coverage", sa.JSON(), nullable=True)),
        ("analysis_metadata", sa.Column("analysis_metadata", sa.JSON(), nullable=True)),
        ("analyst_summary", sa.Column("analyst_summary", sa.Text(), nullable=True)),
        ("management_questions", sa.Column("management_questions", sa.JSON(), nullable=True)),
    ):
        _add_column_if_missing("operational_reports", col_name, col)

    _add_column_if_missing(
        "ingest_jobs", "user_description", sa.Column("user_description", sa.String(512), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs", "content_hash", sa.Column("content_hash", sa.String(64), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs",
        "schema_fingerprint",
        sa.Column("schema_fingerprint", sa.String(64), nullable=True),
    )
    _add_column_if_missing(
        "ingest_jobs", "detected_period", sa.Column("detected_period", sa.String(16), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs", "row_count", sa.Column("row_count", sa.Integer(), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs", "mapping_metadata", sa.Column("mapping_metadata", sa.JSON(), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs",
        "mapping_confidence",
        sa.Column("mapping_confidence", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "ingest_jobs", "mapping_status", sa.Column("mapping_status", sa.String(32), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs", "intake_metadata", sa.Column("intake_metadata", sa.JSON(), nullable=True)
    )
    _add_column_if_missing(
        "ingest_jobs",
        "duplicate_of_job_id",
        sa.Column("duplicate_of_job_id", sa.Uuid(), nullable=True),
    )

    _add_column_if_missing(
        "operational_reports", "period_label", sa.Column("period_label", sa.String(16), nullable=True)
    )
    _add_column_if_missing(
        "operational_reports",
        "improvement_notes",
        sa.Column("improvement_notes", sa.JSON(), nullable=True),
    )

    if not _table_exists("data_series"):
        op.create_table(
            "data_series",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("report_type", sa.String(64), nullable=False),
            sa.Column("schema_fingerprint", sa.String(64), nullable=False),
            sa.Column("display_name", sa.String(256), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if not _insp().has_index("data_series", "ix_data_series_org_fingerprint"):
        op.create_index(
            "ix_data_series_org_fingerprint",
            "data_series",
            ["org_id", "schema_fingerprint", "report_type"],
            unique=True,
        )

    if not _table_exists("series_snapshots"):
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
    if not _insp().has_index("series_snapshots", "ix_series_snapshots_series_at"):
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
