from src.app.models import User
from src.app.models.user_model import UserRoles
from src.app.utils.exceptions import Forbidden


def check_user_access(
    current_user: User, target_user_id: int, error_msg: str | None = None
) -> bool:
    if current_user.role == UserRoles.ADMIN or current_user.id == target_user_id:
        return True
    else:
        raise Forbidden(message=error_msg)
