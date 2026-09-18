from fastapi import APIRouter, Depends, status
from src.app.utils.dependencies import RedisSessionDep, get_refresh_token, get_current_user
from src.app.services import session_service
from src.app.repositories import token_repository
from src.app.schemas.auth_schema import SessionReadSchema
from src.app.models import User
from src.app.utils.errors import error_response, errors_list, error_example, JWT_ERRORS, SESSION_ERRORS
from src.app.utils.exceptions import (UserNotFound, SessionExpired, Forbidden)
from uuid import UUID

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("/",
            status_code=status.HTTP_200_OK,
            response_model=dict[UUID, SessionReadSchema],
            responses={
                **errors_list(
                    status.HTTP_401_UNAUTHORIZED,
                    "Auth Errors",
                    {**JWT_ERRORS, **SESSION_ERRORS}
                )
            })
async def get_sessions(redis: RedisSessionDep,
                       user: User = Depends(get_current_user),
                       refresh_token: str = Depends(get_refresh_token)):
    """
    Returns all user sessions
    """

    session_uuid = await token_repository.get_session_uuid_from_refresh(redis, refresh_token)

    user_sessions = await session_service.get_user_sessions(redis, user, session_uuid)

    return user_sessions

@router.post("/logout",
             status_code=status.HTTP_204_NO_CONTENT,
             response_model=None,
             responses={
                **errors_list(
                    status.HTTP_401_UNAUTHORIZED,
                    "Auth Errors",
                    {**JWT_ERRORS, **SESSION_ERRORS}
                ),
                **error_response(UserNotFound, "Current User Not Found Error"),
                **error_response(Forbidden, "Forbidden Error")
             })
async def logout(redis: RedisSessionDep,
                 user: User = Depends(get_current_user),
                 refresh_token: str = Depends(get_refresh_token)):
    """
    Invalidates the current session
    """

    await session_service.logout(redis, user, refresh_token)

    return

@router.post("/logout-all",
             status_code=status.HTTP_204_NO_CONTENT,
             response_model=None,
             responses={
                 **errors_list(
                    status.HTTP_401_UNAUTHORIZED,
                    "Auth Errors",
                    {**JWT_ERRORS}
                 ),
                 **error_response(UserNotFound, "Current User Not Found Error")
             })
async def logout_all(redis: RedisSessionDep,
                 user: User = Depends(get_current_user)):
    """
    Invalidates all user sessions
    """

    await session_service.logout_all(redis, user)

    return

@router.delete("/revoke/{session_uuid}",
               status_code=status.HTTP_204_NO_CONTENT,
               response_model=None,
               responses={
                   **errors_list(
                        status.HTTP_401_UNAUTHORIZED,
                        "Auth Errors",
                        {
                            **JWT_ERRORS,
                            **error_example(SessionExpired, "Session Not Found Or Expired Error")
                        }
                    ),
                   **error_response(UserNotFound, "Current User Not Found Error"),
                   **error_response(Forbidden, "Forbidden Error")
               })
async def revoke_session_by_uuid(redis: RedisSessionDep,
                 session_uuid: UUID,
                 user: User = Depends(get_current_user)):
    """
    Invalidates a user session by UUID
    """

    await session_service.revoke_session(redis, user, session_uuid)

    return