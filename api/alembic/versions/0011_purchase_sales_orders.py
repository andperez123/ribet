"""Purchase orders and sales orders tables."""

from alembic import op
import sqlalchemy as sa

revision = "0011_purchase_sales_orders"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("po_id", sa.String(length=128), nullable=False),
        sa.Column("vendor_id", sa.String(length=128), nullable=False),
        sa.Column("vendor_name", sa.String(length=512), nullable=True),
        sa.Column("order_date", sa.String(length=32), nullable=True),
        sa.Column("promise_date", sa.String(length=32), nullable=True),
        sa.Column("due_date", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("line_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("open_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("days_late", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("qty_ordered", sa.Float(), nullable=True),
        sa.Column("qty_received", sa.Float(), nullable=True),
        sa.Column("period_label", sa.String(length=16), nullable=False, server_default="unknown"),
        sa.Column("source_job_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_po_org_period", "purchase_orders", ["org_id", "period_label"])

    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.String(length=128), nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.Column("customer_name", sa.String(length=512), nullable=True),
        sa.Column("order_date", sa.String(length=32), nullable=True),
        sa.Column("ship_date", sa.String(length=32), nullable=True),
        sa.Column("promise_date", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("line_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("open_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("days_late", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("qty_ordered", sa.Float(), nullable=True),
        sa.Column("qty_open", sa.Float(), nullable=True),
        sa.Column("period_label", sa.String(length=16), nullable=False, server_default="unknown"),
        sa.Column("source_job_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_so_org_period", "sales_orders", ["org_id", "period_label"])


def downgrade() -> None:
    op.drop_index("ix_so_org_period", table_name="sales_orders")
    op.drop_table("sales_orders")
    op.drop_index("ix_po_org_period", table_name="purchase_orders")
    op.drop_table("purchase_orders")
