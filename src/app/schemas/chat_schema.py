from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.models.chat_model import ChatTypeName


class ChatParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    user_name: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    type: str
    title: str | None
    owner_id: int | None
    is_blocked: bool
    writable: bool
    created_at: datetime
    participants: list[ChatParticipantResponse]


class PaginatedChatsResponse(BaseModel):
    items: list[ChatResponse]
    total: int
    page: int
    limit: int


class ChatCreateSchema(BaseModel):
    user_ids: list[int] = Field(min_length=2, max_length=2)
    type: ChatTypeName = ChatTypeName.PRIVATE


class ChatUpdateSchema(BaseModel):
    is_blocked: bool
