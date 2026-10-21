from decimal import Decimal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.transaction import TransactionStatus


class TransactionCreate(BaseModel):
    customer_id: UUID
    business_id: UUID

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    currency: str = Field(
        default="NGN",
        min_length=3,
        max_length=3
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference: str
    customer_id: UUID
    business_id: UUID
    amount: Decimal
    currency: str
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

