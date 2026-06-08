"""add support message attachments

Revision ID: 0019_support_attachments
Revises: 0018_add_support_chats
Create Date: 2026-06-08 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision: str = "0019_support_attachments"
down_revision: str | None = "0018_add_support_chats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("support_messages", sa.Column("attachment_url", sa.String(length=700), nullable=True))
    op.add_column("support_messages", sa.Column("attachment_file_id", sa.String(length=255), nullable=True))
    op.add_column("support_messages", sa.Column("attachment_name", sa.String(length=255), nullable=True))
    op.add_column("support_messages", sa.Column("attachment_content_type", sa.String(length=120), nullable=True))
    op.add_column("support_messages", sa.Column("attachment_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("support_messages", "attachment_size")
    op.drop_column("support_messages", "attachment_content_type")
    op.drop_column("support_messages", "attachment_name")
    op.drop_column("support_messages", "attachment_file_id")
    op.drop_column("support_messages", "attachment_url")
