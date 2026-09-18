from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class ListResponse(BaseModel, Generic[T]):
    items: list[T]