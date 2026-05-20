from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):  # noqa: UP046
    items: list[T]
    page: int
    page_size: int
    total: int
