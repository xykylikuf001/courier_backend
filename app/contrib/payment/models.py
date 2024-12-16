from typing import Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Boolean, Text, DECIMAL, Integer, JSON

from sqlalchemy_utils import ChoiceType, IPAddressType, URLType
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as SUUID

from app.contrib.file.models import File
from app.db.models import CreationModificationDateBase, ModelWithMetadataBase, UUIDBase
from app.contrib.payment import (
    ChargeStatusChoices,
    CustomPaymentChoices,
    TransactionKindChoices,
    StorePaymentMethodChoices,
    PaymentTypeChoices
)

__all__ = {'Transaction', 'Payment', "PaymentAttachment"}


class Payment(UUIDBase, CreationModificationDateBase, ModelWithMetadataBase):
    """A model that represents a single payment.

    This might be a transactable payment information such as credit card
    details, gift card information or a customer's authorization to charge
    their PayPal account.

    All payment process related pieces of information are stored
    at the gateway level, we are operating on the reusable token
    which is a unique identifier of the customer for given gateway.

    Several payment methods can be used within a single order. Each payment
    method may consist of multiple transactions.
    """

    staff_id: Mapped[Optional[UUID]] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey("user.id", name="fx_payment_staff_id", ondelete="SET NULL"),
        nullable=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey("user.id", name="fx_payment_user_id", ondelete="SET NULL"),
        nullable=True
    )
    wallet_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey("wallet.id", name="fx_payment_wallet_id", ondelete="RESTRICT"),
        nullable=True
    )

    payment_type: Mapped[PaymentTypeChoices] = mapped_column(
        ChoiceType(choices=PaymentTypeChoices, impl=String(25)),
        nullable=False
    )

    gateway: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    to_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    charge_status: Mapped[ChargeStatusChoices] = mapped_column(
        ChoiceType(choices=ChargeStatusChoices, impl=String(25)),
        default=ChargeStatusChoices.NOT_CHARGED, nullable=False
    )

    token: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default='')

    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True),
        nullable=False
    )
    captured_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=2, asdecimal=True),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(String(25), default='USD', nullable=False)
    store_payment_method: Mapped[StorePaymentMethodChoices] = mapped_column(
        ChoiceType(choices=StorePaymentMethodChoices, impl=String(11), ),
        default=StorePaymentMethodChoices.NONE, nullable=False
    )

    cc_first_digits: Mapped[Optional[str]] = mapped_column(String(6), default='', nullable=True)
    cc_last_digits: Mapped[Optional[str]] = mapped_column(String(4), default='', nullable=True)
    cc_brand: Mapped[Optional[str]] = mapped_column(String(40), default='', nullable=True)
    cc_exp_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cc_exp_year: Mapped[Optional[str]] = mapped_column(Integer, nullable=True)
    payment_method_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_ip_address: Mapped[Optional[str]] = mapped_column(IPAddressType, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSON, default={}, nullable=False
    )
    return_url: Mapped[Optional[str]] = mapped_column(URLType, nullable=True, default='')
    psp_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default='')

    staff = relationship("User", uselist=False, viewonly=True, lazy='noload', foreign_keys="Payment.staff_id")
    # user = relationship("User", uselist=False, viewonly=True, lazy='noload', foreign_keys="Payment.user_id")
    transactions = relationship("Transaction", viewonly=True, lazy="noload")
    attachments = relationship("PaymentAttachment", viewonly=True, lazy="noload")

    @hybrid_method
    def get_charge_amount(self):
        """Retrieve the maximum capture possible."""
        return self.total_amount - self.captured_amount

    @hybrid_method
    def not_charged(self):
        return self.charge_status == ChargeStatusChoices.NOT_CHARGED

    @hybrid_method
    def can_authorize(self):
        return self.is_active and self.not_charged

    @hybrid_method
    def can_capture(self):
        if not (self.is_active and self.not_charged):
            return False
        return True

    @hybrid_method
    def can_void(self):
        return self.is_active and self.not_charged

    @hybrid_method
    def can_refund(self):
        can_refund_charge_status = (
            ChargeStatusChoices.PARTIALLY_CHARGED,
            ChargeStatusChoices.FULLY_CHARGED,
            ChargeStatusChoices.PARTIALLY_REFUNDED,
        )
        return self.charge_status in can_refund_charge_status

    @hybrid_method
    def can_confirm(self):
        return self.is_active and self.not_charged

    @hybrid_method
    def is_manual(self):
        return self.gateway == CustomPaymentChoices.MANUAL.value


class Transaction(CreationModificationDateBase):
    staff_id: Mapped[Optional[UUID]] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey("user.id", name="fx_trn_staff_id", ondelete="SET NULL"),
        nullable=True
    )
    token: Mapped[str] = mapped_column(Text, nullable=False, default='')
    kind: Mapped[TransactionKindChoices] = mapped_column(
        ChoiceType(choices=TransactionKindChoices, impl=String(25), ), nullable=False
    )
    is_success: Mapped[bool] = mapped_column(Boolean, default=False)
    is_action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    action_required_data: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)
    currency: Mapped[str] = mapped_column(String(25), nullable=False, default='USD')
    amount: Mapped[Decimal] = mapped_column(DECIMAL(precision=10, scale=2, asdecimal=True))
    error: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default='')
    customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_response: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)
    is_already_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    payment_id: Optional[int] = mapped_column(
        SUUID(as_uuid=True), ForeignKey('payment.id', ondelete='CASCADE'), nullable=False
    )


class PaymentAttachment(CreationModificationDateBase):
    __tablename__ = "payment_attachment"
    payment_id: Mapped[int] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('payment.id', name='fx_pa_payment_id', ondelete="CASCADE"),
        nullable=False
    )
    file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('file.id', ondelete="RESTRICT", name="fx_pa_file_id"),
        nullable=False, unique=True
    )

    file = relationship(
        File, lazy='noload', single_parent=True, uselist=False,
    )
