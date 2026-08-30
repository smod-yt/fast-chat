from sqlalchemy.ext.asyncio import AsyncSession
from src.app.repositories import auth_repository
from src.app.schemas.auth_schema import RegisterSchema
from src.app.utils import hash

async def register(session: AsyncSession, data: RegisterSchema):
    name      = data.name.strip()
    user_name = data.user_name.strip()

    password        = data.password
    hashed_password = await hash.hash_password(password)

    new_user = await auth_repository.register(session, name, user_name, hashed_password)

    return new_user