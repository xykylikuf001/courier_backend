from typing import Optional, Literal
from fastapi import APIRouter, Depends, UploadFile, File, Form

from sqlalchemy.orm import joinedload, selectinload

from app.routers.dependency import get_commons, get_async_db, get_staff_user, get_locale
from app.core.schema import CommonsModel, IPaginationDataBase, IResponseBase
from app.utils.translation import gettext as _
from app.conf import LanguagesChoices
from app.contrib.file.repository import file_repo
from app.contrib.file import ContentTypeChoices

from .schema import (
    SliderVisible, SliderBase, SliderCreateWithTranslation, SliderVisibleExtended,
)
from .repository import slider_repo
from .models import Slider, SliderTranslation

api = APIRouter()


@api.get(
    '/', name='slider-list', response_model=IPaginationDataBase[SliderVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_slider_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        lang: Optional[LanguagesChoices] = None,
        order_by: Optional[Literal[
            "created_at", "-created_at"
        ]] = "-created_at"
) -> dict:
    options = [joinedload(Slider.file)]
    if lang:
        options.append(joinedload(Slider.current_translation.and_(SliderTranslation.locale == lang)))
    rows = await slider_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        options=options
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': rows,
    }


@api.post(
    '/create/', name='slider-create', response_model=IResponseBase[SliderVisible],
    dependencies=Depends(get_staff_user), status_code=201
)
async def create_slider(
        obj_in: SliderCreateWithTranslation,
        async_db=Depends(get_async_db),
):
    result = await slider_repo.create_with_translation(
        async_db, obj_in=obj_in.model_dump(), lang=obj_in.locale
    )

    return {
        "message": _("Slider successfully created"),
        "data": result
    }


@api.post(
    '/create/upload/', name='slider-upload', response_model=IResponseBase[SliderVisible],
    status_code=201,
    dependencies=[Depends(get_staff_user)]
)
async def create_slider_with_file(
        upload_file: UploadFile = File(...),
        host: Optional[str] = Form(None, max_length=255),
        path: Optional[str] = Form(None, max_length=255),
        is_active: bool = Form(...),
        sort_order: Optional[int] = Form(None),
        title: str = Form(..., max_length=255),
        caption: str = Form(..., max_length=255),
        locale: LanguagesChoices = Form(...),
        async_db=Depends(get_async_db),

):
    db_file = await file_repo.create_with_file(
        async_db,
        upload_file=upload_file,
        obj_in={"content_type": ContentTypeChoices.slider}
    )
    data = {
        "host": host,
        "path": path,
        "is_active": is_active,
        "sort_order": sort_order,
        "title": title,
        "caption": caption,
        "file_id": db_file.id
    }
    result = await slider_repo.create_with_translation(
        async_db, obj_in=data, lang=locale
    )
    return {
        "message": _("Slider created"),
        "data": result
    }


@api.post(
    "/{obj_id}/file/manage/",
    response_model=IResponseBase[SliderVisible],
    name='slider-file-manage',
    dependencies=[Depends(get_staff_user)]
)
async def manage_slider_media(
        obj_id: int,
        upload_file: UploadFile,
        async_db=Depends(get_async_db),
):
    db_obj = await slider_repo.get(async_db, obj_id=obj_id)
    if db_obj.media_id:
        db_file = await file_repo.first(async_db, params={"id": db_obj.media_id})
        if db_file:
            await file_repo.delete_with_file(async_db, db_obj=db_file)
    db_file = await file_repo.create_with_file(
        async_db,
        upload_file=upload_file,
        obj_in={
            "content_type": ContentTypeChoices.slider,
        }
    )
    result = await slider_repo.update(async_db, db_obj=db_obj, obj_in={"file_id": db_file.id})
    return {
        "message": _("Slider file update"),
        "data": result
    }


@api.get(
    '/{obj_id}/detail/', name='slider-detail', response_model=SliderVisibleExtended,
    dependencies=[Depends(get_staff_user)]
)
async def retrieve_single_slider(
        obj_id: int,
        async_db=Depends(get_async_db),
        lang: Optional[LanguagesChoices] = None,

):
    options = [selectinload(Slider.translations), ]
    if lang:
        options.append(joinedload(Slider.current_translation.and_(SliderTranslation.locale == lang)))
    return await slider_repo.get(async_db, obj_id=obj_id, options=options)


@api.patch(
    "/{obj_id}/update/", name='slider-update', response_model=IResponseBase[SliderVisible],
    dependencies=[Depends(get_staff_user)]
)
async def update_slider(
        obj_id: int,
        obj_in: SliderBase,
        async_db=Depends(get_async_db),

):
    db_obj = await slider_repo.get(async_db, obj_id=obj_id)
    result = await slider_repo.update(async_db, obj_in=obj_in.model_dump(exclude_unset=True), db_obj=db_obj)
    return {
        "message": _("Slider updated"),
        "data": result
    }


@api.get('/public/', name='slider-public-list', response_model=IPaginationDataBase[SliderVisible])
async def slider_public_list(
        async_db=Depends(get_async_db),
        lang: Optional[str] = Depends(get_locale),
        commons: CommonsModel = Depends(get_commons),

        order_by: Optional[Literal[
            "sort_order", "-sort_order"
        ]] = "-sort_order",
):
    q = {'is_active': True}
    options = None
    if lang:
        options = [joinedload(Slider.current_translation.and_(SliderTranslation.locale == lang))]
    rows = await slider_repo.get_all(
        async_db=async_db,
        q=q, offset=commons.offset, limit=commons.limit,
        options=options,
        order_by=(order_by,),
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": rows
    }


@api.get(
    '/public/count/', name='slider-public-count', response_model=int,
)
async def count_sliders(
        async_db=Depends(get_async_db),
        lang: Optional[str] = Depends(get_locale),

):
    params = {"is_active": True}
    return await slider_repo.count(async_db, params=params)


@api.get(
    '/public/{obj_id}/detail/',
    name='slider-public-detail',
    response_model=SliderVisible,
)
async def get_single_slider(
        obj_id: int,
        async_db=Depends(get_async_db),
        locale: str = Depends(get_locale),
):
    options = [
        joinedload(Slider.current_translation.and_(SliderTranslation.locale == locale))
    ]
    return await slider_repo.get_by_params(
        async_db, params={'id': obj_id, "is_active": True}, options=options
    )
