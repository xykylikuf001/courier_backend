from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy_utils import ChoiceType
from sqlalchemy import (
    String, ForeignKey, Text, DECIMAL, DateTime, select, Sequence, Integer, JSON, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy.dialects.postgresql import UUID as SUUID

from app.conf import LanguagesChoices
from app.db.session import SessionLocal
from app.db.models import CreationModificationDateBase, ModelWithMetadataBase, UUIDBase, metadata, Base
from app.contrib.order import (
    OrderStatusChoices, ShippingMethodChoices, OrderEventChoices,
    OrderChargeStatusChoices, OrderGrantedRefundStatusChoices, OrderOriginChoices, FulfillmentStatusChoices
)
from app.utils.prices import Money

order_code_seq = Sequence('order_order_number_seq', metadata=metadata)


def generate_order_code() -> str:
    """
    Generates a unique order code in hexadecimal format.
    """

    with SessionLocal() as session:
        # Fetch the next value from the sequence
        next_code = session.execute(select(order_code_seq.next_value())).scalar()
        return f"ORD-{next_code:06}"  # Example format: ORD-000001


class Order(CreationModificationDateBase, ModelWithMetadataBase, UUIDBase):
    code: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=False, default=generate_order_code,
    )
    status: Mapped[OrderStatusChoices] = mapped_column(
        ChoiceType(choices=OrderStatusChoices, impl=String(32)),
        nullable=False,
        default=OrderStatusChoices.unconfirmed
    )
    charge_status: Mapped[OrderChargeStatusChoices] = mapped_column(
        ChoiceType(choices=OrderChargeStatusChoices, impl=String(32)),
        default=OrderChargeStatusChoices.none, nullable=False
    )

    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='SET NULL', name='fx_order_user_id'),
        nullable=True,
    )
    language_code: Mapped[LanguagesChoices] = mapped_column(
        ChoiceType(choices=LanguagesChoices, impl=String(35)),
        default=LanguagesChoices.TURKMEN
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    street_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    place_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("place.id", name='fx_order_place_id', ondelete="SET NULL")
    )
    place_full_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default="")
    origin: Mapped[OrderOriginChoices] = mapped_column(
        ChoiceType(choices=OrderOriginChoices, impl=String(32)),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(String(50), nullable=False)
    shipping_method_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('shipping_method.id', name="fx_order_shipping_method_id", ondelete="SET NULL"),
        nullable=True
    )
    shipping_method_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )
    shipping_price_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    base_shipping_price_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    un_discounted_base_shipping_price_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    un_discounted_total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False
    )
    total_charged_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        default=Decimal("0.0"),
        nullable=True
    )
    subtotal_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False
    )
    extra_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", lazy="noload", viewonly=True)

    @hybrid_property
    def base_shipping_price(self):
        return Money(self.base_shipping_price_amount, self.currency)


class OrderLine(ModelWithMetadataBase):
    shipping_method_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )
    shipping_method_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('shipping_method.id', name="fx_order_ln_sh_method_id", ondelete="SET NULL"),
        nullable=True
    )
    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='CASCADE', name='fx_order_line_order_id'),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(50), nullable=False)
    total_price_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False
    )
    un_discounted_total_price_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False
    )
    shipping_price_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    un_discounted_shipping_price_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    price_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    extra_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=True)


class Fulfillment(CreationModificationDateBase, ModelWithMetadataBase):
    fulfillment_order: Mapped[int] = mapped_column(Integer, nullable=False)

    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='CASCADE', name='fx_fulfillment_order_id'),
        nullable=False,
    )
    status: Mapped[FulfillmentStatusChoices] = mapped_column(
        ChoiceType(choices=FulfillmentStatusChoices, impl=String(32)),
        default=FulfillmentStatusChoices.fulfilled, nullable=False
    )
    shipping_refund_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )
    total_refund_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True
    )


class FulfillmentLine(Base):
    order_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('order_line.id', name='fx_full_line_order_line_id', ondelete="CASCADE"),
        nullable=False
    )
    fulfillment_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('fulfillment.id', ondelete='CASCADE', name='fx_full_line_full_id'),
        nullable=True,
    )


class OrderEvent(CreationModificationDateBase):
    """Model used to store events that happened during the order lifecycle.

    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of order

    """
    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='CASCADE', name='fx_order_event_order_id'),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='SET NULL', name='fx_order_event_user_id'),
        nullable=True,
    )
    event_type: Mapped[OrderEventChoices] = ChoiceType(
        choices=OrderEventChoices, impl=String(255),
    )
    parameters: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)


class OrderGrantedRefund(CreationModificationDateBase):
    amount_value: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=True, default=Decimal("0.0")
    )
    currency: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='SET NULL', name='fx_order_gr_user_id'),
        nullable=True,
    )

    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='CASCADE', name='fx_order_gr_order_id'),
        nullable=False,
    )
    shipping_costs_included: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    status: Mapped[OrderGrantedRefundStatusChoices] = mapped_column(
        ChoiceType(choices=OrderGrantedRefundStatusChoices, impl=String(128)),
        nullable=False, default=OrderGrantedRefundStatusChoices.none
    )


class OrderGrantedRefundLine(Base):
    order_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('order_line.id', name='fx_order_gr_ln_order_ln_id', ondelete="CASCADE"),
        nullable=False
    )
    granted_refund_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_granted_refund.id", name='fx_or_gr_ln_or_gr_id', ondelete="CASCADE")
    )
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)


class OrderNote(CreationModificationDateBase):
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    order_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('order.id', ondelete='CASCADE', name='fx_order_note_order_id'),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='SET NULL', name='fx_order_note_user_id'),
        nullable=True,
    )
