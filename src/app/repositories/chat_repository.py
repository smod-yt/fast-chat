from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.app.models.chat_model import (
    SAVED_MESSAGES_TITLE,
    SYSTEM_NOTIFICATIONS_TITLE,
    Chat,
    ChatParticipant,
    ChatType,
    ChatTypeName,
)


async def get_chat_type_by_name(
    session: AsyncSession, name: ChatTypeName
) -> ChatType | None:
    result = await session.execute(select(ChatType).where(ChatType.name == name.value))
    return result.scalar_one_or_none()


async def get_chat_by_uuid(session: AsyncSession, chat_uuid: UUID) -> Chat | None:
    result = await session.execute(select(Chat).where(Chat.uuid == chat_uuid))
    return result.scalar_one_or_none()


async def get_chat_by_uuid_for_update(
    session: AsyncSession, chat_uuid: UUID
) -> Chat | None:
    result = await session.execute(
        select(Chat).where(Chat.uuid == chat_uuid).with_for_update()
    )
    return result.scalar_one_or_none()


async def get_user_chats(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[Chat], int]:
    chat_uuids = select(ChatParticipant.chat_uuid).where(
        ChatParticipant.user_id == user_id
    )

    count_statement = select(func.count(Chat.uuid)).where(Chat.uuid.in_(chat_uuids))
    total = (await session.execute(count_statement)).scalar_one()

    statement = (
        select(Chat)
        .where(Chat.uuid.in_(chat_uuids))
        .order_by(Chat.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all()), total


async def get_private_chat_between(
    session: AsyncSession, user_id: int, other_user_id: int
) -> Chat | None:
    user_chats = select(ChatParticipant.chat_uuid).where(
        ChatParticipant.user_id == user_id
    )
    other_chats = select(ChatParticipant.chat_uuid).where(
        ChatParticipant.user_id == other_user_id
    )

    statement = (
        select(Chat)
        .join(ChatType, Chat.type_id == ChatType.id)
        .where(
            ChatType.name == ChatTypeName.PRIVATE.value,
            Chat.uuid.in_(user_chats),
            Chat.uuid.in_(other_chats),
        )
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def create_chat(
    session: AsyncSession,
    type_id: int,
    owner_id: int,
    user_ids: list[int],
    title: str | None = None,
) -> Chat:
    chat = Chat(type_id=type_id, owner_id=owner_id, title=title)
    chat_uuid = chat.uuid

    session.add(chat)
    await session.flush()

    for user_id in user_ids:
        session.add(ChatParticipant(chat_uuid=chat_uuid, user_id=user_id))

    await session.commit()
    result_chat = await get_chat_by_uuid(session, chat_uuid)
    assert result_chat is not None
    return result_chat


async def create_default_chats(session: AsyncSession, user_id: int) -> None:
    system_type = await get_chat_type_by_name(session, ChatTypeName.SYSTEM)
    if system_type is None:
        raise RuntimeError("Chat types are not seeded")

    for title in (SAVED_MESSAGES_TITLE, SYSTEM_NOTIFICATIONS_TITLE):
        chat = Chat(type_id=system_type.id, owner_id=user_id, title=title)
        session.add(chat)
        await session.flush()
        session.add(ChatParticipant(chat_uuid=chat.uuid, user_id=user_id))


async def update_chat(session: AsyncSession, chat: Chat, is_blocked: bool) -> Chat:
    chat_uuid = chat.uuid
    chat.is_blocked = is_blocked
    session.add(chat)
    await session.commit()
    result_chat = await get_chat_by_uuid(session, chat_uuid)
    assert result_chat is not None
    return result_chat


async def delete_chat(session: AsyncSession, chat: Chat) -> None:
    await session.delete(chat)
    await session.commit()
