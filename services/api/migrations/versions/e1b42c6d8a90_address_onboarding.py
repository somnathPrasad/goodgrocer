"""Remember the one-time customer address offer.

Revision ID: e1b42c6d8a90
Revises: d8a21e9c4b70
"""

import sqlalchemy as sa
from alembic import op

revision = "e1b42c6d8a90"
down_revision = "d8a21e9c4b70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "address_onboarding_seen", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.alter_column("customers", "address_onboarding_seen", server_default=None)


def downgrade() -> None:
    op.drop_column("customers", "address_onboarding_seen")
