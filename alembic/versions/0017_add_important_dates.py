"""add important dates

Revision ID: 0017_add_important_dates
Revises: 0016_add_order_gift_message
Create Date: 2026-06-05 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0017_add_important_dates"
down_revision: str | None = "0016_add_order_gift_message"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "important_dates",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False, server_default="birthday"),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_important_dates_user_id"), "important_dates", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_important_dates_user_id"), table_name="important_dates")
    op.drop_table("important_dates")
