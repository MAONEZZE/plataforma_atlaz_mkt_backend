"""add cover_photo to products

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("cover_photo", sa.Text, nullable=True),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_column("products", "cover_photo", schema="ATZ_HUB")
