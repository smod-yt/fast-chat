from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from src.app.db import AsyncSessionDep
from src.app.models import User
from src.app.schemas.chat_schema import (
    ChatCreateSchema,
    ChatResponse,
    ChatUpdateSchema,
    PaginatedChatsResponse,
)
from src.app.services import chat_service
from src.app.utils import limiter
from src.app.utils.dependencies import get_current_user
from src.app.utils.errors import (
    JWT_ERRORS,
    RATE_LIMIT_ERROR,
    REQUEST_ERRORS,
    error_response,
    errors_list,
)
from src.app.utils.exceptions import (
    BadRequest,
    ChatNotFound,
    Conflict,
    Forbidden,
    UserNotFound,
)

router = APIRouter(prefix="/chats", tags=["Chats"])

CHAT_ACCESS_ERRORS = {
    **REQUEST_ERRORS,
    **errors_list(
        status.HTTP_401_UNAUTHORIZED,
        "Auth Errors",
        {**JWT_ERRORS},
    ),
    **RATE_LIMIT_ERROR,
    **error_response(Forbidden, "Forbidden Error"),
    **error_response(ChatNotFound, "Chat Not Found Error"),
    **error_response(UserNotFound, "User Not Found Error"),
    **error_response(Conflict, "Conflict Error"),
    **error_response(BadRequest, "Bad Request Error"),
}


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedChatsResponse,
    responses=CHAT_ACCESS_ERRORS,
)
@limiter.limit("60/minute")
async def get_my_chats(
    request: Request,
    response: Response,
    session: AsyncSessionDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a paginated list of the current user's chats
    """
    chats, total = await chat_service.get_my_chats(
        session, current_user, page=page, limit=limit
    )
    return PaginatedChatsResponse(
        items=chats,
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedChatsResponse,
    responses=CHAT_ACCESS_ERRORS,
)
@limiter.limit("60/minute")
async def get_user_chats(
    request: Request,
    response: Response,
    session: AsyncSessionDep,
    user_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a paginated list of a user's chats. Others require moderator role or higher
    """
    chats, total = await chat_service.get_user_chats(
        session, current_user, user_id, page=page, limit=limit
    )
    return PaginatedChatsResponse(
        items=chats,
        total=total,
        page=page,
        limit=limit,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ChatResponse,
    responses=CHAT_ACCESS_ERRORS,
)
@limiter.limit("30/minute")
async def create_chat(
    request: Request,
    response: Response,
    session: AsyncSessionDep,
    data: ChatCreateSchema,
    current_user: User = Depends(get_current_user),
):
    """
    Creates a private chat with another user
    """
    return await chat_service.create_chat(session, current_user, data)


@router.patch(
    "/{chat_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=ChatResponse,
    responses=CHAT_ACCESS_ERRORS,
)
@limiter.limit("30/minute")
async def update_chat(
    request: Request,
    response: Response,
    session: AsyncSessionDep,
    chat_uuid: UUID,
    data: ChatUpdateSchema,
    current_user: User = Depends(get_current_user),
):
    """
    Updates chat information (chat blocking). Owner, moderator or higher
    """
    return await chat_service.update_chat(session, current_user, chat_uuid, data)


@router.delete(
    "/{chat_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=CHAT_ACCESS_ERRORS,
)
@limiter.limit("30/minute")
async def delete_chat(
    request: Request,
    response: Response,
    session: AsyncSessionDep,
    chat_uuid: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a chat with cascade. Owner, admin or higher
    """
    await chat_service.delete_chat(session, current_user, chat_uuid)
    return
