"""add shop verification badge

Revision ID: 0014_add_shop_verification_badge
Revises: 0013_bouquet_sizes_addons
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision: str = "0014_add_shop_verification_badge"
down_revision: str | None = "0013_bouquet_sizes_addons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shops",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("shops", "is_verified")
