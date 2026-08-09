from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=32)
    user_name: str = Field(unique=True, min_length=3, max_length=16)
    password: str = Field(max_length=60)