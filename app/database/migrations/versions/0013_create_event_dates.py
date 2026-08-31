"""create event_dates

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_dates",
        sa.Column(
            "id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "client_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        schema="ATZ_HUB",
    )
    op.create_index(
        "event_dates_client_idx", "event_dates", ["client_id"], schema="ATZ_HUB"
    )


def downgrade() -> None:
    op.drop_index("event_dates_client_idx", table_name="event_dates", schema="ATZ_HUB")
    op.drop_table("event_dates", schema="ATZ_HUB")
