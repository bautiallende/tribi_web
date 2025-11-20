"""add esim inventory table and extend statuses

Revision ID: 20251120_add_esim_inventory
Revises: 20251120_connected_you
Create Date: 2025-11-20 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_add_esim_inventory"
down_revision = "20251120_connected_you"
branch_labels = None
depends_on = None


OLD_ESIM_STATUS = mysql.ENUM(
    "draft", "pending_activation", "active", "failed", "expired", name="esimstatus"
)
NEW_ESIM_STATUS = mysql.ENUM(
    "draft",
    "pending_activation",
    "reserved",
    "assigned",
    "active",
    "failed",
    "expired",
    name="esimstatus",
)

ESIM_INVENTORY_STATUS = mysql.ENUM(
    "available", "reserved", "assigned", "retired", name="esiminventorystatus"
)


def upgrade() -> None:
    op.create_table(
        "esim_inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=True),
        sa.Column(
            "carrier_id", sa.Integer(), sa.ForeignKey("carriers.id"), nullable=True
        ),
        sa.Column(
            "country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=True
        ),
        sa.Column("activation_code", sa.String(length=128), nullable=True),
        sa.Column("iccid", sa.String(length=64), nullable=True),
        sa.Column("qr_payload", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column(
            "status",
            ESIM_INVENTORY_STATUS,
            nullable=False,
            server_default="available",
        ),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("provider_payload", sa.JSON(), nullable=True),
        sa.Column("reserved_at", sa.DateTime(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_esim_inventory_plan_id", "esim_inventory", ["plan_id"])
    op.create_index("ix_esim_inventory_country_id", "esim_inventory", ["country_id"])
    op.create_index("ix_esim_inventory_carrier_id", "esim_inventory", ["carrier_id"])

    with op.batch_alter_table("esim_profiles") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=OLD_ESIM_STATUS,
            type_=NEW_ESIM_STATUS,
            existing_nullable=False,
        )
        batch_op.add_column(sa.Column("inventory_item_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_esim_profiles_inventory_item_id", ["inventory_item_id"]
        )
        batch_op.create_foreign_key(
            "fk_esim_profiles_inventory_item_id",
            "esim_inventory",
            ["inventory_item_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("esim_profiles") as batch_op:
        batch_op.drop_constraint(
            "fk_esim_profiles_inventory_item_id", type_="foreignkey"
        )
        batch_op.drop_index("ix_esim_profiles_inventory_item_id")
        batch_op.drop_column("inventory_item_id")
        batch_op.alter_column(
            "status",
            existing_type=NEW_ESIM_STATUS,
            type_=OLD_ESIM_STATUS,
            existing_nullable=False,
        )

    op.drop_index("ix_esim_inventory_carrier_id", table_name="esim_inventory")
    op.drop_index("ix_esim_inventory_country_id", table_name="esim_inventory")
    op.drop_index("ix_esim_inventory_plan_id", table_name="esim_inventory")
    op.drop_table("esim_inventory")
