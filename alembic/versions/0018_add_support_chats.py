"""add support chats

Revision ID: 0018_add_support_chats
Revises: 0017_add_important_dates
Create Date: 2026-06-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0018_add_support_chats"
down_revision: str | None = "0017_add_important_dates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_chats",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", name="uq_support_chats_owner_id"),
    )
    op.create_index(op.f("ix_support_chats_owner_id"), "support_chats", ["owner_id"], unique=False)

    op.create_table(
        "support_messages",
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read_by_owner", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_read_by_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["support_chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_messages_chat_id"), "support_messages", ["chat_id"], unique=False)
    op.create_index(op.f("ix_support_messages_sender_id"), "support_messages", ["sender_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_support_messages_sender_id"), table_name="support_messages")
    op.drop_index(op.f("ix_support_messages_chat_id"), table_name="support_messages")
    op.drop_table("support_messages")
    op.drop_index(op.f("ix_support_chats_owner_id"), table_name="support_chats")
    op.drop_table("support_chats")
