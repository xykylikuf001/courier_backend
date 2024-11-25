from typing import Optional, Literal
from uuid import UUID
from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.dependency import get_commons, get_async_db, get_active_user, get_staff_user, get_current_user
from app.core.schema import CommonsModel, IPaginationDataBase, IResponseBase
from app.utils.translation import gettext as _
from .repository import order_repo
from .schema import OrderVisible, OrderCreate

api = APIRouter()


@api.get(
    '/', name='order-list', response_model=IPaginationDataBase[OrderVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_order_list(
        async_db: AsyncSession = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
) -> dict:
    obj_list = await order_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        # expressions=expressions
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
    }


@api.get(
    "/count/", name="order-count",
    response_model=int,
    dependencies=[Depends(get_staff_user)]
)
async def count_orders(
        async_db: AsyncSession = Depends(get_async_db)
):
    return await order_repo.count(async_db)


@api.get(
    '/{obj_id}/detail/',
    name='order-detail',
    response_model=OrderVisible,
    dependencies=[Depends(get_staff_user)]
)
async def get_single_order(
        obj_id: int,
        async_db: AsyncSession = Depends(get_async_db),
):
    db_obj = await order_repo.get(obj_id=obj_id, async_db=async_db)
    return db_obj


@api.get('/my/list/', name="order-my-list", response_model=IPaginationDataBase[OrderVisible])
async def get_my_orders_list(
        user=Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
):
    obj_list = await order_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        q={"user_id": user.id},
        # expressions=expressions
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
    }


@api.get('/my/count/', name="order-my-count", response_model=int)
async def get_my_orders_count(
        user=Depends(get_current_user),
        async_db: AsyncSession = Depends(get_async_db),
):
    count = await order_repo.count(
        async_db=async_db,
        q={"user_id": user.id},
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
        async_db: AsyncSession = Depends(get_async_db),

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
    dependencies=[Depends(get_current_user)]
)
async def get_my_order_detail(
        obj_id: UUID,
        async_db: AsyncSession = Depends(get_async_db),

):
    return await order_repo.get(async_db, obj_id=obj_id)
