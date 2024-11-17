from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_

from app.routers.dependency import get_commons, get_async_db, get_active_user
from app.core.schema import CommonsModel, IPaginationDataBase, IResponseBase
from app.contrib.account.models import User
from app.utils.translation import gettext as _

from .schema import MessageVisible, MessageCreate
from .repository import message_repo

api = APIRouter()


@api.get(
    '/', name='message-list', response_model=IPaginationDataBase[MessageVisible],
    dependencies=[Depends(get_active_user)]
)
async def get_message_list(
        async_db: AsyncSession = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        search: Optional[str] = Query(None),
        is_read: Optional[bool] = Query(None),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
) -> dict:
    expressions = []
    model = message_repo.model
    if search:
        expressions.append(or_(
            model.full_name.ilike(f"%{search}%"),
            model.email.ilike(f"%{search}%"),
            model.subject.ilike(f"%{search}%"),
            model.phone.ilike(f"%{search}%"),
        ))
    if is_read is not None:
        expressions.append(model.is_read.is_(is_read))
    obj_list = await message_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        expressions=expressions
    )
    count = await message_repo.count(async_db, expressions=expressions)
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
        'count': count,
    }


@api.get('/{obj_id}/detail/', name='message-detail', response_model=MessageVisible)
async def get_single_message(
        obj_id: int,
        user: User = Depends(get_active_user),
        async_db: AsyncSession = Depends(get_async_db),
):
    db_obj = await message_repo.get(obj_id=obj_id, async_db=async_db)
    if db_obj.is_read is False:
        result = await message_repo.update(
            async_db=async_db,
            db_obj=db_obj,
            obj_in={"is_read": True}
        )
        return result
    return db_obj


@api.post('/contact-us/', name='message-contact-us', response_model=IResponseBase[MessageVisible])
async def message_contact_us(
        obj_in: MessageCreate,
        async_db: AsyncSession = Depends(get_async_db),
):
    result = await message_repo.create(async_db, obj_in=obj_in)
    return {
        "message": _("Thanks for messaging with us!!!"),
        "data": result
    }