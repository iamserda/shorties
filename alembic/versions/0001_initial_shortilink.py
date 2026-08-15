"""initial shortilink table

Revision ID: 0001
Revises:
Create Date: 2026-08-15

The baseline schema as it existed before this session's analytics/soft-delete
work: just id, shorti_key, shorti_url, brand.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shortilink",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shorti_key", sa.String(), nullable=False),
        sa.Column("shorti_url", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shortilink_shorti_key"), "shortilink", ["shorti_key"], unique=True
    )
    op.create_index(
        op.f("ix_shortilink_shorti_url"), "shortilink", ["shorti_url"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shortilink_shorti_url"), table_name="shortilink")
    op.drop_index(op.f("ix_shortilink_shorti_key"), table_name="shortilink")
    op.drop_table("shortilink")
