"""add invoices table for billing exports

Revision ID: 20251120_add_invoices_table
Revises: 20251120_fix_inventory_enum_case
Create Date: 2025-11-20 14:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_add_invoices_table"
down_revision = "20251120_fix_inventory_enum_case"
branch_labels = None
depends_on = None

invoice_status_enum = sa.Enum("draft", "issued", "void", name="invoicestatus")


def upgrade() -> None:
    invoice_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_number", sa.String(length=32), nullable=False, unique=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column(
            "amount_minor_units",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "tax_minor_units",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status", invoice_status_enum, nullable=False, server_default="issued"
        ),
        sa.Column(
            "issued_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("pdf_url", sa.String(length=512), nullable=True),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_invoices_order_id", "invoices", ["order_id"])
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])
    op.create_index("ix_invoices_issued_at", "invoices", ["issued_at"])


def downgrade() -> None:
    op.drop_index("ix_invoices_issued_at", table_name="invoices")
    op.drop_index("ix_invoices_user_id", table_name="invoices")
    op.drop_index("ix_invoices_order_id", table_name="invoices")
    op.drop_table("invoices")
    invoice_status_enum.drop(op.get_bind(), checkfirst=True)
