"""add auth orders payments esim tables

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2025-11-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000000000003'
down_revision = '000000000002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime, nullable=True),
    )

    # Create auth_codes table
    op.create_table(
        'auth_codes',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('used', sa.Boolean, server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Index('ix_auth_codes_user_code', 'user_id', 'code'),
    )

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_id', sa.Integer, sa.ForeignKey('plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='created'),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('amount_minor_units', sa.Integer, nullable=False),
        sa.Column('provider_ref', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Index('ix_orders_user_id', 'user_id'),
    )

    # Create esim_profiles table
    op.create_table(
        'esim_profiles',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('country_id', sa.Integer, sa.ForeignKey('countries.id', ondelete='SET NULL'), nullable=True),
        sa.Column('carrier_id', sa.Integer, sa.ForeignKey('carriers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('plan_id', sa.Integer, sa.ForeignKey('plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('activation_code', sa.String(255), nullable=True),
        sa.Column('iccid', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Index('ix_esim_profiles_user_id', 'user_id'),
        sa.Index('ix_esim_profiles_order_id', 'order_id'),
    )

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('raw_payload', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Index('ix_payments_order_id', 'order_id'),
    )


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('esim_profiles')
    op.drop_table('orders')
    op.drop_table('auth_codes')
    op.drop_table('users')
