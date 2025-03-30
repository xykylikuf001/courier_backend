from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.exceptions import RequestValidationError

from pydantic import condecimal
from pydantic_core import ErrorDetails
from sqlalchemy.orm import joinedload, selectinload

from app.contrib.account.models import User
from app.core.schema import IResponseBase, IPaginationDataBase, CommonsModel
from app.routers.dependency import get_async_db, get_staff_user, get_commons, get_current_user, get_active_user
from app.contrib.wallet.repository import wallet_repo
from app.contrib.account.repository import user_repo
from app.contrib.file.repository import file_repo
from app.utils.file import delete_file

from .exceptions import PaymentError
from .schema import (
    PaymentVisible,
    TransactionVisible, PaymentDeposit,
)
from .repository import payment_repo, transaction_repo, payment_attachment_repo
from .actions import create_manual_payment_deposit
from .gateway import refund
from .models import PaymentAttachment
from ..plugins.manager import get_plugins_manager

api = APIRouter()


@api.get(
    '/', name='payment-list', response_model=IPaginationDataBase[PaymentVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_payment_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons)
):
    options = [
        joinedload(payment_repo.model.staff).load_only(User.id, User.username),

        selectinload(payment_repo.model.transactions),
    ]

    rows = await payment_repo.get_all(
        async_db,
        offset=commons.offset, limit=commons.limit,
        options=options,
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": rows
    }


@api.get(
    '/my/', name='user-payment-list', response_model=IPaginationDataBase[PaymentVisible],

)
async def get_user_payment_list(
        user=Depends(get_current_user),
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons)
):
    options = [
        selectinload(payment_repo.model.transactions),
    ]

    rows = await payment_repo.get_all(
        async_db,
        offset=commons.offset, limit=commons.limit,
        options=options,
        q={"user_id": user.id}
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": rows
    }


@api.get('/my/{obj_id}/detail/', name="user-payment-detail", response_model=PaymentVisible)
async def get_single_user_payment(
        obj_id: UUID,
        user=Depends(get_current_user),
        async_db=Depends(get_async_db),
):
    options = [
        selectinload(payment_repo.model.transactions),
    ]
    return await payment_repo.get_by_params(async_db, params={"user_id": user.id, "id": obj_id}, options=options)


# @api.post('/deposit/', name="payment-deposit", response_model=IResponseBase[PaymentVisible])
# async def payment_deposit(
#         obj_in: PaymentDeposit,
#         user=Depends(get_active_user),
#         async_db=Depends(get_async_db),
# ):
#     manager = get_plugins_manager()
#     return {
#         "message": "Payment successfully deposited.",
#         "data": payment
#     }


@api.post(
    '/deposit/manual/',
    name='payment-deposit-manual',
    response_model=IResponseBase[PaymentVisible],
)
async def payment_deposit_manual(
        receiver_user_id: UUID = Form(..., alias="receiver_user_id"),
        amount: condecimal(max_digits=12, decimal_places=2) = Form(..., gt=0),
        upload_file: Optional[UploadFile] = File(None),
        user=Depends(get_staff_user),
        async_db=Depends(get_async_db),
):
    options = [joinedload(user_repo.model.wallet)]
    customer_user = await user_repo.first(
        async_db, params={"id": receiver_user_id},
        options=options,
    )
    file_path = None
    if not customer_user:
        raise RequestValidationError(
            [ErrorDetails(
                msg='User does not exist',
                loc=("body", "userId",),
                type='value_error',
                input=receiver_user_id
            )]
        )
    elif customer_user.is_active is False:
        raise RequestValidationError(
            [ErrorDetails(
                msg='User disabled',
                loc=("body", "userId",),
                type='value_error',
                input=receiver_user_id
            )]
        )
    wallet = customer_user.wallet
    if not wallet:
        wallet = await wallet_repo.get_or_create(
            async_db,
            user_id=receiver_user_id,
        )
    try:
        payment, trn = await create_manual_payment_deposit(
            async_db,
            user_id=receiver_user_id,
            staff_id=user.id,
            wallet_id=wallet.id,
            currency=wallet.currency,
            amount=amount,
            commit=False,
            flush=True,
        )

        await wallet_repo.update(
            async_db,
            db_obj=wallet,
            obj_in={
                "amount": wallet.amount + amount,
            },
            commit=True,
        )
        if upload_file:
            attachment_file = await file_repo.create_with_file(
                async_db, upload_file=upload_file,
                obj_in={
                    "content_type": "payment"
                },
                commit=False, flush=True
            )
            file_path = attachment_file.file_path
            await payment_attachment_repo.create(
                async_db=async_db,
                obj_in={
                    "payment_id": payment.id,
                    "file_id": attachment_file.id
                },
                commit=True,
            )
    except Exception as e:
        print(e)
        await async_db.rollback()
        if file_path:
            delete_file(file_path)
        raise HTTPException(status_code=500, detail="Something went wrong!")
    return {
        "message": "Payment successfully deposited.",
        "data": payment
    }


