import logging
from typing import Callable, TYPE_CHECKING, Optional, Tuple
from decimal import Decimal

from app.contrib.payment import TransactionKindChoices
from app.contrib.payment.exceptions import PaymentError, GatewayError
from app.utils.translation import gettext as _

from .repository import transaction_repo, payment_repo
from .interface import CustomerSource, PaymentGateway
from .utils import (
    clean_authorize,
    create_payment_information,
    validate_gateway_response,
    update_payment,
    get_already_processed_transaction_or_create_new_transaction,
    gateway_postprocess,
    clean_capture,
    create_transaction,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.contrib.plugins.manager import PluginsManager

    from .models import Payment, Transaction

logger = logging.getLogger(__name__)
ERROR_MSG = _('Oops! Something went wrong.')
GENERIC_TRANSACTION_ERROR = _("Transaction was unsuccessful.")


def raise_payment_error(fn: Callable) -> Callable:
    async def wrapped(*args, **kwargs):
        async_db, payment, txn = await fn(*args, **kwargs)
        if not txn.is_success:
            raise PaymentError(txn.error or GENERIC_TRANSACTION_ERROR)
        return async_db, payment, txn

    return wrapped


def require_active_payment(fn: Callable) -> Callable:
    async def wrapped(payment: "Payment", *args, **kwargs):
        if not payment.is_active:
            raise PaymentError('This payment is no longer active.')
        return await fn(payment=payment, *args, **kwargs)

    return wrapped


def with_locked_payment(fn: Callable) -> Callable:
    """Lock payment to protect from asynchronous modification."""

    async def wrapped(async_db: "AsyncSession", payment: "Payment", *args, **kwargs):
        # payment = Payment.objects.select_for_update().get(id=payment.id)
        locked_payment = await payment_repo.get(async_db, obj_id=payment.id, with_for_update=True)
        return fn(async_db=async_db, payment=locked_payment, *args, **kwargs)

    return wrapped


def payment_postprocess(fn: Callable) -> Callable:
    async def wrapped(async_db, payment, *args, **kwargs):
        db, result_payment, txn = await fn(*args, **kwargs)
        await gateway_postprocess(db, payment, txn)
        return db, payment, txn

    return wrapped


@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
async def process_payment(
        async_db: "AsyncSession",
        payment: "Payment",
        token: str,
        manager: "PluginsManager",
        commit: bool,
        flush: bool,
        customer_id: Optional[str] = None,
        additional_data: Optional[dict] = None,
) -> Tuple["AsyncSession", "Payment", "Transaction"]:
    payment_data = create_payment_information(
        payment=payment,
        payment_token=token,
        customer_id=customer_id,
        additional_data=additional_data,
    )

    response, error = _fetch_gateway_response(
        manager.process_payment,
        payment.gateway,
        payment_data,
    )
    action_required = response is not None and response.action_required
    if response:
        await update_payment(async_db, payment, response, commit=commit)
    txn = await get_already_processed_transaction_or_create_new_transaction(
        async_db=async_db,
        payment=payment,
        kind=TransactionKindChoices.CAPTURE,
        action_required=action_required,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
        commit=commit, flush=flush
    )
    return async_db, payment, txn


@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
async def authorize(
        async_db: "AsyncSession",
        payment: "Payment",
        token: str,
        manager: "PluginsManager",
        commit: bool,
        flush: bool,
        customer_id: Optional[str] = None,
) -> Tuple["AsyncSession", "Payment", "Transaction"]:
    clean_authorize(payment)
    payment_data = create_payment_information(
        payment=payment,
        payment_token=token,
        customer_id=customer_id
    )
    response, error = _fetch_gateway_response(
        manager.authorize_payment,
        payment.gateway,
        payment_data,
    )
    if response:
        await update_payment(async_db, payment, response)
    trn = await get_already_processed_transaction_or_create_new_transaction(
        async_db=async_db,
        payment=payment,
        kind=TransactionKindChoices.AUTH,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
        commit=commit, flush=flush
    )
    return async_db, payment, trn


# @payment_postprocess
# @raise_payment_error
# @require_active_payment
# @with_locked_payment
# @payment_postprocess
# async def check_payment_status(
#         async_db: "AsyncSession",
#         payment: "Payment",
#         manager: "PluginsManager",
#         amount: "Decimal" = None,
#         customer_id: str = None,
#         additional_data: Optional[dict] = None,
# ) -> Tuple["AsyncSession", "Transaction"]:
#     if amount is None:
#         amount = payment.get_charge_amount()
#     clean_capture(payment, Decimal(amount))
#     token = await _get_past_transaction_token(async_db, payment, TransactionKindChoices.AUTH)
#     payment_data = create_payment_information(
#         payment=payment,
#         payment_token=token,
#         amount=amount,
#         customer_id=customer_id,
#         additional_data=additional_data,
#     )
#     response, error = _fetch_gateway_response(
#         manager.check_payment_status,
#         payment_data,
#     )
#     if response:
#         await update_payment(async_db, payment, response)
#     trn = await get_already_processed_transaction_or_create_new_transaction(
#         async_db,
#         payment=payment,
#         kind=TransactionKindChoices.CHECK_STATUS,
#         payment_information=payment_data,
#         error_msg=error,
#         gateway_response=response,
#     )
#     return async_db, trn


# @payment_postprocess
@payment_postprocess
@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
async def capture(
        async_db: "AsyncSession",
        payment: "Payment",
        manager: "PluginsManager",
        commit: bool,
        flush: bool,
        amount: "Decimal" = None,
        customer_id: str = None,
) -> Tuple["AsyncSession", "Payment", "Transaction"]:
    if amount is None:
        amount = payment.get_charge_amount()
    clean_capture(payment, Decimal(amount))
    token = await _get_past_transaction_token(async_db, payment, TransactionKindChoices.AUTH)
    payment_data = create_payment_information(
        payment=payment,
        payment_token=token,
        amount=amount,
        customer_id=customer_id,
    )
    response, error = _fetch_gateway_response(
        manager.capture_payment,

        payment.gateway,
        payment_data,
    )
    if response:
        await update_payment(async_db, payment, response, commit)
    trn = await get_already_processed_transaction_or_create_new_transaction(
        async_db=async_db,
        payment=payment,
        kind=TransactionKindChoices.CAPTURE,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
        commit=commit, flush=flush
    )
    return async_db, payment, trn


@raise_payment_error
@with_locked_payment
@payment_postprocess
async def refund(
        async_db: "AsyncSession",
        payment: "Payment",
        manager: "PluginsManager",

        commit: bool,
        flush: bool,
        amount: "Decimal" = None,
) -> Tuple["AsyncSession", "Payment", "Transaction"]:
    if amount is None:
        amount = payment.captured_amount
    _validate_refund_amount(payment, amount)
    if not payment.can_refund():
        raise PaymentError("This payment cannot be refunded.")

    kind = TransactionKindChoices.EXTERNAL if payment.is_manual() else TransactionKindChoices.CAPTURE

    token = await _get_past_transaction_token(async_db, payment, kind)
    payment_data = create_payment_information(
        payment=payment, payment_token=token, amount=amount,
    )
    if payment.is_manual():
        # for manual payment we just need to mark payment as a refunded
        txn = await create_transaction(
            async_db,
            payment,
            TransactionKindChoices.REFUND,
            payment_information=payment_data,
            is_success=True,
            commit=commit, flush=flush
        )
        return async_db, payment, txn
    response, error = _fetch_gateway_response(
        manager.refund_payment, payment.gateway, payment_data,
    )
    txn = await get_already_processed_transaction_or_create_new_transaction(
        async_db=async_db,
        payment=payment,
        kind=TransactionKindChoices.REFUND,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
        commit=commit, flush=flush
    )
    return async_db, payment, txn


@raise_payment_error
@with_locked_payment
@payment_postprocess
async def void(
        async_db: "AsyncSession",
        payment: "Payment",
        manager: "PluginsManager",

        commit: bool,
        flush: bool,
) -> Tuple["AsyncSession", "Payment", "Transaction"]:
    token = await _get_past_transaction_token(async_db, payment, TransactionKindChoices.AUTH)
    payment_data = create_payment_information(payment=payment, payment_token=token)
    response, error = _fetch_gateway_response(
        manager.void_payment, payment.gateway, payment_data,
    )
    txn = await get_already_processed_transaction_or_create_new_transaction(
        async_db=async_db,
        payment=payment,
        kind=TransactionKindChoices.VOID,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
        commit=commit, flush=flush
    )
    return async_db, payment, txn


@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
async def confirm(
        async_db: "AsyncSession",
        payment: "Payment",
        manager: "PluginsManager",

        commit: bool,
        flush: bool,
        additional_data: Optional[dict] = None
) -> Tuple["AsyncSession", "Payment", "Transaction"]:
    txn = await transaction_repo.first(
        async_db,
        order_by=[transaction_repo.model.id.desc()],
        params={"payment_id": payment.id, "kind": TransactionKindChoices.ACTION_TO_CONFIRM, "is_success": True}
    )

    token = txn.token if txn else ""
    payment_data = create_payment_information(
        payment=payment, payment_token=token, additional_data=additional_data
    )
    response, error = _fetch_gateway_response(
        manager.confirm_payment,
        payment.gateway,
        payment_data,
    )
    action_required = response is not None and response.action_required
    if response:
        await update_payment(async_db, payment, response, commit=commit)
    txn = await get_already_processed_transaction_or_create_new_transaction(
        async_db,
        payment=payment,
        kind=TransactionKindChoices.CONFIRM,
        payment_information=payment_data,
        action_required=action_required,
        error_msg=error,
        gateway_response=response,
        commit=commit, flush=flush
    )
    return async_db, payment, txn


def list_payment_sources(
        gateway: str,
        customer_id: str,
        manager: "PluginsManager",
) -> list["CustomerSource"]:
    return manager.list_payment_sources(gateway, customer_id)


def list_gateways(manager: "PluginsManager") -> list["PaymentGateway"]:
    return manager.list_payment_gateways()


def _fetch_gateway_response(fn, *args, **kwargs):
    response, error = None, None
    try:
        response = fn(*args, **kwargs)
        validate_gateway_response(response)
    except GatewayError:
        logger.exception(_("Gateway response validation failed!"))
        response = None
        error = 'Gateway response validation failed!'
    except PaymentError:
        logger.exception(_('Error encountered while executing payment gateway.'))
        error = 'Error encountered while executing payment gateway.'
        response = None
    return response, error


async def _get_past_transaction_token(
        async_db: "AsyncSession", payment: "Payment", kind: "TransactionKindChoices"
) -> Optional[str]:
    txn = await transaction_repo.first(
        async_db,
        order_by=[transaction_repo.model.id.asc()],
        params={
            "payment_id": payment.id,
            "kind": kind,
            "is_success": True,
        }
    )
    if txn is None:
        raise PaymentError(f"Cannot find successful %(kind)s transaction." % {'kind': kind})
    return txn.token


def _validate_refund_amount(payment: "Payment", amount: "Decimal"):
    if amount <= 0:
        raise PaymentError(_("Amount should be a positive number."))
    if amount > payment.captured_amount:
        raise PaymentError(_("Cannot refund more than captured."))
