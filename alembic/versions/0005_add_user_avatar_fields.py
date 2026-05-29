"""add avatar fields to users

Revision ID: 0005_add_user_avatar_fields
Revises: 0004_add_address_coords
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_add_user_avatar_fields"
down_revision: str | None = "0004_add_address_coords"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("avatar_file_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_file_id")
    op.drop_column("users", "avatar_url")
