"""add plan snapshot and esim metadata

Revision ID: 20251117_milestone1
Revises: b5d90b87eda2
Create Date: 2025-11-17 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251117_milestone1"
down_revision = "b5d90b87eda2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("plan_snapshot", sa.JSON(), nullable=True))

    op.add_column("esim_profiles", sa.Column("qr_payload", sa.Text(), nullable=True))
    op.add_column("esim_profiles", sa.Column("instructions", sa.Text(), nullable=True))
    op.alter_column(
        "esim_profiles",
        "activation_code",
        existing_type=sa.String(length=128),
        nullable=True,
    )


def downgrade() -> None:
    # Ensure there are no NULL activation codes before making column non-nullable again
    connection = op.get_bind()
    esim_table = sa.table(
        "esim_profiles",
        sa.column("id", sa.Integer),
        sa.column("activation_code", sa.String(length=128)),
    )
    connection.execute(
        esim_table.update()
        .where(esim_table.c.activation_code.is_(None))
        .values(activation_code="")
    )

    op.alter_column(
        "esim_profiles",
        "activation_code",
        existing_type=sa.String(length=128),
        nullable=False,
    )
    op.drop_column("esim_profiles", "instructions")
    op.drop_column("esim_profiles", "qr_payload")
    op.drop_column("orders", "plan_snapshot")
