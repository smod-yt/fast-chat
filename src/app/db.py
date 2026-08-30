from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.app.settings import settings

engine = create_async_engine(settings.POSTGRES_URL)

AsyncSessionLocal = async_sessionmaker(engine)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]