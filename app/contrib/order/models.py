from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from sqlalchemy_utils import ChoiceType
from sqlalchemy import String, ForeignKey, Text, DECIMAL, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as SUUID

from app.db.models import CreationModificationDateBase, ModelWithMetadataBase, UUIDBase
from app.contrib.order import OrderStatusChoices, ShippingTypeChoices


def generate_order_code() -> str:
    """
    Generates a unique order code in hexadecimal format.
    """
    return uuid4().hex.upper()


class Order(CreationModificationDateBase, ModelWithMetadataBase, UUIDBase):
    code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=generate_order_code)
    status: Mapped[OrderStatusChoices] = mapped_column(
        ChoiceType(choices=OrderStatusChoices, impl=String(50)),
        nullable=False,
        default=OrderStatusChoices.pending
    )

    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='RESTRICT', name='fx_order_user_id'),
        nullable=False,
    )
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_phone: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)

    shipping_address: Mapped[int] = mapped_column(Text, nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True), nullable=True
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True), nullable=True,
    )
    shipping_type: Mapped[ShippingTypeChoices] = mapped_column(
        ChoiceType(choices=ShippingTypeChoices, impl=String(20)),
        nullable=False
    )
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user = relationship("User", lazy="noload", viewonly=True)

class Invoice(CreationModificationDateBase, ModelWithMetadataBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='RESTRICT', name='fx_invoice_user_id'),
        nullable=False,
    )
    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='RESTRICT', name='fx_order_order_id'),
        nullable=False,
    )
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)


class OrderNote(CreationModificationDateBase):
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='CASCADE', name='fx_order_note_order_id'),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_order_note_user_id'),
        nullable=False,
    )
