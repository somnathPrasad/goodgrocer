"""Support Customer deletion and retained order erasure.

Revision ID: b7c91d2e4f60
Revises: 6f2a1a3e8d24
"""

import sqlalchemy as sa
from alembic import op

revision = "b7c91d2e4f60"
down_revision = "6f2a1a3e8d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders", sa.Column("customer_deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "orders",
        sa.Column("delivery_details_erase_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_orders_customer_deleted_at"),
        "orders",
        ["customer_deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orders_delivery_details_erase_at"),
        "orders",
        ["delivery_details_erase_at"],
        unique=False,
    )
    op.alter_column("orders", "customer_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("orders", "customer_phone", existing_type=sa.String(length=20), nullable=True)
    op.drop_constraint("orders_customer_id_fkey", "orders", type_="foreignkey")
    op.create_foreign_key(
        "orders_customer_id_fkey",
        "orders",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM orders WHERE customer_id IS NULL OR customer_phone IS NULL LIMIT 1"
            )
        )
        .first()
    ):
        raise RuntimeError("Cannot downgrade while retained orders contain erased Customer data")
    op.drop_constraint("orders_customer_id_fkey", "orders", type_="foreignkey")
    op.create_foreign_key("orders_customer_id_fkey", "orders", "customers", ["customer_id"], ["id"])
    op.alter_column("orders", "customer_phone", existing_type=sa.String(length=20), nullable=False)
    op.alter_column("orders", "customer_id", existing_type=sa.Integer(), nullable=False)
    op.drop_index(op.f("ix_orders_delivery_details_erase_at"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_deleted_at"), table_name="orders")
    op.drop_column("orders", "delivery_details_erase_at")
    op.drop_column("orders", "customer_deleted_at")
