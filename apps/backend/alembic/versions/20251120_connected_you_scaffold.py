"""add provider metadata for esim provisioning

Revision ID: 20251120_connected_you
Revises: 20251117_milestone1
Create Date: 2025-11-20 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_connected_you"
down_revision = "20251117_milestone1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "esim_profiles",
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "esim_profiles",
        sa.Column("provisioned_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "esim_profiles",
        sa.Column("provider_payload", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("esim_profiles", "provider_payload")
    op.drop_column("esim_profiles", "provisioned_at")
    op.drop_column("esim_profiles", "provider_reference")
