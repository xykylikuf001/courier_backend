from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select, and_, true
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, selectinload, contains_eager

from fastapi.exceptions import RequestValidationError
from pydantic_core import ErrorDetails

from app.core.schema import IPaginationDataBase, CommonsModel, IResponseBase
from app.routers.dependency import get_commons, get_db, get_locale, get_staff_user
from app.utils.translation import gettext as _
from app.db.repository import prepare_data_with_slug, prepare_data_with_slug_sync
from app.conf import LanguagesChoices

from .schema import (
    PlaceVisible, PlaceCreateWithTranslation, PlaceBase, PlaceTranslationVisible,
    PlaceTranslationCreate, PlaceTranslationBase, PlaceVisibleExtended
)
from .models import Place, PlaceTranslation
from .repository import place_repo_sync, place_tr_repo_sync

api = APIRouter()


@api.get(
    '/', name='place-list',
    response_model=IPaginationDataBase[PlaceVisible],
    dependencies=[Depends(get_staff_user)]
)
def get_place_list(
        db: Session = Depends(get_db),
        commons: CommonsModel = Depends(get_commons),
        lang: Optional[LanguagesChoices] = None,
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id",
) -> dict:
    options = None
    if lang:
        options = [
            joinedload(Place.current_translation.and_(PlaceTranslation.locale == lang))
        ]

    rows = place_repo_sync.get_all(
        db=db,
        order_by=(order_by,),
        limit=commons.limit,
        offset=commons.offset,
        options=options,
    )

    return {
        'page': commons.page,
        'limit': commons.limit,
        "rows": rows
    }


@api.get(
    '/count/', name='place-count', response_model=int,
    dependencies=[Depends(get_staff_user)]
)
def count_places(
        db=Depends(get_db),
):
    return place_repo_sync.count(db)


@api.post(
    '/create/',
    name="place-create",
    response_model=IResponseBase[PlaceVisible],
    status_code=201,
    dependencies=[Depends(get_staff_user)]

)
def create_place(
        obj_in: PlaceCreateWithTranslation,
        db=Depends(get_db),
):
    data = {
        "location_level": obj_in.location_level,
        "locale": obj_in.locale,
        "name": obj_in.name,
        "slug": obj_in.slug,
        "full_name": obj_in.full_name,
        "is_active": obj_in.is_active,
        "parent_id": obj_in.parent_id
    }
    if obj_in.parent_id is not None:
        is_exist = place_repo_sync.exists(db=db, params={'id': obj_in.parent_id})
        if not is_exist:
            raise RequestValidationError(
                [ErrorDetails(
                    msg=_('Place does not exist'),
                    loc=("body", "parentId",),
                    type='value_error',
                    input=obj_in.parent_id
                )]
            )
    elif obj_in.full_name is not None:
        data["full_name"] = obj_in.name
    try:
        result = place_repo_sync.create_with_translation(
            db,
            obj_in=obj_in.model_dump(), lang=obj_in.locale
        )
        return {
            "message": "Place created",
            "data": result
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong!")


@api.get(
    '/{obj_id}/detail/', name='place-detail', response_model=PlaceVisibleExtended,
    dependencies=[Depends(get_staff_user)]

)
def get_single_place(
        obj_id: int,
        db=Depends(get_db),
        lang: Optional[LanguagesChoices] = None,
):
    options = [selectinload(Place.translations), ]
    if lang:
        options.append(joinedload(Place.current_translation.and_(PlaceTranslation.locale == lang)))
    return place_repo_sync.get(db, obj_id=obj_id, options=options)


@api.patch(
    '/{obj_id}/update/', name='place-update', response_model=IResponseBase[PlaceVisible],
    dependencies=[Depends(get_staff_user)]

)
async def update_place(
        obj_id: int,
        obj_in: PlaceBase,
        db=Depends(get_db),
):
    db_obj = place_repo_sync.get(db, obj_id=obj_id)
    if obj_in.parent_id is not None and db_obj.parent_id != obj_in.parent_id:
        is_exist = place_repo_sync.exists(db=db, params={'id': obj_in.parent_id})
        if not is_exist:
            raise RequestValidationError(
                [ErrorDetails(
                    msg=_('Place does not exist'),
                    loc=("body", "parentId",),
                    type='value_error',
                    input=obj_in.parent_id
                )]
            )
    data = obj_in.model_dump(exclude_unset=True)
    if obj_in.slug is not None and obj_in.slug != db_obj.slug:
        data = prepare_data_with_slug_sync(
            db=db,
            obj_in=data,
            obj_repo_sync=place_repo_sync,
            db_obj=db_obj
        )
    print(data)
    db_obj.parent_id = obj_in.parent_id
    result = place_repo_sync.update(
        db, db_obj=db_obj, obj_in=data
    )

    return {
        "message": _("PLace updated"),
        "data": result
    }


@api.get(
    "/{obj_id}/translations/",
    name="place-translations", response_model=IPaginationDataBase[PlaceTranslationVisible],
    dependencies=[Depends(get_staff_user)]
)
def retrieve_place_translations(
        obj_id: int,
        db=Depends(get_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "locale", "-locale"
        ]] = "locale",
):
    obj_list = place_tr_repo_sync.get_all(
        db=db,
        order_by=(order_by,),
        limit=commons.limit,
        offset=commons.offset,
        q={'id': obj_id}
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        "rows": obj_list
    }


