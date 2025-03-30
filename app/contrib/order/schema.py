from typing import Optional, List
from pydantic import Field, condecimal, field_validator, AwareDatetime
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.core.schema import BaseModel, VisibleBase, ChoiceBase, non_nullable_field, string_to_null_field
from app.contrib.order import OrderStatusChoices, ShippingMethodChoices


# class OrderBase(BaseModel):
#     code: Optional[str] = Field(None, max_length=255)
#     status: Optional[OrderStatusChoices] = None
#     # sender_name: Optional[str] = Field(None, alias="senderName", max_length=255)
#     # sender_phone: Optional[str] = Field(None, alias="senderPhone", max_length=255)
#     # receiver_name: Optional[str] = Field(None, alias="receiverName", max_length=255)
#     # receiver_phone: Optional[str] = Field(None, alias="receiverPhone", max_length=255)
#     # billing_address: Optional[str] = Field(None, alias="billingAddress", max_length=500)
#     # shipping_address: Optional[str] = Field(None, alias="shippingAddress", max_length=500)
#     customer_note: Optional[str] = Field(None, max_length=500)
#     # weight: Optional[str] = Field(None, max_length=255)
#     # price: Optional[condecimal(decimal_places=2, max_digits=12)] = None
#     # shipping_amount: Optional[condecimal(decimal_places=2, max_digits=12)] = Field(None, alias="shippingAmount")
#     # shipping_type: Optional[ShippingTypeChoices] = Field(None, alias="shippingType")
#     # completed_at: Optional[AwareDatetime] = Field(None, alias="completedAt")
#     _normalize_empty = field_validator(
#         'price', "weight", "shipping_amount", "completed_at", mode="before",
#     )(string_to_null_field)
#     _normalize_nullable = field_validator(
#         "status",
#         "sender_name",
#         "sender_phone",
#         "receiver_name",
#         "receiver_phone",
#         "shipping_amount",
#         "shipping_type",
#     )(non_nullable_field)

class OrderLineCheckout(BaseModel):
    name: str = Field(..., alias="name", max_length=255)
    phone: str = Field(..., alias="phone", max_length=255)
    price: Optional[condecimal(decimal_places=2, max_digits=12)] = None
    note: Optional[str] = Field(None, max_length=500)


class OrderCheckout(BaseModel):
    name: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=255)
    shipping_method: ShippingMethodChoices = Field(..., alias="shippingMethod")
    note: Optional[str] = Field(None, max_length=500)
    street_address: Optional[str] = Field(None, alias="streetAddress", max_length=255)
    save_address: Optional[bool] = Field(False, alias='saveAddress')
    place_id: Optional[int] = Field(None, alias="placeId")
    lines: List[OrderLineCheckout] = Field(..., min_length=1)


class OrderUser(VisibleBase):
    id: UUID
    name: str


class OrderLineVisible(VisibleBase):
    id: int


class OrderVisible(VisibleBase):
    id: UUID
    code: Optional[str] = None
    status: ChoiceBase[OrderStatusChoices]
    name: str
    phone: str
    created_at: datetime = Field(alias="createdAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    shipping_method: ChoiceBase[ShippingMethodChoices] = Field(alias="shippingMethod")
    note: Optional[str] = None

    user: Optional[OrderUser] = None
