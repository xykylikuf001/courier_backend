

from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic_core import ErrorDetails
from starlette.status import HTTP_400_BAD_REQUEST
from sqlalchemy.orm import joinedload, selectinload

from app.routers.dependency import get_active_user, get_async_db, get_commons
from app.core.schema import IResponseBase, IPaginationDataBase, CommonsModel
from app.utils.translation import gettext as _
from app.core.exceptions import HTTP404
from app.conf.config import settings

from .schema import (
    ConfigCreate, ConfigVisible, ConfigVisiblePublic,
    ConfigTranslationVisible, ConfigTranslationCreate, ConfigTranslationBase,
)
from .repository import config_repo, config_tr_repo
from .models import Config, ConfigTranslation

api = APIRouter()


@api.get('/', name='config-detail', response_model=ConfigVisible, dependencies=[Depends(get_active_user)])
async def config_detail(
        async_db=Depends(get_async_db),
):
    options = [
        selectinload(Config.translations)
    ]
    db_obj = await config_repo.first(async_db, options=options)
    if not db_obj:
        raise HTTP404(detail=_("Config does not created yet"))
    return db_obj




@api.post(
    '/manage/', name='config-manage', response_model=IResponseBase[ConfigVisible],
    dependencies=[Depends(get_active_user)]
)
async def config_manage(
        obj_in: ConfigCreate,
        async_db=Depends(get_async_db),
) -> dict:
    db_obj = await config_repo.first(async_db)
    if not db_obj:
        result = await config_repo.create(async_db, obj_in=obj_in)
        return {
            "message": "Config created",
            "data": result
        }
    result = await config_repo.update(async_db=async_db, obj_in=obj_in, db_obj=db_obj)
    return {
        'data': result,
        'message': "Config updated"
    }


@api.get('/translations/', name='config-tr-list', response_model=IPaginationDataBase[ConfigTranslationVisible],

         dependencies=[Depends(get_active_user)])
async def get_config_translations(

        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),

        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
) -> dict:
    obj_list = await config_tr_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
    )
    count = await config_tr_repo.count(async_db)
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
        'count': count,
    }


@api.post(
    "/translations/create/", name='config-tr-create', response_model=IResponseBase[ConfigTranslationVisible],
    status_code=201,
    dependencies=[Depends(get_active_user)]
)
async def manage_config_translations(
        obj_in: ConfigTranslationCreate,
        async_db=Depends(get_async_db),
) -> dict:
    if obj_in.locale not in settings.LANGUAGES:
        raise RequestValidationError(
            [ErrorDetails(
                msg=_("Translation with this locale %(locale)s not supported") % {"locale": obj_in.locale},
                loc=("body", "locale",),
                type='value_error',
                input=obj_in.locale
            )]
        )
    db_obj = await config_repo.first(async_db)
    if not db_obj:
        raise HTTPException(detail=_("Config does not exist yet"), status_code=HTTP_400_BAD_REQUEST)

    is_exists = await config_tr_repo.exists(async_db, params={'locale': obj_in.locale})
    if is_exists:
        raise RequestValidationError(
            [ErrorDetails(
                msg="Translation with this locale %(locale)s already exists" % {"locale": obj_in.locale},
                loc=("body", "locale",),
                type='value_error',
                input=obj_in.locale
            )]
        )
    result = await config_tr_repo.create(async_db, obj_in={
        "id": db_obj.id,
        "seo_title": obj_in.seo_title,
        "seo_description": obj_in.seo_description,
        "seo_keywords": obj_in.seo_keywords,
        "address": obj_in.address,
        "site_name": obj_in.site_name,
        "locale": obj_in.locale
    })

    return {
        "message": "Config translation created: %(locale)s" % {"locale": obj_in.locale},
        "data": result
    }


@api.get('/translations/{locale}/detail/', name='config-tr-detail', response_model=ConfigTranslationVisible,
         dependencies=[Depends(get_active_user)])
async def config_translation_detail(
        locale: str,
        async_db=Depends(get_async_db),
):
    return await config_tr_repo.get_by_params(async_db, params={'locale': locale})


@api.patch(
    '/translations/{locale}/update/',
    name='config-tr-update', response_model=IResponseBase[ConfigTranslationVisible],
    dependencies=[Depends(get_active_user)]
)
async def update_config_translation(
        locale: str,
        obj_in: ConfigTranslationBase,
        async_db=Depends(get_async_db),
) -> dict:
    db_obj = await config_tr_repo.get_by_params(async_db, params={'locale': locale})
    result = await config_tr_repo.update(
        async_db, db_obj=db_obj, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    return {
        "message": _("Config translation updated: %(locale)s") % {"locale": locale},
        "data": result
    }


@api.get(
    '/translations/{locale}/delete/', name='config-tr-delete',
    response_model=IResponseBase[ConfigTranslationVisible],
    dependencies=[Depends(get_active_user)]
)
async def delete_config_translation(
        locale: str,
        async_db=Depends(get_async_db),
):
    db_obj = await config_tr_repo.get_by_params(async_db, params={'locale': locale})
    result = await config_tr_repo.delete(async_db, db_obj=db_obj)
    return {
        "message": _("Config translation deleted: %(locale)s") % {"locale": locale},
        "data": result
    }


@api.get("/public/", name='config-public', response_model=ConfigVisiblePublic)
async def get_public_config(
        lang: str,
        async_db=Depends(get_async_db),
):
    options = [
        joinedload(Config.current_translation.and_(ConfigTranslation.locale == lang), innerjoin=True)
    ]
    config = await config_repo.first(async_db, options=options)
    if not config:
        raise HTTP404(detail="Config does not exist!")
    return config
