"""create stages and user_stages tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stages",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        schema="ATZ_HUB",
    )
    op.create_table(
        "user_stages",
        sa.Column("user_id", PGUUID(as_uuid=True), sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("stage_id", PGUUID(as_uuid=True), sa.ForeignKey("ATZ_HUB.stages.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("done", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_table("user_stages", schema="ATZ_HUB")
    op.drop_table("stages", schema="ATZ_HUB")
