from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
from src.app.settings import settings
from src.app.db import AsyncSessionLocal
from src.app.utils.exceptions import BaseAppException
from src.app.routes import register_routes
from src.app.utils.logger import startup_logger
from src.app.repositories.user_repository import create_first_admin_if_not_exists

startup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        await create_first_admin_if_not_exists(session)

    yield

app = FastAPI(
    lifespan=lifespan,
    title="FastChat",
    version=settings.version
)

register_routes(app)

logger.info("Server successfully started")

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code":    exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code":    "INTERNAL_SERVER_ERROR",
                "message": "Internal server Error",
                "details": {}
            }
        }
    )