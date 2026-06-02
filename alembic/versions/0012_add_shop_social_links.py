"""add shop social links

Revision ID: 0012_add_shop_social_links
Revises: 0011_add_shop_application_coords
Create Date: 2026-05-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_add_shop_social_links"
down_revision: str | None = "0011_add_shop_application_coords"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shops", sa.Column("instagram", sa.String(length=255), nullable=True))
    op.add_column("shops", sa.Column("telegram", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("shops", "telegram")
    op.drop_column("shops", "instagram")