@api.post(
    "/{obj_id}/append-attachment/", name="payment-append-attachment", response_model=IResponseBase[PaymentVisible],
    dependencies=[Depends(get_staff_user)]
)
async def append_attachment_to_payment(
        obj_id: UUID,
        upload_file: Optional[UploadFile] = File(...),
        async_db=Depends(get_async_db),
):
    db_obj = await payment_repo.get(async_db, obj_id=obj_id)
    file_path = None
    try:
        attachment_file = await file_repo.create_with_file(
            async_db, upload_file=upload_file,
            obj_in={
                "content_type": "payment"
            },
            commit=False,
            flush=True,
        )
        file_path = attachment_file.file_path
        await payment_attachment_repo.create(
            async_db=async_db,
            obj_in={
                "payment_id": db_obj.id,
                "file_id": attachment_file.id
            },
            commit=True,
        )
    except Exception as e:
        print(e)
        await async_db.rollback()
        if file_path:
            delete_file(file_path)
        raise HTTPException(status_code=500, detail="Something went wrong!")

    return {
        "message": "Attachment successfully append to payment",
        "data": db_obj
    }


@api.get(
    "/{obj_id}/detail/",
    name="payment-detail",
    response_model=PaymentVisible,
    dependencies=[Depends(get_staff_user)]
)
async def retrieve_single_payment(
        obj_id: UUID,
        async_db=Depends(get_async_db),

):
    options = [
        joinedload(payment_repo.model.staff).load_only(User.id, User.username),
        selectinload(payment_repo.model.transactions),
        selectinload(payment_repo.model.attachments).options(joinedload(PaymentAttachment.file)),
    ]
    db_obj = await payment_repo.get(async_db, obj_id=obj_id, options=options)
    return db_obj


@api.get(
    '/{obj_id}/refund/', name='payment-refund', response_model=IResponseBase[PaymentVisible],
    dependencies=[Depends(get_staff_user)]
)
async def refund_payment(
        obj_id: UUID,
        async_db=Depends(get_async_db),
):
    db_obj = await payment_repo.get(async_db, obj_id=obj_id)
    wallet = await wallet_repo.get(async_db, obj_id=db_obj.wallet_id)
    captured_amount = db_obj.captured_amount
    try:

        _, payment, txn = await refund(
            async_db=async_db, payment=db_obj, amount=db_obj.total_amount, commit=False
        )
        await wallet_repo.update(
            async_db,
            db_obj=wallet,
            obj_in={
                "amount": wallet.amount - captured_amount,
            },
            commit=True,
        )
    except PaymentError as e:
        await async_db.rollback()

        raise HTTPException(status_code=400, detail=e.message)
    return {
        "message": "Payment refunded",
        "data": payment
    }


@api.get(
    '/transaction/', name='transaction-list', response_model=IPaginationDataBase[TransactionVisible],
    dependencies=[Depends(get_staff_user)]

)
async def get_transaction_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons)
):
    rows = await transaction_repo.get_all(
        async_db,
        offset=commons.offset, limit=commons.limit,
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": rows
    }


@api.get(
    "/transaction/{obj_id}/detail/", name="transaction-detail", response_model=TransactionVisible,
    dependencies=[Depends(get_staff_user)]
)
async def retrieve_single_transaction(
        obj_id: int,
        async_db=Depends(get_async_db),
):
    return await transaction_repo.get(async_db, obj_id=obj_id)


@api.get('/method/list/', name='payment-method-list', response_model=List, tags=["payment-method"])
async def payment_method_list(

        async_db=Depends(get_async_db),
):
    manager = get_plugins_manager()
    result = await manager.list_payment_gateways(async_db=async_db)
    return result
