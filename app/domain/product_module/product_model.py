from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class Product:
    id: UUID
    name: str
    value: Decimal
    created_at: datetime
