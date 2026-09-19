from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.db import AsyncSessionDep
from src.app.models import User
from src.app.models.user_model import UserRoles
from src.app.utils import hash
from src.app.utils.exceptions import Forbidden, RefreshTokenNotGranted, UserNotFound

security_scheme = HTTPBearer()


async def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis


RedisSessionDep = Annotated[aioredis.Redis, Depends(get_redis)]


async def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token is None:
        raise RefreshTokenNotGranted

    return refresh_token


async def get_user_id_from_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> int:
    access_token = credentials.credentials

    return hash.get_user_id_from_jwt(access_token)


async def get_current_user(
    session: AsyncSessionDep, user_id: int = Depends(get_user_id_from_jwt)
) -> User:
    user = await session.get(User, user_id)

    if user is None:
        raise UserNotFound("Current user not found")

    return user


def require_role(require_role: UserRoles) -> User:
    def role_check(user: User = Depends(get_current_user)):
        if user.role != require_role:
            raise Forbidden("You don't have permissions for this action")
        return user

    return role_check
