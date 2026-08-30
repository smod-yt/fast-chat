from fastapi import APIRouter
from src.app.db import AsyncSessionDep
from src.app.schemas.auth_schema import RegisterSchema
from src.app.schemas.user_schema import UserResponse
from src.app.services import auth_service
from src.app.utils.errors import error_response
from src.app.utils.exceptions import Conflict

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register",
             response_model=UserResponse,
             responses={
                 **error_response(
                     Conflict,
                     "Conflict Error"
                 )
             })
async def register(session: AsyncSessionDep, data: RegisterSchema):
    """
    Creates a user
    """

    result = await auth_service.register(session, data)
    return result