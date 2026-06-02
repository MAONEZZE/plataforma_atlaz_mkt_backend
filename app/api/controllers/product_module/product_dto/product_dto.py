from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    name: str
    value: Decimal = Field(ge=0)
    description: str | None = None
    cover_photo: str | None = None


class ProductPatchIn(BaseModel):
    name: str | None = None
    value: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    cover_photo: str | None = None


class ProductOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    cover_photo: str | None
    created_at: datetime


class AssignProductBody(BaseModel):
    product_id: UUID | None = None
