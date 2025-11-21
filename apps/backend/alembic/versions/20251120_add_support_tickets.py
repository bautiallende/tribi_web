"""add support tickets and user notes

Revision ID: 20251120_add_support_tickets
Revises: 20251120_add_invoices_table
Create Date: 2025-11-20 15:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_add_support_tickets"
down_revision = "20251120_add_invoices_table"
branch_labels = None
depends_on = None

support_ticket_status = sa.Enum(
    "open", "in_progress", "resolved", "archived", name="supportticketstatus"
)
support_ticket_priority = sa.Enum("low", "normal", "high", name="supportticketpriority")


def upgrade() -> None:
    support_ticket_status.create(op.get_bind(), checkfirst=True)
    support_ticket_priority.create(op.get_bind(), checkfirst=True)

    op.add_column("users", sa.Column("internal_notes", sa.Text(), nullable=True))

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column(
            "status",
            support_ticket_status,
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "priority",
            support_ticket_priority,
            nullable=False,
            server_default="normal",
        ),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("ix_support_tickets_order_id", "support_tickets", ["order_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_support_tickets_status", table_name="support_tickets")
    op.drop_index("ix_support_tickets_order_id", table_name="support_tickets")
    op.drop_index("ix_support_tickets_user_id", table_name="support_tickets")
    op.drop_table("support_tickets")

    op.drop_column("users", "internal_notes")

    support_ticket_priority.drop(op.get_bind(), checkfirst=True)
    support_ticket_status.drop(op.get_bind(), checkfirst=True)
