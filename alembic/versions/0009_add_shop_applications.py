"""add shop applications table

Revision ID: 0009_add_shop_applications
Revises: 0008_add_courier_role
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0009_add_shop_applications"
down_revision: str | None = "0008_add_courier_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    shop_application_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="shop_application_status",
    )
    shop_application_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "shop_applications",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instagram", sa.String(length=255), nullable=True),
        sa.Column("telegram", sa.String(length=255), nullable=True),
        sa.Column("logo", sa.String(length=500), nullable=True),
        sa.Column("banner", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "approved", "rejected", name="shop_application_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("admin_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shop_applications_city"), "shop_applications", ["city"], unique=False)
    op.create_index(op.f("ix_shop_applications_user_id"), "shop_applications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_shop_applications_user_id"), table_name="shop_applications")
    op.drop_index(op.f("ix_shop_applications_city"), table_name="shop_applications")
    op.drop_table("shop_applications")
    postgresql.ENUM(name="shop_application_status").drop(op.get_bind(), checkfirst=True)
