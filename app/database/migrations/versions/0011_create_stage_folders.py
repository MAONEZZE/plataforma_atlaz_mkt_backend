"""create stage_folders and add folder_id/sort_order to stages

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-03
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stage_folders",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        schema="ATZ_HUB",
    )
    op.add_column(
        "stages",
        sa.Column(
            "folder_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("ATZ_HUB.stage_folders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="ATZ_HUB",
    )
    op.add_column(
        "stages",
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_column("stages", "sort_order", schema="ATZ_HUB")
    op.drop_column("stages", "folder_id", schema="ATZ_HUB")
    op.drop_table("stage_folders", schema="ATZ_HUB")
