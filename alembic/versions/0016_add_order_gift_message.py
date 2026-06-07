"""add order gift message

Revision ID: 0016_add_order_gift_message
Revises: 0015_add_shop_premium_fields
Create Date: 2026-06-05 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision: str = "0016_add_order_gift_message"
down_revision: str | None = "0015_add_shop_premium_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("gift_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "gift_message")
