"""add shop premium fields

Revision ID: 0015_add_shop_premium_fields
Revises: 0014_add_shop_verification_badge
Create Date: 2026-06-05 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision: str = "0015_add_shop_premium_fields"
down_revision: str | None = "0014_add_shop_verification_badge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shops",
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "shops",
        sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shops", "premium_until")
    op.drop_column("shops", "is_premium")
