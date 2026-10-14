from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import User
from src.app.models.user_ban_model import UserBan
from src.app.models.user_model import UserRoles
from src.app.repositories import ban_repository, token_repository, user_repository
from src.app.schemas.ban_schema import BanUserSchema, UserBanResponse
from src.app.utils.exceptions import Forbidden, UserAlreadyBanned, UserNotFound


async def ban_user(
    session: AsyncSession,
    redis: Redis,
    admin: User,
    data: BanUserSchema,
) -> UserBan:
    target_user = await user_repository.get_user_by_id(session, data.user_id)
    if target_user is None:
        raise UserNotFound("User not found")

    if target_user.role == UserRoles.ADMIN:
        raise Forbidden("Admins cannot be banned")

    active_ban = await ban_repository.get_active_ban(session, data.user_id)
    if active_ban is not None:
        raise UserAlreadyBanned(
            message="User is already banned",
            details=UserBanResponse.model_validate(active_ban).model_dump(mode="json"),
        )

    ban = await ban_repository.create_ban(
        session=session,
        admin_id=admin.id,
        user_id=data.user_id,
        reason=data.reason,
        expires_at=data.expires_at,
    )

    await token_repository.delete_all_user_sessions(redis, data.user_id)

    return ban


async def get_ban_history(
    session: AsyncSession,
    user_id: int,
) -> list[UserBan]:
    target_user = await user_repository.get_user_by_id(session, user_id)
    if target_user is None:
        raise UserNotFound("User not found")

    return await ban_repository.get_user_bans(session, user_id)


async def unban_user(
    session: AsyncSession,
    user_id: int,
) -> None:
    target_user = await user_repository.get_user_by_id(session, user_id)
    if target_user is None:
        raise UserNotFound("User not found")

    await ban_repository.revoke_active_ban(session, user_id)
