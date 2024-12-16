from typing import Optional
from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, DECIMAL, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import ChoiceType

from app.db.models import CreationModificationDateBase, UUIDBase, ModelWithMetadataBase, Base
from app.contrib.discount import DiscountTypeChoices, DiscountValueTypeChoices, VoucherTypeChoices
from app.utils.datetime.timezone import now


class Voucher(ModelWithMetadataBase):
    type: Mapped[VoucherTypeChoices] = mapped_column(
        ChoiceType(choices=VoucherTypeChoices, impl=String(64)),
        nullable=False, default=VoucherTypeChoices.entire_order
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now)
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    # this field indicates if discount should be applied per order or
    # individually to every item
    apply_once_per_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    apply_once_per_customer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    single_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    only_for_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    discount_value_type: Mapped[DiscountTypeChoices] = mapped_column(
        ChoiceType(choices=DiscountValueTypeChoices, impl=String(64)),
        nullable=False, default=DiscountValueTypeChoices.fixed
    )


class VoucherCode(CreationModificationDateBase):
    code: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    voucher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('voucher.id', name='fx_voucher_code_voucher_id', ondelete="CASCADE"),
        nullable=False
    )


class VoucherCustomer(Base):
    voucher_code_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('voucher_code.id', name='fx_vcher_cus_vcher_code_id', ondelete="CASCADE"),
        nullable=False
    )
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)


class BaseDiscount(CreationModificationDateBase, UUIDBase):
    __abstract__ = True
    type: Mapped[DiscountTypeChoices] = mapped_column(
        ChoiceType(choices=DiscountTypeChoices, impl=String(64)),
        nullable=False, default=DiscountTypeChoices.manual
    )
    value_type: Mapped[DiscountTypeChoices] = mapped_column(
        ChoiceType(choices=DiscountValueTypeChoices, impl=String(64)),
        nullable=False, default=DiscountValueTypeChoices.fixed
    )

    value: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False,
        default=Decimal("0.0")
    )
    amount_value: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False,
        default=Decimal("0.0")
    )
    currency: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voucher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('voucher.id', name='fx_discount_voucher_id', ondelete="SET NULL"),
        nullable=True
    )
    voucher_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class OrderDiscount(BaseDiscount):
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('order.id', name='fx_o_dis_order_id', ondelete="CASCADE"),
        nullable=True
    )


class OrderLineDiscount(BaseDiscount):
    line_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('order_line.id', name='fx_o_line_dis_o_ln_id', ondelete="CASCADE"),
        nullable=True
    )
    # This will ensure that we always apply a single specific discount type.
    unique_type:  Mapped[DiscountTypeChoices] = mapped_column(
        ChoiceType(choices=DiscountTypeChoices, impl=String(64)),
        nullable=True,
    )
