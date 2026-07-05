"""replace weekly_metrics with user-defined metrics + daily entries

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-03
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("weekly_metrics", schema="ATZ_HUB")

    op.create_table(
        "metrics",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("unit", sa.String, nullable=False, server_default=sa.text("'qtd'")),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        schema="ATZ_HUB",
    )
    op.create_index("metrics_user_idx", "metrics", ["user_id"], schema="ATZ_HUB")

    op.create_table(
        "metric_entries",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "metric_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("ATZ_HUB.metrics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("value", sa.Integer, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        sa.UniqueConstraint("metric_id", "day", name="metric_entries_metric_day_uq"),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_table("metric_entries", schema="ATZ_HUB")
    op.drop_index("metrics_user_idx", table_name="metrics", schema="ATZ_HUB")
    op.drop_table("metrics", schema="ATZ_HUB")

    op.create_table(
        "weekly_metrics",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("meetings_held", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("calls_made", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("sales", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("referrals", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "week_start"),
        schema="ATZ_HUB",
    )
