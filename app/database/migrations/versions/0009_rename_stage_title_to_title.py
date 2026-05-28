"""rename stage_title to title in stages

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-28
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("stages", "stage_title", new_column_name="title", schema="ATZ_HUB")


def downgrade() -> None:
    op.alter_column("stages", "title", new_column_name="stage_title", schema="ATZ_HUB")
