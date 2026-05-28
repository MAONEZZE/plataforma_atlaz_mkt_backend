"""add description to products and is_doc to lessons

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("description", sa.Text, nullable=True),
        schema="ATZ_HUB",
    )
    op.add_column(
        "lessons",
        sa.Column("is_doc", sa.Boolean, nullable=False, server_default=sa.false()),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_column("lessons", "is_doc", schema="ATZ_HUB")
    op.drop_column("products", "description", schema="ATZ_HUB")
