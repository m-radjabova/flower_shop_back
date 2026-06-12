"""add category description

Revision ID: 0020_add_category_description
Revises: 0019_support_attachments
Create Date: 2026-06-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0020_add_category_description"
down_revision: Union[str, None] = "0019_support_attachments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "description")
