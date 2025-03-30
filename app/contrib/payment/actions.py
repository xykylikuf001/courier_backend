from typing import TYPE_CHECKING, Optional
from uuid import UUID

from app.contrib.payment import (
    CustomPaymentChoices, ChargeStatusChoices, TransactionKindChoices,
    PaymentTypeChoices
)
from .repository import transaction_repo
from .utils import create_payment

if TYPE_CHECKING:
    from decimal import Decimal
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.contrib.account.models import User
    from app.contrib.wallet.models import Wallet


# def mark_order_as_paid_with_transaction(
#     order: "Order",
#     request_user: User,
#     app: Optional["App"],
#     manager: "PluginsManager",
#     external_reference: Optional[str] = None,
# ):
#     """Mark order as paid.
#
#     Allows to create a transaction for an order.
#     """
#     with transaction.atomic():
#         create_transaction_for_order(
#             order=order,
#             user=request_user,
#             app=app,
#             psp_reference=external_reference,
#             charged_value=order.total.gross.amount,
#             available_actions=[TransactionAction.REFUND],
#             name=MARK_AS_PAID_TRANSACTION_NAME,
#         )
#         updates_amounts_for_order(order)
#         events.order_manually_marked_as_paid_event(
#             order=order,
#             user=request_user,
#             app=app,
#             transaction_reference=external_reference,
#         )
#         call_event(manager.order_fully_paid, order)
#         call_event(manager.order_updated, order)


async def create_manual_payment_deposit(
        async_db: "AsyncSession",
        staff_id: UUID,
        user_id: UUID,
        wallet_id: UUID,
        currency: str,
        amount: "Decimal",
        commit: bool,
        flush: bool,
        external_reference: Optional[str] = None,
):
    """Mark order as paid.

    Allows to create a payment deposit without actually performing any
    payment by the gateway.
    """
    # transaction ensures that webhooks are triggered when payments and transactions are
    # properly created
    payment = await create_payment(
        async_db=async_db,
        gateway=CustomPaymentChoices.MANUAL.value,
        payment_token="",
        currency=currency,
        total=amount,
        captured_amount=amount,
        payment_type=PaymentTypeChoices.deposit,
        external_reference=external_reference,
        wallet_id=wallet_id,
        staff_id=staff_id,
        user_id=user_id,
        charge_status=ChargeStatusChoices.FULLY_CHARGED,
        is_active=True,
        commit=commit,
        flush=flush,
    )

    transaction_data = {
        "payment_id": payment.id,
        "is_action_required": False,
        "kind": TransactionKindChoices.EXTERNAL,
        "token": external_reference or "",
        "is_success": True,
        "amount": amount,
        "currency": currency,
        "gateway_response": {}
    }

    transaction = await transaction_repo.create(
        async_db, obj_in=transaction_data, commit=commit,
        flush=flush
    )
    return payment, transaction
