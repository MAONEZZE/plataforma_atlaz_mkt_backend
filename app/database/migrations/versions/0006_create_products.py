"""create products table and add product_id to users

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
        schema="ATZ_HUB",
    )
    op.add_column(
        "users",
        sa.Column(
            "product_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("ATZ_HUB.products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="ATZ_HUB",
    )


def downgrade() -> None:
    op.drop_column("users", "product_id", schema="ATZ_HUB")
    op.drop_table("products", schema="ATZ_HUB")
