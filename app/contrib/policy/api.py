from typing import Optional, Literal
from fastapi import APIRouter, Depends
from fastapi.exceptions import RequestValidationError

from pydantic_core import ErrorDetails

from app.core.schema import IPaginationDataBase, IResponseBase, CommonsModel
from app.routers.dependency import get_staff_user, get_async_db, get_commons, get_language
from app.utils.translation import gettext as _

from .schema import PolicyTranslationVisible, PolicyTranslationBase, PolicyTranslationCreate
from .repository import policy_tr_repo

api = APIRouter()


@api.get(
    '/', name='policy-tr-list', response_model=IPaginationDataBase[PolicyTranslationVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_policy_translation_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
):
    obj_list = await policy_tr_repo.get_all(
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


@api.post(
    '/create/', name='policy-tr-create', response_model=IResponseBase[PolicyTranslationVisible],
    dependencies=[Depends(get_staff_user)]
)
async def create_policy_translation(
        obj_in: PolicyTranslationCreate,
        async_db=Depends(get_async_db),
):
    is_exist = await policy_tr_repo.exists(async_db, params={'locale': obj_in.locale.value})
    if is_exist:
        raise RequestValidationError(
            [ErrorDetails(
                msg=_("Policy translation with this locale already exist"),
                loc=("body", "locale",),
                type='value_error',
                input=obj_in.locale
            )]
        )
    result = await policy_tr_repo.create(
        async_db=async_db, obj_in=obj_in.model_dump()
    )
    return {
        "message": _("Policy translation created"),
        "data": result
    }


@api.get(
    '/{obj_id}/detail/', name='policy-tr-detail', response_model=PolicyTranslationVisible,
    dependencies=[Depends(get_staff_user)]
)
async def retrieve_sinel_policy_translation(
        obj_id: int,
        async_db=Depends(get_async_db),
):
    return await policy_tr_repo.get(async_db, obj_id=obj_id)


@api.patch(
    '/{obj_id}/update/',
    name='policy-tr-update',
    response_model=IResponseBase[PolicyTranslationVisible],
    dependencies=[Depends(get_staff_user)]
)
async def update_policy(
        obj_id: int,
        obj_in: PolicyTranslationBase,
        async_db=Depends(get_async_db),
):
    db_obj = await policy_tr_repo.get(async_db, obj_id=obj_id)
    result = await policy_tr_repo.update(
        async_db, db_obj=db_obj, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    return {
        "message": _("Policy translation updated"),
        "data": result
    }


@api.get('/public/detail/', name='policy-public-detail', response_model=PolicyTranslationVisible)
async def retrieve_policy_public_detail(
        lang=Depends(get_language),
        async_db=Depends(get_async_db),
):
    return await policy_tr_repo.get_by_params(
        async_db, params={'locale': lang}
    )
