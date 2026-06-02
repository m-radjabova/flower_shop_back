"""restore single user role column

Revision ID: 0010_restore_single_user_role
Revises: 0009_add_shop_applications
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0010_restore_single_user_role"
down_revision: str | None = "0009_add_shop_applications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role_enum = postgresql.ENUM(
        "admin",
        "owner",
        "customer",
        "courier",
        name="user_role",
        create_type=False,
    )

    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default="customer"),
    )
    op.execute(
        """
        UPDATE users
        SET role = CASE
            WHEN 'admin' = ANY(roles) THEN 'admin'::user_role
            WHEN 'owner' = ANY(roles) THEN 'owner'::user_role
            WHEN 'courier' = ANY(roles) THEN 'courier'::user_role
            ELSE 'customer'::user_role
        END
        """
    )
    op.drop_column("users", "roles")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "roles",
            postgresql.ARRAY(
                postgresql.ENUM(
                    "admin",
                    "owner",
                    "customer",
                    "courier",
                    name="user_role",
                    create_type=False,
                )
            ),
            nullable=False,
            server_default=sa.text("ARRAY['customer']::user_role[]"),
        ),
    )
    op.execute("UPDATE users SET roles = ARRAY[role]::user_role[]")
    op.drop_column("users", "role")
