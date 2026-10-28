from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql
from sqlmodel import Column, Field, Relationship, SQLModel

from src.app.models.user_model import User

SAVED_MESSAGES_TITLE = "Saved messages"
SYSTEM_NOTIFICATIONS_TITLE = "System notifications"


class ChatTypeName(str, Enum):
    PRIVATE = "private"
    SYSTEM = "system"


class ChatType(SQLModel, table=True):
    __tablename__ = "chat_types"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=16, nullable=False)
    writable: bool = Field(default=True, nullable=False)


class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    type_id: int = Field(
        foreign_key="chat_types.id", nullable=False, index=True, ondelete="CASCADE"
    )
    owner_id: int | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
        ondelete="SET NULL",
    )
    title: str | None = Field(default=None, max_length=64)
    is_blocked: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    )

    chat_type: ChatType = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    participants: list["ChatParticipant"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )

    @property
    def type(self) -> str:
        return self.chat_type.name

    @property
    def writable(self) -> bool:
        return self.chat_type.writable


class ChatParticipant(SQLModel, table=True):
    __tablename__ = "chat_participants"

    chat_uuid: UUID = Field(
        foreign_key="chats.uuid",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    user_id: int = Field(
        foreign_key="users.id",
        primary_key=True,
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    joined_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    )

    chat: Chat | None = Relationship(back_populates="participants")
    user: User | None = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    @property
    def name(self) -> str:
        return self.user.name if self.user is not None else ""

    @property
    def user_name(self) -> str:
        return self.user.user_name if self.user is not None else ""
