import json
import logging
from decimal import Decimal

from typing import TYPE_CHECKING, Dict, Optional
from babel.numbers import get_currency_precision
from sqlalchemy import cast, JSON

from app.contrib.payment import (
    StorePaymentMethodChoices, TransactionKindChoices,
    ChargeStatusChoices, PaymentTypeChoices
)
from app.conf.config import settings

from app.utils.prices import quantize_price
from app.contrib.plugins.manager import PluginsManager, get_plugins_manager

# from . import PaymentError, GatewayError
from .interface import PaymentData, GatewayResponse, PaymentMethodInfo
from .repository import payment_repo, transaction_repo
from .exceptions import PaymentError, GatewayError

if TYPE_CHECKING:
    from uuid import UUID
    from enum import Enum
    from sqlalchemy.ext.asyncio import AsyncSession

    from .models import Payment, Transaction

logger = logging.getLogger(__name__)

GENERIC_TRANSACTION_ERROR = "Transaction was unsuccessful"
ALLOWED_GATEWAY_KINDS = {choice for choice in TransactionKindChoices}


def create_payment_information(
        payment: "Payment",
        payment_token: Optional[str] = None,
        amount: Optional["Decimal"] = None,
        customer_id: Optional[str] = None,
        additional_data: Optional[dict] = None,
        customer_email: Optional[str] = None,
) -> "PaymentData":
    """Extract order information along with payment details.

    Returns information required to process payment for optional fraud-prevention mechanisms.
    """

    return PaymentData(
        gateway=payment.gateway,
        token=payment_token,
        amount=amount or payment.total_amount,
        currency=payment.currency,
        payment_id=payment.id,
        customer_ip_address=payment.customer_ip_address,
        customer_id=customer_id,
        data=additional_data or {},
        store_payment_method=payment.store_payment_method,
        payment_metadata=payment.public_metadata,
        psp_reference=payment.psp_reference,
        customer_email=customer_email
    )


async def create_payment(
        async_db: "AsyncSession",
        *,
        gateway: "Enum",
        total: "Decimal",
        captured_amount: "Decimal",
        currency: str,
        commit: bool,
        flush: bool,
        is_active: Optional[bool] = True,
        staff_id: Optional["UUID"] = None,
        user_id: Optional["UUID"] = None,
        wallet_id: Optional["UUID"] = None,
        customer_ip_address: Optional[str] = "",
        payment_token: Optional[str] = "",
        extra_data: Optional[dict] = None,
        return_url: str = None,
        external_reference: Optional[str] = None,
        charge_status: ChargeStatusChoices,
        payment_type: PaymentTypeChoices,
        store_payment_method: StorePaymentMethodChoices = StorePaymentMethodChoices.NONE,
        metadata: Optional[Dict[str, str]] = None,
        force_create: Optional[bool] = False,
) -> "Payment":
    """Create a payment instance.

    This method is responsible for creating payment instances
    """

    if extra_data is None:
        extra_data = {}

    filter_data = {
        "staff_id": staff_id,
        "user_id": user_id,
        "wallet_id": wallet_id,
        "charge_status": charge_status,
        "is_active": is_active,
        "customer_ip_address": customer_ip_address,
        "token": payment_token,
        "currency": currency,
        "gateway": gateway,
        "total_amount": total,
        "captured_amount": captured_amount,
        "return_url": return_url,
        "psp_reference": external_reference or "",
        "store_payment_method": store_payment_method,
        "payment_type": payment_type,
    }
    data = filter_data | {
        "extra_data": extra_data,
        "public_metadata": metadata or {},
    }

    if force_create:
        return await payment_repo.create(
            async_db=async_db, obj_in=data, commit=commit,
        )
    public_metadata = metadata or {}
    # Todo cover payment expressions
    expressions = [
        cast(payment_repo.model.extra_data, JSON) == json.dumps(extra_data),
        cast(payment_repo.model.public_metadata, JSON) == json.dumps(public_metadata),
    ]

    payment = await payment_repo.first(
        async_db, params=filter_data,
    )
    if not payment:
        return await payment_repo.create(
            async_db=async_db,
            obj_in=data,
            commit=commit,
            flush=flush
        )
    return payment


async def get_already_processed_transaction(
        async_db: "AsyncSession",
        payment: "Payment",
        gateway_response: "GatewayResponse"
) -> Optional["Transaction"]:
    transaction = await transaction_repo(
    ).first(async_db, params={
        "is_success": gateway_response.is_success,
        "action_required": gateway_response.action_required,
        "token": gateway_response.transaction_id,
        "kind": gateway_response.kind,
        "amount": gateway_response.amount,
        "currency": gateway_response.currency,
        "payment_id": payment.id,
    })
    return transaction


