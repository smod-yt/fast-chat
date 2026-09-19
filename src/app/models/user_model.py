from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlmodel import Column, Field, SQLModel


class UserRoles(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(min_length=1, max_length=32)
    user_name: str = Field(
        unique=True, min_length=3, max_length=16, regex=r"^[a-z0-9_-]+$"
    )

    role: UserRoles = Field(
        sa_column=Column(SQLEnum(UserRoles), default=UserRoles.USER, nullable=False)
    )

    password: str = Field(max_length=60)
