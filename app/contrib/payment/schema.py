from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import Field, condecimal

from app.core.schema import BaseModel, VisibleBase, ChoiceBase
from app.contrib.payment import (
    PaymentTypeChoices,
    ChargeStatusChoices,
    StorePaymentMethodChoices, TransactionKindChoices,
)
from app.contrib.file.schema import FileVisible


class PaymentAttachmentVisible(BaseModel):
    id: int
    created_at: datetime = Field(alias="createdAt")
    file: FileVisible


class TransactionVisible(BaseModel):
    id: int
    token: str
    kind: ChoiceBase[TransactionKindChoices]
    is_success: bool = Field(alias='isSuccess')
    is_action_required: bool = Field(alias='isActionRequired')
    currency: str
    amount: Decimal
    error: Optional[str] = None
    customer_id: Optional[str] = Field(alias="customerId")
    gateway_response: dict = Field(alias="gatewayResponse")
    is_already_processed: bool = Field(alias="isAlreadyProcessed")
    created_at: datetime = Field(alias="createdAt")
    payment_id: UUID = Field(alias="paymentId")


class PaymentStaff(BaseModel):
    id: UUID
    username: str


class PaymentBase(BaseModel):
    pass


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(PaymentBase):
    pass


class PaymentDeposit(BaseModel):
    amount: condecimal(max_digits=12, decimal_places=2) = Field(..., gt=0)
    gateway: str = Field(..., max_length=255)


class PaymentVisible(VisibleBase):
    id: UUID
    wallet_id: Optional[UUID] = Field(alias="walletId")
    staff_id: Optional[UUID] = Field(alias="staffId")
    user_id: Optional[UUID] = Field(alias="staffId")

    payment_type: ChoiceBase[PaymentTypeChoices] = Field(alias="paymentType")
    gateway: str
    is_active: bool = Field(alias="isActive")
    to_confirm: bool = Field(alias='toConfirm')
    charge_status: ChoiceBase[ChargeStatusChoices] = Field(alias='chargeStatus')
    token: Optional[str] = None
    total_amount: Decimal = Field(alias="totalAmount")
    captured_amount: Decimal = Field(alias="capturedAmount")
    currency: str
    store_payment_method: ChoiceBase[StorePaymentMethodChoices] = Field(alias="storePaymentMethod")
    cc_first_digits: Optional[str] = Field(alias="ccFirstDigits")
    cc_last_digits: Optional[str] = Field(alias="ccLastDigits")
    cc_brand: Optional[str] = Field(alias="ccBrand")
    cc_exp_month: Optional[str] = Field(alias="ccExpMonth")
    cc_exp_year: Optional[str] = Field(alias="ccExpYear")
    payment_method_type: Optional[str] = Field(alias="paymentMethodType")
    customer_ip_address: Optional[str] = Field(alias="customerIpAddress")
    extra_data: Optional[dict] = Field(alias="extraData")
    return_url: Optional[str] = Field(alias="returnUrl")
    psp_reference: Optional[str] = Field(alias="pspReference")

    created_at: datetime = Field(alias="createdAt")
    private_metadata: dict = Field(alias="privateMetadata")
    public_metadata: dict = Field(alias="publicMetadata")

    staff: Optional[PaymentStaff] = None
    transactions: Optional[List[TransactionVisible]] = None
    attachments: Optional[List[PaymentAttachmentVisible]] = None
