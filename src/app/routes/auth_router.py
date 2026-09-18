from fastapi import APIRouter, Request, Response, Depends, status
from src.app.db import AsyncSessionDep
from src.app.settings import settings
from src.app.schemas.auth_schema import RegisterSchema, LoginSchema, AuthResponse, AccessTokenSchema
from src.app.services import auth_service
from src.app.utils.errors import error_response
from src.app.utils.exceptions import Conflict, InvalidCredentials, SessionExpired
from src.app.utils.dependencies import RedisSessionDep, get_refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.HTTPS,
        samesite="lax",
        max_age=settings.REFRESH_EXPIRES_TIME
    )

@router.post("/register",
             status_code=status.HTTP_201_CREATED,
             response_model=AuthResponse,
             responses={
                 **error_response(
                     Conflict,
                     "Conflict Error"
                 )
             })
async def register(session: AsyncSessionDep, response: Response, data: RegisterSchema,
                   request: Request, redis: RedisSessionDep):
    """
    Creates a user. Returns user info and access token
    """

    user, refresh_token, access_token = await auth_service.register(session, data, request, redis)

    set_refresh_cookie(response, refresh_token)

    return {
        "user": user,
        "access_token": access_token
    }

@router.post("/login",
             status_code=status.HTTP_200_OK,
             response_model=AuthResponse,
             responses={
                 **error_response(
                     InvalidCredentials,
                     "Invalid Credentials Error"
                 )
             })
async def login(session: AsyncSessionDep, response: Response, data: LoginSchema,
                request: Request, redis: RedisSessionDep):
    """
    Performs authorization. Returns user info and access token
    """

    user, refresh_token, access_token = await auth_service.login(session, data, request, redis)

    set_refresh_cookie(response, refresh_token)

    return {
        "user": user,
        "access_token": access_token
    }

@router.post("/refresh",
             status_code=status.HTTP_200_OK,
             response_model=AccessTokenSchema,
             responses={
                 **error_response(
                     SessionExpired,
                     "Session Expired Error"
                 )
             })
async def refresh(request: Request, response: Response,
                  redis: RedisSessionDep, refresh_token: str = Depends(get_refresh_token)):
    """
    Updates the refresh token and returns a new access token
    """

    new_refresh_token, access_token = await auth_service.refresh(request, redis, refresh_token)

    set_refresh_cookie(response, new_refresh_token)
    
    return {"access_token": access_token}