@api.post(
    "/{obj_id}/translations/create/", name="place-tr-create",
    response_model=IResponseBase[PlaceTranslationVisible],
    status_code=201,
    dependencies=[Depends(get_staff_user)]
)
def create_place_translation(

        obj_id: int,
        obj_in: PlaceTranslationCreate,
        db=Depends(get_db),
):
    place_exists = place_repo_sync.exists(db, params={"id": obj_id})

    if not place_exists:
        raise HTTPException(detail="Invalid place id", status_code=400)
    is_exists = place_tr_repo_sync.exists(db, params={'locale': obj_in.locale, "id": obj_id})
    if is_exists:
        raise RequestValidationError(
            [ErrorDetails(
                msg=f"Translation with this locale {obj_in.locale} already exists",
                loc=("body", "locale",),
                type='value_error',
                input=obj_in.locale
            )]
        )

    result = place_tr_repo_sync.create(db, obj_in={
        "id": obj_id,
        "name": obj_in.name,
        "full_name": obj_in.full_name,
        "locale": obj_in.locale,
    })
    return {
        "message": f"Place translation created: {obj_in.locale}",
        "data": result
    }


@api.get(
    '/{obj_id}/translations/{obj_locale}/detail/', name="place-tr-detail",
    response_model=PlaceTranslationVisible,
    dependencies=[Depends(get_staff_user)]
)
def retrieve_place_translation(
        obj_id: int,
        obj_locale: str,
        db=Depends(get_db),
):
    return place_tr_repo_sync.get_by_params(db, params={'id': obj_id, "locale": obj_locale})


@api.patch(
    '/{obj_id}/translations/{obj_locale}/update/',
    name='place-tr-update',
    response_model=IResponseBase[PlaceTranslationVisible],
    dependencies=[Depends(get_staff_user)]

)
def update_place_translation(
        obj_id: int,
        obj_locale: str,
        obj_in: PlaceTranslationBase,
        db=Depends(get_db),
) -> dict:
    db_obj = place_tr_repo_sync.get_by_params(db, params={'id': obj_id, "locale": obj_locale})
    result = place_tr_repo_sync.update(
        db, db_obj=db_obj, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    return {
        "message": "Place translation updated: %(locale)s" % {"locale": obj_locale},
        "data": result
    }


@api.delete(
    '/{obj_id}/translations/{locale}/delete/',
    name='place-tr-delete',
    status_code=204,
    dependencies=[Depends(get_staff_user)]

)
def delete_place_translation(
        obj_id: int,
        locale: str,
        db=Depends(get_db),
):
    place_tr_repo_sync.remove(
        db,
        expressions=(PlaceTranslation.id == obj_id, PlaceTranslation.locale == locale,)
    )


@api.get(
    '/public/list/', name='place-public-list', response_model=IPaginationDataBase[PlaceVisible],
)
def place_public_list(
        search: Optional[str] = Query(None, max_length=255),
        parent_id: Optional[int] = None,
        db=Depends(get_db),
        locale: Optional[str] = Depends(get_locale),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id",
):
    expressions = [
        Place.parent_id == parent_id,
        Place.is_active == true(),
    ]
    if search:
        expressions.append(PlaceTranslation.name.ilike(f'%{search}%'))
    stmt = select(Place).join(PlaceTranslation, and_(
        Place.id == PlaceTranslation.id,
        PlaceTranslation.locale == locale
    )).options(
        contains_eager(Place.current_translation)
    ).filter(
        *expressions,
    )
    rows = place_repo_sync.get_all(
        db=db,
        stmt=stmt,
        offset=commons.offset,
        limit=commons.limit,
        order_by=(order_by,),
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": rows
    }


@api.get(
    '/public/count/', name='place-public-count', response_model=int,
)
async def count_places(
        db=Depends(get_db),
        search: Optional[str] = Query(None, max_length=255),
        parent_id: Optional[int] = None,
):
    params = {'parent_id': parent_id, "is_active": True}
    expressions = None
    if search is not None:
        expressions = (PlaceTranslation.name.ilike(f'%{search}%'),)
    return place_repo_sync.count(db, params=params, expressions=expressions)


@api.get(
    '/public/{slug_in}/detail/',
    name='place-public-detail',
    response_model=PlaceVisible,
)
def get_single_place(
        slug_in: str,
        db=Depends(get_db),
        locale: Optional[str] = Depends(get_locale),
):
    stmt = select(Place).join(
        PlaceTranslation,
        and_(
            Place.id == PlaceTranslation.id,
            PlaceTranslation.locale == locale
        )
    ).options(
        contains_eager(Place.current_translation)
    ).filter(
        Place.slug == slug_in,
        Place.is_active == true(),
    )
    return place_repo_sync.get_by_params(db, stmt=stmt)
