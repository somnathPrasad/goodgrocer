"""Capture signed WhatsApp webhook deliveries.

Revision ID: d8a21e9c4b70
Revises: b7c91d2e4f60
"""

import sqlalchemy as sa
from alembic import op

revision = "d8a21e9c4b70"
down_revision = "b7c91d2e4f60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_webhook_deliveries",
        sa.Column("payload_hash", sa.String(64), primary_key=True),
        sa.Column("raw_body", sa.LargeBinary(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_whatsapp_webhook_deliveries_received_at"),
        "whatsapp_webhook_deliveries",
        ["received_at"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_whatsapp_webhook_deliveries_received_at"), table_name="whatsapp_webhook_deliveries"
    )
    op.drop_table("whatsapp_webhook_deliveries")
