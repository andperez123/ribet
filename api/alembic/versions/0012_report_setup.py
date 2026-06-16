"""Report setup: draft context, source jobs join table, generation_context on reports."""

from alembic import op
import sqlalchemy as sa

revision = "0012_report_setup"
down_revision = "0011_purchase_sales_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "report_context_drafts",
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("context_schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_job_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("manual_notes", sa.Text(), nullable=True),
        sa.Column("excluded_finding_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence_overrides", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("narrative_overrides", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("org_id"),
    )

    op.add_column(
        "operational_reports",
        sa.Column("generation_context", sa.JSON(), nullable=True),
    )

    op.create_table(
        "operational_report_source_jobs",
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("ingest_job_id", sa.Uuid(), nullable=False),
        sa.Column(
            "included_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["report_id"], ["operational_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ingest_job_id"], ["ingest_jobs.id"]),
        sa.PrimaryKeyConstraint("report_id", "ingest_job_id"),
    )
    op.create_index(
        "ix_report_source_jobs_job",
        "operational_report_source_jobs",
        ["ingest_job_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_report_source_jobs_job", table_name="operational_report_source_jobs")
    op.drop_table("operational_report_source_jobs")
    op.drop_column("operational_reports", "generation_context")
    op.drop_table("report_context_drafts")
