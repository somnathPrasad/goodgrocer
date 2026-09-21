"""Add Google customer identity while retaining legacy phone accounts.

Revision ID: 6f2a1a3e8d24
Revises: 84ebe9c8a5f3
"""

import sqlalchemy as sa
from alembic import op

revision = "6f2a1a3e8d24"
down_revision = "84ebe9c8a5f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("customers", "phone_number", existing_type=sa.String(length=20), nullable=True)
    op.add_column("customers", sa.Column("google_subject", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_customers_google_subject", "customers", ["google_subject"])


def downgrade() -> None:
    op.drop_constraint("uq_customers_google_subject", "customers", type_="unique")
    op.drop_column("customers", "google_subject")
    op.alter_column("customers", "phone_number", existing_type=sa.String(length=20), nullable=False)
