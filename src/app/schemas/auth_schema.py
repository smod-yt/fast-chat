from pydantic import BaseModel, Field

class RegisterSchema(BaseModel):
    name:      str = Field(min_length=1, max_length=32)
    user_name: str = Field(min_length=3, max_length=16, pattern=r"^[a-z0-9_-]+$")
    password:  str = Field(max_length=60)