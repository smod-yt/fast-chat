from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.app.settings import settings

engine = create_async_engine(settings.POSTGRES_URL)

AsyncSessionLocal = async_sessionmaker(engine)

async def get_session():
    async with AsyncSession() as session:
        yield session

AsyncSessionDep = Depends(get_session)