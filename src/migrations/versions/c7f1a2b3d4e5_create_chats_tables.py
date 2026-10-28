"""create_chats_tables

Revision ID: c7f1a2b3d4e5
Revises: a9216cfe4580
Create Date: 2026-10-28 15:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c7f1a2b3d4e5"
down_revision: Union[str, Sequence[str], None] = "a9216cfe4580"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "chat_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "name", sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False
        ),
        sa.Column("writable", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    chat_types = sa.table(
        "chat_types",
        sa.column("name", sa.String),
        sa.column("writable", sa.Boolean),
    )
    op.bulk_insert(
        chat_types,
        [
            {"name": "private", "writable": True},
            {"name": "system", "writable": False},
        ],
    )

    op.create_table(
        "chats",
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["type_id"], ["chat_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index("ix_chats_type_id", "chats", ["type_id"])
    op.create_index("ix_chats_owner_id", "chats", ["owner_id"])

    op.create_table(
        "chat_participants",
        sa.Column("chat_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "joined_at", postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(["chat_uuid"], ["chats.uuid"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chat_uuid", "user_id"),
    )
    op.create_index(
        "ix_chat_participants_user_id", "chat_participants", ["user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_chat_participants_user_id", table_name="chat_participants"
    )
    op.drop_table("chat_participants")
    op.drop_index("ix_chats_owner_id", table_name="chats")
    op.drop_index("ix_chats_type_id", table_name="chats")
    op.drop_table("chats")
    op.drop_table("chat_types")
