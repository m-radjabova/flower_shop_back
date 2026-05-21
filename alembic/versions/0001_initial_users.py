"""initial flower shop marketplace schema

Revision ID: 0001_initial_users
Revises:
Create Date: 2026-05-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_users"
down_revision: str | None = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = postgresql.ENUM("admin", "owner", "customer", name="user_role", create_type=False)
shop_status_enum = postgresql.ENUM("pending", "active", "blocked", name="shop_status", create_type=False)
bouquet_status_enum = postgresql.ENUM("active", "inactive", "sold_out", name="bouquet_status", create_type=False)
order_status_enum = postgresql.ENUM(
    "new",
    "accepted",
    "preparing",
    "delivering",
    "delivered",
    "cancelled",
    name="order_status",
    create_type=False,
)
payment_status_enum = postgresql.ENUM("pending", "paid", "failed", name="payment_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    shop_status_enum.create(bind, checkfirst=True)
    bouquet_status_enum.create(bind, checkfirst=True)
    order_status_enum.create(bind, checkfirst=True)
    payment_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False, server_default="customer"),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)

    op.create_table(
        "shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo", sa.String(length=500), nullable=True),
        sa.Column("banner", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("latitude", sa.String(length=32), nullable=True),
        sa.Column("longitude", sa.String(length=32), nullable=True),
        sa.Column("working_hours", sa.String(length=255), nullable=True),
        sa.Column("rating", sa.Numeric(2, 1), nullable=False, server_default="0"),
        sa.Column("reviews_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", shop_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.CheckConstraint("rating >= 0 AND rating <= 5", name="check_shops_rating_range"),
        sa.CheckConstraint("reviews_count >= 0", name="check_shops_reviews_count_nonnegative"),
    )
    op.create_index(op.f("ix_shops_city"), "shops", ["city"], unique=False)
    op.create_index(op.f("ix_shops_owner_id"), "shops", ["owner_id"], unique=False)
    op.create_index(op.f("ix_shops_slug"), "shops", ["slug"], unique=True)

    op.create_table(
        "bouquets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("compound", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("old_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("image", sa.String(length=500), nullable=False),
        sa.Column("size", sa.String(length=50), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", bouquet_status_enum, nullable=False, server_default="active"),
        sa.Column("rating", sa.Numeric(2, 1), nullable=False, server_default="0"),
        sa.Column("reviews_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "slug", name="uq_bouquets_shop_slug"),
        sa.CheckConstraint("price >= 0", name="check_bouquets_price_nonnegative"),
        sa.CheckConstraint("old_price IS NULL OR old_price >= 0", name="check_bouquets_old_price_nonnegative"),
        sa.CheckConstraint("stock >= 0", name="check_bouquets_stock_nonnegative"),
        sa.CheckConstraint("rating >= 0 AND rating <= 5", name="check_bouquets_rating_range"),
        sa.CheckConstraint("reviews_count >= 0", name="check_bouquets_reviews_count_nonnegative"),
    )
    op.create_index(op.f("ix_bouquets_category_id"), "bouquets", ["category_id"], unique=False)
    op.create_index(op.f("ix_bouquets_shop_id"), "bouquets", ["shop_id"], unique=False)
    op.create_index(op.f("ix_bouquets_slug"), "bouquets", ["slug"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("delivery_method", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("payment_status", payment_status_enum, nullable=False, server_default="pending"),
        sa.Column("status", order_status_enum, nullable=False, server_default="new"),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("total_price >= 0", name="check_orders_total_price_nonnegative"),
    )
    op.create_index(op.f("ix_orders_shop_id"), "orders", ["shop_id"], unique=False)
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bouquet_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bouquet_name", sa.String(length=150), nullable=False),
        sa.Column("bouquet_image", sa.String(length=500), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["bouquet_id"], ["bouquets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("price >= 0", name="check_order_items_price_nonnegative"),
        sa.CheckConstraint("quantity > 0", name="check_order_items_quantity_positive"),
        sa.CheckConstraint("total_price >= 0", name="check_order_items_total_price_nonnegative"),
    )
    op.create_index(op.f("ix_order_items_bouquet_id"), "order_items", ["bouquet_id"], unique=False)
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bouquet_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["bouquet_id"], ["bouquets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="check_reviews_rating_range"),
    )
    op.create_index(op.f("ix_reviews_bouquet_id"), "reviews", ["bouquet_id"], unique=False)
    op.create_index(op.f("ix_reviews_order_id"), "reviews", ["order_id"], unique=False)
    op.create_index(op.f("ix_reviews_shop_id"), "reviews", ["shop_id"], unique=False)
    op.create_index(op.f("ix_reviews_user_id"), "reviews", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_user_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_shop_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_order_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_bouquet_id"), table_name="reviews")
    op.drop_table("reviews")

    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_bouquet_id"), table_name="order_items")
    op.drop_table("order_items")

    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_shop_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_bouquets_slug"), table_name="bouquets")
    op.drop_index(op.f("ix_bouquets_shop_id"), table_name="bouquets")
    op.drop_index(op.f("ix_bouquets_category_id"), table_name="bouquets")
    op.drop_table("bouquets")

    op.drop_index(op.f("ix_shops_slug"), table_name="shops")
    op.drop_index(op.f("ix_shops_owner_id"), table_name="shops")
    op.drop_index(op.f("ix_shops_city"), table_name="shops")
    op.drop_table("shops")

    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_table("categories")

    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    payment_status_enum.drop(op.get_bind(), checkfirst=True)
    order_status_enum.drop(op.get_bind(), checkfirst=True)
    bouquet_status_enum.drop(op.get_bind(), checkfirst=True)
    shop_status_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
