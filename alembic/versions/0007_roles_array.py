"""convert user role to roles array

Revision ID: 0007_roles_array
Revises: 0006_add_referrals
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0007_roles_array"
down_revision: str | None = "0006_add_referrals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


USER_ROLE_ARRAY_DEFAULT = "ARRAY['customer']::user_role[]"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "roles",
            postgresql.ARRAY(
                postgresql.ENUM("admin", "owner", "customer", name="user_role", create_type=False)
            ),
            nullable=False,
            server_default=sa.text(USER_ROLE_ARRAY_DEFAULT),
        ),
    )
    op.execute("UPDATE users SET roles = ARRAY[role]::user_role[]")
    op.drop_column("users", "role")


def downgrade() -> None:
    user_role_enum = postgresql.ENUM("admin", "owner", "customer", name="user_role", create_type=False)
    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default="customer"),
    )
    op.execute("UPDATE users SET role = COALESCE(roles[1], 'customer')::user_role")
    op.drop_column("users", "roles")