async def create_transaction(
        async_db: "AsyncSession",
        payment: "Payment",
        kind: "TransactionKindChoices",
        payment_information: "PaymentData",
        commit: bool,
        flush: bool,
        action_required: bool = False,
        gateway_response: GatewayResponse = None,
        error_msg=None,
        is_success=False,
) -> "Transaction":
    """Create a transaction based on transaction kind and gateway response."""
    # Default values for token, amount, currency are only used in cases where
    # response from gateway was invalid or an exception occurred
    if not gateway_response:
        gateway_response = GatewayResponse(
            kind=kind,
            action_required=False,
            transaction_id=payment_information.token or "",
            is_success=is_success,
            amount=payment_information.amount,
            currency=payment_information.currency,
            error=error_msg,
            raw_response={},
        )

    data = {
        'payment_id': payment.id,
        'is_action_required': action_required,
        'kind': gateway_response.kind,
        'token': gateway_response.transaction_id,
        'is_success': gateway_response.is_success,
        'amount': gateway_response.amount,
        'currency': gateway_response.currency,
        'error': str(gateway_response.error),
        'customer_id': gateway_response.customer_id,
        'gateway_response': gateway_response.raw_response or {},
        'action_required_data': gateway_response.action_required_data or {},
    }
    return await transaction_repo.create(async_db, obj_in=data, commit=commit, flush=flush)


async def get_already_processed_transaction_or_create_new_transaction(
        async_db: "AsyncSession",
        payment: "Payment",
        kind: "TransactionKindChoices",
        payment_information: "PaymentData",
        commit: bool,
        flush: bool,
        action_required: bool = False,
        gateway_response: "GatewayResponse" = None,
        error_msg: Optional[str] = None,
) -> "Transaction":
    if gateway_response and gateway_response.transaction_already_processed:
        txn = await get_already_processed_transaction(async_db, payment, gateway_response)
        if txn:
            return txn
    return await create_transaction(
        async_db=async_db,
        payment=payment,
        kind=kind,
        payment_information=payment_information,
        action_required=action_required,
        gateway_response=gateway_response,
        error_msg=error_msg,
        commit=commit, flush=flush
    )


def clean_capture(payment: "Payment", amount: "Decimal"):
    """Check if payment can be captured."""
    if amount <= 0:
        raise PaymentError("Amount should be a positive number.")
    if not payment.can_capture():
        raise PaymentError("This payment cannot be captured.")
    if amount > payment.total_amount or amount > (payment.total_amount - payment.captured_amount):
        raise PaymentError("Unable to charge more than un-captured amount.")


def clean_authorize(payment: "Payment"):
    """Check if payment can be authorized."""
    if not payment.can_authorize():
        raise PaymentError("Charged transactions cannot be authorized again.")


def validate_gateway_response(response: "GatewayResponse"):
    """Validate response to be a correct format for Saleor to process."""
    if not isinstance(response, GatewayResponse):
        raise GatewayError("Gateway needs to return a GatewayResponse obj")
    if response.kind not in ALLOWED_GATEWAY_KINDS:
        raise GatewayError(
            "Gateway response kind must be one of {}".format(
                ALLOWED_GATEWAY_KINDS
            )
        )

    try:
        json.dumps(response.raw_response, )
    except (TypeError, ValueError):
        raise GatewayError("Gateway response needs to be json serializable")


