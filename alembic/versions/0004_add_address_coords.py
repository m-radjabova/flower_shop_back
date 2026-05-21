"""add address coordinates

Revision ID: 0004_add_address_coords
Revises: 0003_add_addresses
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_address_coords"
down_revision = "0003_add_addresses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("addresses", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("addresses", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))


def downgrade() -> None:
    op.drop_column("addresses", "longitude")
    op.drop_column("addresses", "latitude")
