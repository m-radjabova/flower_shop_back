"""add courier role to user_role enum

Revision ID: 0008_add_courier_role
Revises: 0007_roles_array
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0008_add_courier_role"
down_revision: str | None = "0007_roles_array"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'courier'")


def downgrade() -> None:
    # PostgreSQL enum values are not easily removable in-place.
    # Keeping downgrade as a no-op avoids destructive implicit casts.
    pass
