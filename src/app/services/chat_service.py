from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import User
from src.app.models.chat_model import Chat, ChatTypeName
from src.app.models.user_model import UserRoles
from src.app.repositories import chat_repository, user_repository
from src.app.schemas.chat_schema import ChatCreateSchema, ChatUpdateSchema
from src.app.utils.exceptions import (
    BadRequest,
    ChatNotFound,
    Conflict,
    Forbidden,
    UserNotFound,
)


async def create_chat(
    session: AsyncSession, current_user: User, data: ChatCreateSchema
) -> Chat:
    actor_id = current_user.id
    actor_name = current_user.user_name

    if data.type != ChatTypeName.PRIVATE:
        logger.warning(
            f"User {actor_id} ('{actor_name}') attempted to create a {data.type.value} chat"
        )
        raise Forbidden("System chats cannot be created manually")

    user_ids = list(data.user_ids)
    if len(set(user_ids)) != 2:
        raise BadRequest("Exactly two distinct users are required")

    if actor_id not in user_ids:
        raise BadRequest("You must be a participant of the chat")

    for user_id in user_ids:
        if await user_repository.get_user_by_id(session, user_id) is None:
            logger.warning(
                f"User {actor_id} attempted to create a chat with missing user {user_id}"
            )
            raise UserNotFound(f"User {user_id} not found")

    other_user_id = next(uid for uid in user_ids if uid != actor_id)

    existing = await chat_repository.get_private_chat_between(
        session, actor_id, other_user_id
    )
    if existing is not None:
        logger.warning(
            f"User {actor_id} attempted to create a duplicate chat with user {other_user_id} (chat {existing.uuid})"
        )
        raise Conflict("Chat with this user already exists")

    chat_type = await chat_repository.get_chat_type_by_name(
        session, ChatTypeName.PRIVATE
    )
    if chat_type is None:
        raise RuntimeError("Chat types are not seeded")

    chat = await chat_repository.create_chat(
        session,
        type_id=chat_type.id,
        owner_id=actor_id,
        user_ids=user_ids,
    )
    logger.info(
        f"User {actor_id} ('{actor_name}') created chat {chat.uuid} "
        f"with user {other_user_id}"
    )
    return chat


async def get_my_chats(
    session: AsyncSession,
    current_user: User,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[Chat], int]:
    return await chat_repository.get_user_chats(
        session, current_user.id, page=page, limit=limit
    )


async def get_user_chats(
    session: AsyncSession,
    current_user: User,
    user_id: int,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[Chat], int]:
    if await user_repository.get_user_by_id(session, user_id) is None:
        raise UserNotFound

    if (
        current_user.id != user_id
        and current_user.role.weight < UserRoles.MODERATOR.weight
    ):
        logger.warning(
            f"Access denied: user {current_user.id} ('{current_user.user_name}') "
            f"attempted to view chats of user {user_id}"
        )
        raise Forbidden("You don't have permissions to view these chats")

    return await chat_repository.get_user_chats(
        session, user_id, page=page, limit=limit
    )


async def update_chat(
    session: AsyncSession,
    current_user: User,
    chat_uuid: UUID,
    data: ChatUpdateSchema,
) -> Chat:
    actor_id = current_user.id
    actor_name = current_user.user_name

    chat = await chat_repository.get_chat_by_uuid_for_update(session, chat_uuid)
    if chat is None:
        raise ChatNotFound

    if chat.type == ChatTypeName.SYSTEM.value:
        logger.warning(
            f"User {actor_id} ('{actor_name}') attempted to modify system chat {chat_uuid}"
        )
        raise Forbidden("System chats cannot be modified")

    is_owner = chat.owner_id is not None and chat.owner_id == actor_id
    if not is_owner and current_user.role.weight < UserRoles.MODERATOR.weight:
        logger.warning(
            f"Access denied: user {actor_id} ('{actor_name}') "
            f"attempted to modify chat {chat_uuid}"
        )
        raise Forbidden("You don't have permissions to modify this chat")

    updated = await chat_repository.update_chat(
        session, chat, is_blocked=data.is_blocked
    )
    logger.info(
        f"User {actor_id} ('{actor_name}') set is_blocked={data.is_blocked} "
        f"for chat {chat_uuid}"
    )
    return updated


async def delete_chat(
    session: AsyncSession,
    current_user: User,
    chat_uuid: UUID,
) -> None:
    actor_id = current_user.id
    actor_name = current_user.user_name

    chat = await chat_repository.get_chat_by_uuid_for_update(session, chat_uuid)
    if chat is None:
        raise ChatNotFound

    if chat.type == ChatTypeName.SYSTEM.value:
        logger.warning(
            f"User {actor_id} ('{actor_name}') attempted to delete system chat {chat_uuid}"
        )
        raise Forbidden("System chats cannot be deleted")

    is_owner = chat.owner_id is not None and chat.owner_id == actor_id
    if not is_owner and current_user.role.weight < UserRoles.ADMIN.weight:
        logger.warning(
            f"Access denied: user {actor_id} ('{actor_name}') "
            f"attempted to delete chat {chat_uuid}"
        )
        raise Forbidden("You don't have permissions to delete this chat")

    await chat_repository.delete_chat(session, chat)
    logger.info(
        f"Chat {chat_uuid} deleted by user {actor_id} ('{actor_name}')"
    )
