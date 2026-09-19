from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from redis.exceptions import RedisError
from sqlalchemy.exc import InterfaceError, OperationalError


class BaseAppException(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "BAD_REQUEST"
    default_message: str = "An error occurred while processing your request"

    def __init__(
        self, message: str | None = None, details: dict[str, Any] | None = None
    ):
        self.message = message or self.default_message
        self.details = details or {}


def add_db_exception_handlers(app: FastAPI):
    @app.exception_handler(RedisError)
    async def redis_unavailable_error(request: Request, exc: Exception):
        logger.exception(f"Redis unavailable {request.url.path}: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "REDIS_UNAVAILABLE",
                    "message": "Redis is temporarily unavailable",
                    "details": {},
                }
            },
        )

    @app.exception_handler(OperationalError)
    async def db_operational_error(request: Request, exc: Exception):
        logger.exception(f"Database unavailable {request.url.path}: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database is temporarily unavailable",
                    "details": {},
                }
            },
        )

    @app.exception_handler(InterfaceError)
    async def db_interface_error(request: Request, exc: Exception):
        logger.exception(f"Database unavailable {request.url.path}: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database is temporarily unavailable",
                    "details": {},
                }
            },
        )


class Conflict(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    default_message = "Conflict"


class Forbidden(BaseAppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    default_message = "You don't have permission to perform this action"


class InvalidCredentials(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_CREDENTIALS"
    default_message = "Invalid credentials"


class UserNotFound(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "USER_NOT_FOUND"
    default_message = "User not found"


class JWTExpired(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "JWT_EXPIRED"
    default_message = "JWT has expired"


class InvalidJWTSignature(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_JWT_SIGNATURE"
    default_message = "JWT signature is invalid"


class InvalidJWT(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_JWT"
    default_message = "JWT is invalid"


class JWTDecodeError(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "JWT_DECODE_ERROR"
    default_message = "An error occurred while decoding the JWT"


class RefreshTokenNotGranted(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "REFRESH_TOKEN_NOT_GRANTED"
    default_message = "Refresh token not granted"


class SessionExpired(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "SESSION_EXPIRED"
    default_message = "Session not found or expired"
