"""add multiple images to bouquets

Revision ID: 0002_add_bouquet_images
Revises: 0001_initial_users
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_add_bouquet_images"
down_revision: str | None = "0001_initial_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bouquets",
        sa.Column(
            "images",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.execute("UPDATE bouquets SET images = jsonb_build_array(image) WHERE image IS NOT NULL")
    op.alter_column("bouquets", "images", server_default=None)


def downgrade() -> None:
    op.drop_column("bouquets", "images")
