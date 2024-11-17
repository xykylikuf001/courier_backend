from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from fastapi.exceptions import RequestValidationError
from pydantic_core import ErrorDetails

from app.core.schema import IPaginationDataBase, CommonsModel, IResponseBase
from app.routers.dependency import get_commons, get_async_db, get_language, get_active_user

from .schema import PlaceVisible, PlaceCreateWithTranslation
from .models import Place, PlaceTranslation
from .repository import place_repo, place_translation_repo

api = APIRouter()


@api.get(
    '/', name='place-list', response_model=IPaginationDataBase[PlaceVisible],
    # dependencies=[Depends(get_active_user)]

)
async def get_place_list(
        async_db: AsyncSession = Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        lang: Optional[str] = Depends(get_language),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id",
) -> dict:
    options = None
    if lang:
        options = [
            joinedload(Place.current_translation.and_(PlaceTranslation.locale == lang))
        ]

    obj_list = await place_repo.get_all(
        async_db=async_db,
        order_by=(order_by,),
        limit=commons.limit,
        offset=commons.offset,
        options=options,
    )

    return {
        'page': commons.page,
        'limit': commons.limit,
        "rows": obj_list
    }


@api.get(
    '/count/', name='place-count', response_model=int,
    # dependencies=[Depends(get_active_user)]
)
async def count_places(
        async_db=Depends(get_async_db),
):
    return await place_repo.count(async_db)


@api.post(
    '/create/',
    name="place-create",
    response_model=IResponseBase[PlaceVisible],
    status_code=201,
    dependencies=[Depends(get_active_user)]

)
async def create_place(
        obj_in: PlaceCreateWithTranslation,
        async_db=Depends(get_async_db),
):
    if obj_in.parent_id is not None:
        is_exist = await place_repo.exists(async_db=async_db, params={'id': obj_in.parent_id})
        if not is_exist:
            raise RequestValidationError(
                [ErrorDetails(
                    msg='Place does not exist',
                    loc=("body", "parentId",),
                    type='value_error',
                    input=obj_in.parent_id
                )]
            )
    try:
        result = await place_repo.create_with_translation(
            async_db, obj_in=obj_in.model_dump(), lang=obj_in.locale
        )
        return {
            "message": "Place created",
            "data": result
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong!")
