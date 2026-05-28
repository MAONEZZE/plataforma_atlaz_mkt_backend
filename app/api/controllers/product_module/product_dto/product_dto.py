from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    name: str
    value: Decimal = Field(ge=0)


class ProductPatchIn(BaseModel):
    name: str | None = None
    value: Decimal | None = Field(default=None, ge=0)


class ProductOut(BaseModel):
    id: UUID
    name: str
    value: Decimal
    created_at: datetime


class AssignProductBody(BaseModel):
    product_id: UUID | None = None
