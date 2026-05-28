"""add stage_title to stages

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stages",
        sa.Column("stage_title", sa.Text, nullable=True),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_column("stages", "stage_title", schema="ATZ_HUB")