async def update_payment_charge_status(
        async_db: "AsyncSession",
        payment: "Payment",
        transaction,
        commit: bool,
        obj_in: Optional[dict] = None
):
    if obj_in is None:
        obj_in = {}

    transaction_kind = transaction.kind

    if transaction_kind in {
        TransactionKindChoices.CAPTURE,
        TransactionKindChoices.REFUND_REVERSED,
    }:
        obj_in['captured_amount'] = payment.captured_amount + transaction.amount
        obj_in['is_active'] = True

        # Set payment charge status to fully charged
        # only if there is no more amount needs to charge
        obj_in['charge_status'] = ChargeStatusChoices.PARTIALLY_CHARGED
        if payment.get_charge_amount() <= 0:
            obj_in['charge_status'] = ChargeStatusChoices.FULLY_CHARGED

    elif transaction_kind == TransactionKindChoices.VOID:
        obj_in['is_active'] = False

    elif transaction_kind == TransactionKindChoices.REFUND:
        obj_in['captured_amount'] = payment.captured_amount - transaction.amount
        obj_in['charge_status'] = ChargeStatusChoices.PARTIALLY_REFUNDED
        if obj_in['captured_amount'] <= Decimal('0.0'):
            obj_in['captured_amount'] = Decimal('0.0')
            obj_in['charge_status'] = ChargeStatusChoices.FULLY_REFUNDED
            obj_in['is_active'] = False
    elif transaction_kind == TransactionKindChoices.PENDING:
        obj_in['charge_status'] = ChargeStatusChoices.PENDING
    elif transaction_kind == TransactionKindChoices.CANCEL:
        obj_in['charge_status'] = ChargeStatusChoices.CANCELLED
        obj_in['is_active'] = False
    elif transaction_kind == TransactionKindChoices.CAPTURE_FAILED:

        if payment.charge_status in {
            ChargeStatusChoices.PARTIALLY_CHARGED,
            ChargeStatusChoices.FULLY_CHARGED,
        }:
            obj_in['captured_amount'] = payment.captured_amount - transaction.amount
            obj_in['charge_status'] = ChargeStatusChoices.PARTIALLY_CHARGED

            if payment.captured_amount <= 0:
                obj_in['charge_status'] = ChargeStatusChoices.NOT_CHARGED
    if obj_in:
        await payment_repo.update(async_db=async_db, db_obj=payment, obj_in=obj_in, commit=commit)
    await transaction_repo.update(
        async_db=async_db, db_obj=transaction, obj_in={'already_processed': True},
        commit=commit
    )


def price_to_minor_unit(value: "Decimal", currency: Optional[str] = settings.DEFAULT_CURRENCY):
    """Convert decimal value to the smallest unit of currency.

    Take the value, discover the precision of currency and multiply value by
    Decimal('10.0'), then change quantization to remove the comma.
    Decimal(10.0) -> str(1000)
    """
    value = quantize_price(value, currency=currency)
    precision = get_currency_precision(currency)
    number_places = Decimal("10.0") ** precision
    value_without_comma = value * number_places
    return str(value_without_comma.quantize(Decimal("1")))


def price_from_minor_unit(value: str, currency: Optional[str] = settings.DEFAULT_CURRENCY):
    """Convert minor unit (smallest unit of currency) to decimal value.

    (value: 1000, currency: USD) will be converted to 10.00
    """

    value = Decimal(value)
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return value * number_places


async def update_payment(
        async_db: "AsyncSession", payment: "Payment", gateway_response: "GatewayResponse",
        commit: bool
):
    obj_in = {}
    if psp_reference := gateway_response.psp_reference:
        obj_in['psp_reference'] = psp_reference

    if gateway_response.payment_method_info:
        await update_payment_method_details(
            async_db, payment, gateway_response.payment_method_info, commit, obj_in
        )

    if obj_in:
        await payment_repo.update(async_db=async_db, db_obj=payment, obj_in=obj_in, commit=commit)


async def update_payment_method_details(
        async_db: "AsyncSession",
        payment: "Payment",
        payment_method_info: Optional["PaymentMethodInfo"],
        commit: bool,
        obj_in: Optional[dict] = None
):
    if not payment_method_info:
        return
    if not obj_in:
        obj_in = {}
    if payment_method_info.brand:
        obj_in['cc_brand'] = payment_method_info.brand
    if payment_method_info.last_4:
        obj_in['cc_last_digits'] = payment_method_info.last_4
    if payment_method_info.exp_year:
        obj_in['cc_exp_year'] = payment_method_info.exp_year
    if payment_method_info.exp_month:
        obj_in['cc_exp_month'] = payment_method_info.exp_month
    if payment_method_info.type:
        obj_in['payment_method_type'] = payment_method_info.type
    if obj_in:
        await payment_repo.update(async_db=async_db, db_obj=payment, obj_in=obj_in, commit=commit)


async def get_payment_token(async_db: "AsyncSession", payment: "Payment"):
    auth_transaction = await transaction_repo.first(
        async_db=async_db,
        params={"kind": TransactionKindChoices.AUTH, "is_success": True, "payment_id": payment.id}
    )
    if auth_transaction is None:
        raise PaymentError("Cannot process unauthorized transaction")
    return auth_transaction.token


async def gateway_postprocess(async_db: "AsyncSession", payment, transaction):
    if not transaction.is_success or transaction.is_already_processed:
        return

    if transaction.is_action_required:
        await payment_repo.update(async_db=async_db, db_obj=payment, obj_in={'to_confirm': True})
        return

    # to_confirm is defined by the transaction.is_action_required. Payment doesn't
    # require confirmation when we got action_required == False
    obj_in = {}
    if payment.to_confirm:
        obj_in['to_confirm'] = False

    await update_payment_charge_status(async_db=async_db, payment=payment, transaction=transaction, obj_in=obj_in)
