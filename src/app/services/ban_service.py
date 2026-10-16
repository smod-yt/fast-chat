from loguru import logger
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
        logger.warning(
            f"Admin {admin.id} ('{admin.user_name}') failed to ban user {data.user_id}: user not found"
        )
        raise UserNotFound("User not found")

    if target_user.role == UserRoles.ADMIN:
        logger.warning(
            f"Admin {admin.id} ('{admin.user_name}') attempted to ban admin {target_user.id} ('{target_user.user_name}')"
        )
        raise Forbidden("Admins cannot be banned")

    active_ban = await ban_repository.get_active_ban(session, data.user_id)
    if active_ban is not None:
        logger.warning(
            f"Admin {admin.id} ('{admin.user_name}') attempted to ban user {target_user.id} ('{target_user.user_name}'), but user is already banned (ban_id={active_ban.id})"
        )
        raise UserAlreadyBanned(
            message="User is already banned",
            details=UserBanResponse.model_validate(active_ban).model_dump(mode="json"),
        )

    target_user_id = target_user.id
    target_user_name = target_user.user_name
    admin_id = admin.id
    admin_user_name = admin.user_name

    ban = await ban_repository.create_ban(
        session=session,
        admin_id=admin_id,
        user_id=data.user_id,
        reason=data.reason,
        expires_at=data.expires_at,
    )

    await token_repository.delete_all_user_sessions(redis, data.user_id)
    logger.info(
        f"User {target_user_id} ('{target_user_name}') was banned by admin {admin_id} ('{admin_user_name}'). "
        f"Ban ID: {ban.id}, reason: '{ban.reason}', expires_at: {ban.expires_at}"
    )

    return ban


async def get_ban_history(
    session: AsyncSession,
    user_id: int,
) -> list[UserBan]:
    target_user = await user_repository.get_user_by_id(session, user_id)
    if target_user is None:
        logger.warning(f"Failed to get ban history: user {user_id} not found")
        raise UserNotFound("User not found")

    bans = await ban_repository.get_user_bans(session, user_id)
    logger.debug(f"Retrieved {len(bans)} ban record(s) for user {user_id}")
    return bans


async def unban_user(
    session: AsyncSession,
    user_id: int,
    admin: User | None = None,
) -> None:
    target_user = await user_repository.get_user_by_id(session, user_id)
    if target_user is None:
        admin_info = f" by admin {admin.id} ('{admin.user_name}')" if admin else ""
        logger.warning(f"Failed to unban user {user_id}{admin_info}: user not found")
        raise UserNotFound("User not found")

    target_user_name = target_user.user_name
    admin_info = (
        f" by admin {admin.id} ('{admin.user_name}')" if admin is not None else ""
    )

    revoked_ban = await ban_repository.revoke_active_ban(session, user_id)
    if revoked_ban:
        logger.info(
            f"Active ban (ban_id={revoked_ban.id}) revoked for user {user_id} ('{target_user_name}'){admin_info}"
        )
    else:
        logger.info(
            f"No active ban to revoke for user {user_id} ('{target_user_name}'){admin_info}"
        )
