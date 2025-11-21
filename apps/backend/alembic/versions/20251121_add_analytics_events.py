"""add analytics events table

Revision ID: 20251121_add_analytics_events
Revises: 20251120_fix_inventory_enum_case
Create Date: 2025-11-21 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251121_add_analytics_events"
down_revision = "20251120_fix_inventory_enum_case"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "user_signup",
                "checkout_started",
                "payment_succeeded",
                "esim_activated",
                name="analyticseventtype",
            ),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=True),
        sa.Column("amount_minor_units", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "occurred_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_analytics_events_event_type", "analytics_events", ["event_type"]
    )
    op.create_index(
        "ix_analytics_events_occurred_at", "analytics_events", ["occurred_at"]
    )
    op.create_index("ix_analytics_events_user_id", "analytics_events", ["user_id"])
    op.create_index("ix_analytics_events_order_id", "analytics_events", ["order_id"])
    op.create_index("ix_analytics_events_plan_id", "analytics_events", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_analytics_events_plan_id", table_name="analytics_events")
    op.drop_index("ix_analytics_events_order_id", table_name="analytics_events")
    op.drop_index("ix_analytics_events_user_id", table_name="analytics_events")
    op.drop_index("ix_analytics_events_occurred_at", table_name="analytics_events")
    op.drop_index("ix_analytics_events_event_type", table_name="analytics_events")
    op.drop_table("analytics_events")
    op.execute("DROP TYPE IF EXISTS analyticseventtype")
