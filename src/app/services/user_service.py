from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import User
from src.app.models.user_model import UserRoles
from src.app.repositories import token_repository, user_repository
from src.app.schemas.user_schema import (
    UserUpdatePasswordSchema,
    UserUpdateSchema,
)
from src.app.utils import hash
from src.app.utils.exceptions import Conflict, Forbidden, InvalidCredentials, UserNotFound


def check_user_access(
    current_user: User, target_user_id: int, error_msg: str | None = None
) -> bool:
    if current_user.role.weight >= UserRoles.ADMIN.weight or current_user.id == target_user_id:
        return True
    else:
        raise Forbidden(message=error_msg)


async def get_users(
    session: AsyncSession,
    page: int = 1,
    limit: int = 10,
    name: str | None = None,
    user_name: str | None = None,
) -> tuple[list[User], int]:
    return await user_repository.get_users(
        session, page=page, limit=limit, name=name, user_name=user_name
    )


async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    user = await user_repository.get_user_by_id(session, user_id)
    if user is None:
        raise UserNotFound
    return user


async def get_user_by_user_name(session: AsyncSession, user_name: str) -> User | None:
    return await user_repository.get_user_by_user_name(session, user_name)


async def update_user(
    session: AsyncSession,
    user: User,
    data: UserUpdateSchema,
) -> User:
    name = data.name.strip() if data.name is not None else None
    user_name = data.user_name.strip() if data.user_name is not None else None

    if user_name is not None and user_name != user.user_name:
        existing = await user_repository.get_user_by_user_name(session, user_name)
        if existing is not None and existing.id != user.id:
            raise Conflict(message="This user name is already taken")

    return await user_repository.update_user(
        session, user, name=name, user_name=user_name
    )


async def update_user_password(
    session: AsyncSession,
    user: User,
    data: UserUpdatePasswordSchema,
) -> None:
    if not await hash.check_password(data.old_password, user.password):
        raise InvalidCredentials(message="Incorrect old password")

    hashed_password = await hash.hash_password(data.new_password)
    await user_repository.update_user_password(session, user, hashed_password)


async def delete_user(
    session: AsyncSession,
    redis: Redis,
    user: User,
) -> None:
    await token_repository.delete_all_user_sessions(redis, user.id)
    await user_repository.delete_user(session, user)

