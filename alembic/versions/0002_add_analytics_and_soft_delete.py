"""add analytics and soft delete

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-15

Adds hit-count/click-analytics and soft-delete support: new columns on
shortilink (redirect_code, hit_count, last_accessed_at, created_at,
updated_at, deleted_at) and a new linkclickevent table.

server_default is set on every NOT NULL column added to the existing
shortilink table so this applies cleanly against a database that already
has rows — SQLite has no way to add a NOT NULL column without one, and
ADD COLUMN NOT NULL with no default fails immediately.
"""

from __future__ import annotations

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "linkclickevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shorti_link_id", sa.Integer(), nullable=False),
        sa.Column("clicked_at", sa.DateTime(), nullable=False),
        sa.Column("referrer", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("user_agent", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["shorti_link_id"], ["shortilink.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_linkclickevent_clicked_at"),
        "linkclickevent",
        ["clicked_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_linkclickevent_shorti_link_id"),
        "linkclickevent",
        ["shorti_link_id"],
        unique=False,
    )

    with op.batch_alter_table("shortilink", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "redirect_code", sa.Integer(), nullable=False, server_default="307"
            )
        )
        batch_op.add_column(
            sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("last_accessed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_shortilink_deleted_at"), ["deleted_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("shortilink", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_shortilink_deleted_at"))
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("last_accessed_at")
        batch_op.drop_column("hit_count")
        batch_op.drop_column("redirect_code")

    op.drop_index(op.f("ix_linkclickevent_shorti_link_id"), table_name="linkclickevent")
    op.drop_index(op.f("ix_linkclickevent_clicked_at"), table_name="linkclickevent")
    op.drop_table("linkclickevent")
