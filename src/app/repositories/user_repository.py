from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.app.models import User
from src.app.models.user_model import UserRoles
from src.app.settings import settings
from src.app.utils.hash import hash_password


async def create_first_admin_if_not_exists(session: AsyncSession):
    query = await session.execute(select(User).where(User.role == UserRoles.ADMIN))
    admin = query.scalar_one_or_none()

    if admin is not None:
        logger.debug("The admin already exists")
        return

    logger.info("No admins found, creating the first admin...")

    admin_name = settings.FIRST_ADMIN_DEFAULT_NAME
    admin_user_name = settings.FIRST_ADMIN_DEFAULT_USER_NAME
    admin_hashed_password = await hash_password(settings.FIRST_ADMIN_DEFAULT_PASSWORD)

    try:
        first_admin = User(
            name=admin_name,
            user_name=admin_user_name,
            role=UserRoles.ADMIN,
            password=admin_hashed_password,
        )

        session.add(first_admin)
        await session.commit()
        logger.info(f"The first admin ({admin_user_name}) successfully created")
    except IntegrityError:
        await session.rollback()
        logger.warning(
            "Failed to create first admin, user with the same user_name already exists"
        )
    except Exception as e:
        await session.rollback()
        logger.exception(
            f"An unexpected error occurred while creating the first admin: {e}"
        )
