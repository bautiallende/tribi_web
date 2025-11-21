"""add due dates and audit trail for support tickets

Revision ID: 20251120_add_support_ticket_sla
Revises: 20251120_add_support_tickets
Create Date: 2025-11-20 18:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_add_support_ticket_sla"
down_revision = "20251120_add_support_tickets"
branch_labels = None
depends_on = None

support_ticket_status = sa.Enum(
    "open", "in_progress", "resolved", "archived", name="supportticketstatus"
)
support_ticket_event_type = sa.Enum(
    "created",
    "status_changed",
    "priority_changed",
    "note_added",
    "reminder_sent",
    "escalated",
    "sla_updated",
    name="supportticketeventtype",
)


def upgrade() -> None:
    bind = op.get_bind()
    support_ticket_event_type.create(bind, checkfirst=True)

    op.add_column("support_tickets", sa.Column("due_at", sa.DateTime(), nullable=True))
    op.add_column(
        "support_tickets",
        sa.Column("last_reminder_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "support_tickets",
        sa.Column(
            "reminder_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "support_tickets",
        sa.Column(
            "escalation_level",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE support_tickets
            SET due_at = CASE priority
                WHEN 'high' THEN DATE_ADD(created_at, INTERVAL 4 HOUR)
                WHEN 'normal' THEN DATE_ADD(created_at, INTERVAL 24 HOUR)
                ELSE DATE_ADD(created_at, INTERVAL 72 HOUR)
            END
            WHERE due_at IS NULL
            """
        )
    )

    op.create_table(
        "support_ticket_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", support_ticket_event_type, nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=True),
        sa.Column("from_status", support_ticket_status, nullable=True),
        sa.Column("to_status", support_ticket_status, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_support_ticket_audit_ticket_id",
        "support_ticket_audit",
        ["ticket_id"],
    )

    # Drop server defaults now that data backfill is complete
    op.alter_column(
        "support_tickets",
        "reminder_count",
        server_default=None,
        existing_type=sa.Integer(),
    )
    op.alter_column(
        "support_tickets",
        "escalation_level",
        server_default=None,
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    op.alter_column(
        "support_tickets",
        "escalation_level",
        server_default="0",
        existing_type=sa.Integer(),
    )
    op.alter_column(
        "support_tickets",
        "reminder_count",
        server_default="0",
        existing_type=sa.Integer(),
    )

    op.drop_index(
        "ix_support_ticket_audit_ticket_id", table_name="support_ticket_audit"
    )
    op.drop_table("support_ticket_audit")

    op.drop_column("support_tickets", "escalation_level")
    op.drop_column("support_tickets", "reminder_count")
    op.drop_column("support_tickets", "last_reminder_at")
    op.drop_column("support_tickets", "due_at")

    bind = op.get_bind()
    support_ticket_event_type.drop(bind, checkfirst=True)
