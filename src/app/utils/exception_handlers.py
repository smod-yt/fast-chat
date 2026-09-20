from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from redis.exceptions import RedisError
from sqlalchemy.exc import InterfaceError, OperationalError

from src.app.utils.exceptions import BaseAppException


def error_response(
    status_code: status,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
        headers=headers,
    )


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException):
        return error_response(exc.status_code, exc.error_code, exc.message, exc.details)

    @app.exception_handler(RedisError)
    async def redis_unavailable_error(request: Request, exc: Exception):
        logger.exception(f"Redis unavailable {request.url.path}: {exc}")
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "REDIS_UNAVAILABLE",
            "Redis is temporarily unavailable",
        )

    @app.exception_handler(OperationalError)
    async def db_operational_error(request: Request, exc: Exception):
        logger.exception(f"Database unavailable {request.url.path}: {exc}")
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "DATABASE_UNAVAILABLE",
            "Database is temporarily unavailable",
        )

    @app.exception_handler(InterfaceError)
    async def db_interface_error(request: Request, exc: Exception):
        logger.exception(f"Database unavailable {request.url.path}: {exc}")
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "DATABASE_UNAVAILABLE",
            "Database is temporarily unavailable",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_SERVER_ERROR",
            "Internal server Error",
        )
