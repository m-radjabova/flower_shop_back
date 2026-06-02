"""add shop application coordinates

Revision ID: 0011_add_shop_application_coords
Revises: 0010_restore_single_user_role
Create Date: 2026-05-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_add_shop_application_coords"
down_revision: str | None = "0010_restore_single_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shop_applications", sa.Column("latitude", sa.String(length=32), nullable=True))
    op.add_column("shop_applications", sa.Column("longitude", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("shop_applications", "longitude")
    op.drop_column("shop_applications", "latitude")
