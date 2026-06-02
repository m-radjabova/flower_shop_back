"""add bouquet sizes addons and order item selections

Revision ID: 0013_bouquet_sizes_addons
Revises: 0012_add_shop_social_links
Create Date: 2026-05-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_bouquet_sizes_addons"
down_revision: str | None = "0012_add_shop_social_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bouquets", sa.Column("size_options", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("bouquets", sa.Column("addon_options", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("order_items", sa.Column("selected_size", sa.JSON(), nullable=True))
    op.add_column("order_items", sa.Column("selected_addons", sa.JSON(), nullable=False, server_default="[]"))

    op.execute(
        """
        UPDATE bouquets
        SET size_options = json_build_array(
            json_build_object(
                'key', 'medium',
                'label', COALESCE(NULLIF(size, ''), 'Medium'),
                'price', price,
                'image', image
            )
        )
        WHERE image IS NOT NULL AND image <> '';
        """
    )

    op.alter_column("bouquets", "size_options", server_default=None)
    op.alter_column("bouquets", "addon_options", server_default=None)
    op.alter_column("order_items", "selected_addons", server_default=None)


def downgrade() -> None:
    op.drop_column("order_items", "selected_addons")
    op.drop_column("order_items", "selected_size")
    op.drop_column("bouquets", "addon_options")
    op.drop_column("bouquets", "size_options")
