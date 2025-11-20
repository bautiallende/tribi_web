"""ensure esim inventory enum uses lowercase values

Revision ID: 20251120_fix_inventory_enum_case
Revises: 20251120_add_esim_inventory
Create Date: 2025-11-20 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_fix_inventory_enum_case"
down_revision = "20251120_add_esim_inventory"
branch_labels = None
depends_on = None


LOWERCASE_ENUM = "available','reserved','assigned','retired"
UPPERCASE_ENUM = "AVAILABLE','RESERVED','ASSIGNED','RETIRED"


def upgrade() -> None:
    conn = op.get_bind()
    # Normalize existing values to lowercase before altering column type
    conn.execute(sa.text("UPDATE esim_inventory SET status = LOWER(status)"))
    conn.execute(
        sa.text(
            """
        ALTER TABLE esim_inventory
        MODIFY COLUMN status ENUM('available','reserved','assigned','retired')
        NOT NULL DEFAULT 'available'
        """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE esim_inventory SET status = UPPER(status)"))
    conn.execute(
        sa.text(
            """
        ALTER TABLE esim_inventory
        MODIFY COLUMN status ENUM('AVAILABLE','RESERVED','ASSIGNED','RETIRED')
        NOT NULL DEFAULT 'AVAILABLE'
        """
        )
    )
