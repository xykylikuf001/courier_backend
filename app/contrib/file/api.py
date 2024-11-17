from typing import Optional, Literal

from fastapi import APIRouter, Depends, UploadFile, Form

from app.core.schema import IPaginationDataBase, CommonsModel, IResponseBase
from app.routers.dependency import get_active_user, get_async_db, get_commons
from app.contrib.file import ContentTypeChoices

from .schema import FileVisible, FileBase
from .repository import file_repo

api = APIRouter()


@api.get(
    '/',
    name='file-list', response_model=IPaginationDataBase[FileVisible],
    dependencies=[Depends(get_active_user)]
)
async def get_media_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),

        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
):
    obj_list = await file_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        q={"content_type": ContentTypeChoices.gallery}
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
    }


@api.post("/create/upload/", name='file-upload', response_model=IResponseBase[FileVisible],
          dependencies=[Depends(get_active_user)])
async def create_media(
        upload_file: UploadFile,
        caption: Optional[str] = Form(None, max_length=500),
        async_db=Depends(get_async_db),
):
    result = await file_repo.create_with_file(
        async_db,
        upload_file=upload_file,
        obj_in={
            "content_type": ContentTypeChoices.gallery,
            "caption": caption,
        }
    )
    return {
        "message": "File created",
        "data": result
    }


@api.get(
    '/{obj_id}/detail/',
    name="file-detail",
    response_model=FileVisible,
    dependencies=[Depends(get_active_user)])
async def get_single_file(
        obj_id: int,
        async_db=Depends(get_async_db)
):
    return await file_repo.get(async_db, obj_id=obj_id)


@api.patch(
    "/{obj_id}/update/", name="file-update", response_model=IResponseBase[FileVisible],
    dependencies=[Depends(get_active_user)]
)
async def update_media(
        obj_id: int,
        obj_in: FileBase,
        async_db=Depends(get_async_db)

):
    db_obj = await file_repo.get(async_db, obj_id=obj_id)
    result = await file_repo.update(
        async_db, db_obj=db_obj, obj_in={"caption": obj_in.caption}
    )
    return {
        'message': "File updated",
        'data': result
    }


@api.delete(
    '/{obj_id}/delete/',
    name="file-delete",
    status_code=204,
    dependencies=[Depends(get_active_user)]
)
async def delete_media(
        obj_id: int,
        async_db=Depends(get_async_db),
):
    db_obj = await file_repo.get(async_db, obj_id=obj_id)
    await file_repo.delete_with_file(async_db, db_obj)


@api.get(
    '/public/', name='file-public-list', response_model=IPaginationDataBase[FileVisible],
)
async def get_media_list(
        async_db=Depends(get_async_db),
        commons: CommonsModel = Depends(get_commons),
        order_by: Optional[Literal[
            "id", "-id"
        ]] = "-id"
):
    obj_list = await file_repo.get_all(
        async_db=async_db,
        limit=commons.limit,
        offset=commons.offset,
        order_by=(order_by,),
        q={
            "content_type": ContentTypeChoices.gallery,
            "is_active": True
        }
    )
    return {
        'page': commons.page,
        'limit': commons.limit,
        'rows': obj_list,
    }
