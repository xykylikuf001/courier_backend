from typing import Optional
from pydantic import Field, condecimal, field_validator, AwareDatetime
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.core.schema import BaseModel, VisibleBase, ChoiceBase, non_nullable_field, string_to_null_field
from app.contrib.order import OrderStatusChoices, ShippingTypeChoices


class OrderBase(BaseModel):
    code: Optional[str] = Field(None, max_length=255)
    status: Optional[OrderStatusChoices] = None
    sender_name: Optional[str] = Field(None, alias="senderName", max_length=255)
    sender_phone: Optional[str] = Field(None, alias="senderPhone", max_length=255)
    receiver_name: Optional[str] = Field(None, alias="receiverName", max_length=255)
    receiver_phone: Optional[str] = Field(None, alias="receiverPhone", max_length=255)
    billing_address: Optional[str] = Field(None, alias="billingAddress", max_length=500)
    shipping_address: Optional[str] = Field(None, alias="shippingAddress", max_length=500)
    note: Optional[str] = Field(None, max_length=500)
    weight: Optional[str] = Field(None, max_length=255)
    price: Optional[condecimal(decimal_places=2, max_digits=12)] = None
    shipping_amount: Optional[condecimal(decimal_places=2, max_digits=12)] = Field(None, alias="shippingAmount")
    shipping_type: Optional[ShippingTypeChoices] = Field(None, alias="shippingType")
    completed_at: Optional[AwareDatetime] = Field(None, alias="completedAt")
    _normalize_empty = field_validator(
        'price', "weight", "shipping_amount", "completed_at", mode="before",
    )(string_to_null_field)
    _normalize_nullable = field_validator(
        "status",
        "sender_name",
        "sender_phone",
        "receiver_name",
        "receiver_phone",
        "shipping_amount",
        "shipping_type",
    )(non_nullable_field)


class OrderCreate(BaseModel):
    sender_name: str = Field(..., alias="senderName", max_length=255)
    sender_phone: str = Field(..., alias="senderPhone", max_length=255)
    receiver_name: str = Field(..., alias="receiverName", max_length=255)
    receiver_phone: str = Field(..., alias="receiverPhone", max_length=255)
    weight: Optional[str] = Field(None, max_length=255)
    price: Optional[condecimal(decimal_places=2, max_digits=12)] = None

    billing_address: str = Field(..., alias="billingAddress", max_length=500)
    shipping_address: str = Field(..., alias="shippingAddress", max_length=500)
    shipping_type: ShippingTypeChoices = Field(..., alias="shippingType")
    note: Optional[str] = Field(None, max_length=500)

    _normalize_empty = field_validator(
        'price', "weight", mode="before"
    )(string_to_null_field)


class OrderUser(VisibleBase):
    id: UUID
    name: str


class OrderVisible(VisibleBase):
    id: UUID
    code: Optional[str] = None
    status: ChoiceBase[OrderStatusChoices]
    sender_name: str = Field(alias="senderName", max_length=255)
    sender_phone: str = Field(alias="senderPhone", max_length=255)
    receiver_name: str = Field(alias="receiverName", max_length=255)
    receiver_phone: str = Field(alias="receiverPhone", max_length=255)

    billing_address: str = Field(alias="billingAddress", max_length=500)
    shipping_address: str = Field(alias="shippingAddress", max_length=500)
    created_at: datetime = Field(alias="createdAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    shipping_type: ChoiceBase[ShippingTypeChoices] = Field(alias="shippingType")
    shipping_amount: Optional[Decimal] = Field(None, alias="shippingAmount")
    price: Optional[Decimal] = None
    weight: Optional[str] = None
    note: Optional[str] = None

    user: Optional[OrderUser] = None

    @field_validator("code")
    def normalize_code(cls, v: Optional[str]):
        if v is not None:
            return v[:6]
        return v
