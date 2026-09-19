from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from src.app.db import AsyncSessionLocal
from src.app.repositories.user_repository import create_first_admin_if_not_exists
from src.app.routes import register_routes
from src.app.settings import settings
from src.app.utils.exceptions import BaseAppException, add_db_exception_handlers
from src.app.utils.logger import startup_logger

startup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        await create_first_admin_if_not_exists(session)

    app.state.redis = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=2.0,
        socket_timeout=2.0,
        retry_on_timeout=False,
        retry=None,
    )

    yield

    await app.state.redis.close()


app = FastAPI(lifespan=lifespan, title="FastChat", version=settings.version)

register_routes(app)

logger.info("Server successfully started")


@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


add_db_exception_handlers(app)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server Error",
                "details": {},
            }
        },
    )
