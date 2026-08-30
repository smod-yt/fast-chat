from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.app.utils.exceptions import Conflict
from src.app.models import User
from loguru import logger

async def register(session: AsyncSession, name: str, user_name: str, hashed_password: str):
    new_user = User(
        name=name,
        user_name=user_name,
        password=hashed_password
    )

    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"User with user_name \"{new_user.user_name}\" (id: {new_user.id}) succesfully registered")
        return new_user
    except IntegrityError:
        await session.rollback()
        logger.warning(f"Failed registration attempt, user_name \"{user_name}\" is already taken")
        raise Conflict(message="This user name is already taken")