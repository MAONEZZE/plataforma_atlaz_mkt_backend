"""rename calls_scheduled→meetings_held and meetings_scheduled→sales

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-28
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "weekly_metrics", "calls_scheduled", new_column_name="meetings_held", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "meetings_scheduled", new_column_name="sales", schema="ATZ_HUB"
    )


def downgrade() -> None:
    op.alter_column(
        "weekly_metrics", "sales", new_column_name="meetings_scheduled", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "meetings_held", new_column_name="calls_scheduled", schema="ATZ_HUB"
    )
