from typing import Optional, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import joinedload

from app.routers.dependency import get_commons, get_async_db, get_active_user, get_staff_user, get_current_user
from app.core.schema import CommonsModel, IPaginationDataBase, IResponseBase
from app.utils.translation import gettext as _
from app.utils.datetime.timezone import now
from app.contrib.account.models import User
from app.contrib.order import OrderStatusChoices

from .repository import order_repo
from .schema import OrderVisible, OrderCreate, OrderBase
from .models import Order

api = APIRouter()


@api.get(
    '/', name='order-list', response_model=IPaginationDataBase[OrderVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_order_list(
        async_db = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "created_at", "-created_at"
        ]] = "-created_at"
) -> dict:
    rows = await order_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        # expressions=expressions
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': rows,
    }


@api.get(
    "/count/", name="order-count",
    response_model=int,
    dependencies=[Depends(get_staff_user)]
)
async def count_orders(
        async_db = Depends(get_async_db)
):
    return await order_repo.count(async_db)


@api.get(
    '/{obj_id}/detail/',
    name='order-detail',
    response_model=OrderVisible,
    dependencies=[Depends(get_staff_user)]
)
async def get_single_order(
        obj_id: UUID,
        async_db = Depends(get_async_db),
):
    options = [joinedload(Order.user).load_only(User.id, User.name)]
    db_obj = await order_repo.get(obj_id=obj_id, async_db=async_db, options=options)
    return db_obj


@api.post(
    '/{obj_id}/update/', name='order-update', response_model=IResponseBase[OrderVisible],
    dependencies=[Depends(get_staff_user)]
)
async def update_order(
        obj_id: UUID,
        obj_in: OrderBase,
        async_db = Depends(get_async_db),
):
    params = {'id': obj_id}
    # if not user.is_superuser:
    #     params["deleted_at"] = None

    db_obj = await order_repo.get_by_params(async_db, params=params)
    result = await order_repo.update(
        async_db, db_obj=db_obj, obj_in=obj_in.model_dump()
    )
    return {
        "message": _("Order status changed"),
        "data": result
    }


@api.delete(
    '/{obj_id}/delete/', name='order-delete',
    response_model=IResponseBase[OrderVisible],
    dependencies=[Depends(get_staff_user)]
)
async def set_order_deleted_at(
        obj_id: UUID,
        async_db = Depends(get_async_db),
):
    order_repo.raw_update(
        async_db, expressions=[Order.id == obj_id], obj_in={"deleted_at": now()}
    )


@api.get('/my/list/', name="order-my-list", response_model=IPaginationDataBase[OrderVisible])
async def get_my_orders_list(
        user=Depends(get_current_user),
        async_db = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "created_at", "-created_at"
        ]] = "-created_at",
        code: Optional[str] = Query(None, max_length=50),
        status: Optional[OrderStatusChoices] = None
):
    q = {"user_id": user.id, "deleted_at": None}
    if status:
        q['status'] = status
    expressions = None
    if code:
        expressions = (Order.code.ilike(f'%{code}%'),)
    obj_list = await order_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        q=q,
        expressions=expressions
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
    }


@api.get('/my/count/', name="order-my-count", response_model=int)
async def get_my_orders_count(
        user=Depends(get_current_user),
        async_db = Depends(get_async_db),
        status: Optional[OrderStatusChoices] = None
):
    params = {"user_id": user.id, "deleted_at": None}
    if status:
        params['status'] = status
    count = await order_repo.count(
        async_db=async_db,
        params=params,
        # expressions=expressions
    )
    return count


@api.post(
    "/my/create/",
    name="order-my-create",
    response_model=IResponseBase[OrderVisible],
    status_code=201,
)
async def create_my_order(
        obj_in: OrderCreate,
        user=Depends(get_active_user),
        async_db = Depends(get_async_db),

):
    data = {
        "user_id": user.id,
        "sender_name": obj_in.sender_name,
        "sender_phone": obj_in.sender_phone,
        "billing_address": obj_in.billing_address,
        "shipping_address": obj_in.shipping_address,
        "receiver_name": obj_in.receiver_name,
        "receiver_phone": obj_in.receiver_phone,
        "price": obj_in.price,
        "weight": obj_in.weight,
        "note": obj_in.note,
        "shipping_type": obj_in.shipping_type
    }
    result = await order_repo.create(
        async_db, obj_in=data
    )
    return {
        "message": _("Order successfully created"),
        "data": result
    }


@api.get(
    '/my/{obj_id}/detail/', name='order-my-detail', response_model=OrderVisible,

)
async def get_my_order_detail(
        obj_id: UUID,
        async_db = Depends(get_async_db),
        user=Depends(get_current_user)

):
    return await order_repo.get_by_params(async_db, params={"id": obj_id, "user_id": user.id, "deleted_at": None})


@api.get(
    '/my/{obj_id}/cancel/', name='order-my-cancel', response_model=IResponseBase[OrderVisible],

)
async def get_my_order_detail(
        obj_id: UUID,
        async_db = Depends(get_async_db),
        user=Depends(get_current_user)
):
    db_obj = await order_repo.get_by_params(async_db, params={"id": obj_id, "user_id": user.id, "deleted_at": None})
    if db_obj.status != OrderStatusChoices.pending:
        raise HTTPException(detail=_("Can't cancel order"), status_code=400)
    result = await order_repo.update(
        async_db, db_obj=db_obj, obj_in={"status": OrderStatusChoices.cancelled}
    )
    return {
        "message": _("Order cancelled"),
        "data": result
    }
