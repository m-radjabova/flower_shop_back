"""add referral fields to users

Revision ID: 0006_add_referrals
Revises: 0005_add_user_avatar_fields
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0006_add_referrals"
down_revision: str | None = "0005_add_user_avatar_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("referral_code", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("referred_by_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("users", sa.Column("referral_reward_granted", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("referral_bonus_balance", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.create_index(op.f("ix_users_referral_code"), "users", ["referral_code"], unique=True)
    op.create_index(op.f("ix_users_referred_by_id"), "users", ["referred_by_id"], unique=False)
    op.create_foreign_key("fk_users_referred_by_id_users", "users", "users", ["referred_by_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_users_referred_by_id_users", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_referred_by_id"), table_name="users")
    op.drop_index(op.f("ix_users_referral_code"), table_name="users")
    op.drop_column("users", "referral_bonus_balance")
    op.drop_column("users", "referral_reward_granted")
    op.drop_column("users", "referred_by_id")
    op.drop_column("users", "referral_code")
