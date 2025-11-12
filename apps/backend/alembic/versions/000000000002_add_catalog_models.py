"""add catalog models: countries, carriers, plans

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000000000002'
down_revision = '000000000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create countries table
    op.create_table(
        'countries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('iso2', sa.String(length=2), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iso2'),
    )
    op.create_index('idx_country_iso2_name', 'countries', ['iso2', 'name'])
    op.create_index('ix_countries_id', 'countries', ['id'])
    op.create_index('ix_countries_iso2', 'countries', ['iso2'])
    op.create_index('ix_countries_name', 'countries', ['name'])

    # Create carriers table
    op.create_table(
        'carriers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_carriers_id', 'carriers', ['id'])
    op.create_index('ix_carriers_name', 'carriers', ['name'])

    # Create plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_id', sa.Integer(), nullable=False),
        sa.Column('carrier_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('data_gb', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_unlimited', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['carrier_id'], ['carriers.id'], ),
        sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_plan_country_carrier', 'plans', ['country_id', 'carrier_id'])
    op.create_index('idx_plan_price', 'plans', ['price_usd'])
    op.create_index('ix_plans_carrier_id', 'plans', ['carrier_id'])
    op.create_index('ix_plans_country_id', 'plans', ['country_id'])
    op.create_index('ix_plans_id', 'plans', ['id'])


def downgrade() -> None:
    op.drop_index('ix_plans_id', table_name='plans')
    op.drop_index('ix_plans_country_id', table_name='plans')
    op.drop_index('ix_plans_carrier_id', table_name='plans')
    op.drop_index('idx_plan_price', table_name='plans')
    op.drop_index('idx_plan_country_carrier', table_name='plans')
    op.drop_table('plans')
    op.drop_index('ix_carriers_name', table_name='carriers')
    op.drop_index('ix_carriers_id', table_name='carriers')
    op.drop_table('carriers')
    op.drop_index('ix_countries_name', table_name='countries')
    op.drop_index('ix_countries_iso2', table_name='countries')
    op.drop_index('ix_countries_id', table_name='countries')
    op.drop_index('idx_country_iso2_name', table_name='countries')
    op.drop_table('countries')
