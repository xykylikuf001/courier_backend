from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic_core import ErrorDetails
from starlette.status import HTTP_201_CREATED

from app.routers.dependency import get_active_user, get_commons, get_async_db
from app.core.schema import IPaginationDataBase, IResponseBase, CommonsModel
from app.utils.translation import gettext as _
from app.contrib.contact import SectionChoices

from .schema import (
    ContactVisible, ContactCreate, ContactBase,
    ManagerBase, ManagerCreate, ManagerVisible
)
from .repository import contact_repo, manager_repo
from .models import Contact, Manager

api = APIRouter()


@api.get(
    '/', name='contact-list',
    dependencies=[Depends(get_active_user)],
    response_model=IPaginationDataBase[ContactVisible]
)
async def get_contact_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
) -> dict:
    obj_list = await contact_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
    }


@api.post(
    '/create/', name='contact-create', response_model=IResponseBase[ContactVisible],
    status_code=HTTP_201_CREATED,
    dependencies=[Depends(get_active_user)]
)
async def create_contact(
        obj_in: ContactCreate,
        async_db=Depends(get_async_db),
) -> dict:
    is_exists = await contact_repo.exists(async_db=async_db, params={'contact_type': obj_in.contact_type})
    if is_exists:
        raise RequestValidationError(
            [ErrorDetails(
                msg=_("Contact with this type already exists"),
                loc=("body", "contactType",),
                type='value_error',
                input=obj_in.contact_type
            )]
        )
    result = await contact_repo.create(
        async_db=async_db,
        obj_in=obj_in
    )
    return {
        'data': result,
        'message': "Contact created"
    }


@api.get(
    '/{obj_id}/detail/',
    name='contact-detail',
    response_model=ContactVisible,
    dependencies=[Depends(get_active_user)]
)
async def get_single_contact(
        obj_id: int,
        async_db=Depends(get_async_db),
):
    return await contact_repo.get(async_db, obj_id=obj_id)


@api.patch(
    '/{obj_id}/update/',
    name='contact-update', response_model=IResponseBase[ContactVisible],
    dependencies=[Depends(get_active_user)]
)
async def update_contact(
        obj_id: int,
        obj_in: ContactBase,
        async_db=Depends(get_async_db),
) -> dict:
    db_obj = await contact_repo.get(async_db, obj_id=obj_id)
    if obj_in.contact_type and obj_in.contact_type != db_obj.contact_type:
        model = contact_repo.model
        is_exists = await contact_repo.exists(
            async_db,
            expressions=(
                model.id != db_obj.id,
                model.contact_type == obj_in.contact_type,
            )
        )
        if is_exists:
            raise RequestValidationError(
                [ErrorDetails(
                    msg=_("Contact with this type already exist"),
                    loc=('body', 'contactType',),
                    type='value_error',
                    input=obj_in.email
                )]
            )

    result = await contact_repo.update(
        async_db,
        db_obj=db_obj,
        obj_in=obj_in.model_dump(exclude_unset=True)
    )
    return {
        'message': "Contact updated",
        'data': result
    }


@api.get(
    '/{obj_id}/delete/', name='contact-delete',
    status_code=204,
    dependencies=[Depends(get_active_user)]
)
async def delete_contact(
        obj_id: int,
        async_db=Depends(get_async_db),
):
    await contact_repo.remove(async_db, expressions=[Contact.id == obj_id])


@api.get("/public/", name='contact-public-list', response_model=IPaginationDataBase[ContactVisible])
async def get_public_contact_list(
        async_db=Depends(get_async_db),
) -> dict:
    obj_list = await contact_repo.get_all(
        async_db=async_db,
        q={'is_active': True},
    )
    return {
        'page': 1,
        'limit': 25,
        'rows': obj_list,
    }


@api.get(
    "/manager/",
    response_model=IPaginationDataBase[ManagerVisible],
    name='manager-list',
    dependencies=[Depends(get_active_user)]
)
async def manager_list(
        async_db=Depends(get_async_db),

        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
):
    obj_list = await manager_repo.get_all(
        async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),

    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": obj_list
    }


@api.post(
    "/manager/create",
    response_model=IResponseBase[ManagerVisible],
    status_code=HTTP_201_CREATED,
    name="manager-create",
    dependencies=[Depends(get_active_user)]

)
async def create_manager(
        obj_in: ManagerCreate,
        async_db=Depends(get_async_db),
):
    result = await manager_repo.create(async_db, obj_in=obj_in)
    return {
        "message": "Manager created",
        "data": result
    }


@api.get(
    "/manager/{obj_id}/detail/", name="manager-detail",
    response_model=ManagerVisible,
    dependencies=[Depends(get_active_user)],
)
async def retrieve_single_manager(
        obj_id: int,
        async_db=Depends(get_async_db),
):
    return await manager_repo.get(async_db, obj_id=obj_id)


@api.patch(
    "/manager/{obj_id}/update/", name="manager-update",
    response_model=IResponseBase[ManagerVisible],
    dependencies=[Depends(get_active_user)],
)
async def update_manager(
        obj_id: int,
        obj_in: ManagerBase,
        async_db=Depends(get_async_db),

):
    db_obj = await manager_repo.get(async_db, obj_id=obj_id)
    result = await manager_repo.update(
        async_db,
        db_obj=db_obj,
        obj_in=obj_in.model_dump(exclude_unset=True)
    )
    return {
        "message": "Manager updated",
        "data": result
    }


@api.delete(
    "/manager/{obj_id}/delete/", name="manager-delete",
    dependencies=[Depends(get_active_user)],
    status_code=204
)
async def delete_manager(
        obj_id: int,
        async_db=Depends(get_async_db),

):
    await manager_repo.remove(async_db, expressions=[manager_repo.model.id == obj_id])


@api.get(
    '/manager/public/', name='manager-public-list', response_model=IPaginationDataBase[ManagerVisible]
)
async def retrieve_public_sponsor_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        section: Optional[SectionChoices] = Query(None),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id",
):
    expressions = [
        Manager.is_active.is_(True),
    ]
    if section:
        expressions.append(
            Manager.section == section
        )

    obj_list = await manager_repo.get_all(
        async_db,
        limit=commons.limit,
        offset=commons.offset,
        expressions=expressions,
        order_by=[order_by]
    )
    return {
        "page": commons.page,
        "limit": commons.limit,
        "rows": obj_list
    }


@api.get('/manager/public/{obj_id}/detail/', name='manager-public-detail', response_model=ManagerVisible)
async def retrieve_single_public_manager(
        obj_id: int,
        async_db=Depends(get_async_db),

):
    return await manager_repo.get_by_params(async_db, params={'is_active': True, "id": obj_id})
