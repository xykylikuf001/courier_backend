from typing import List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from app.core.schema import IResponseBase, IPaginationDataBase, CommonsModel
from app.routers.dependency import get_async_db, get_staff_user, get_commons
from app.core.exceptions import HTTP404
from .manager import get_plugins_manager
from .schema import PluginVisible, PluginConfigurationBase
from .utils import resolve_plugins, resolve_plugin

api = APIRouter()


@api.get(
    '/', name='plugin-list', response_model=List[PluginVisible],
    dependencies=[Depends(get_staff_user)]
)
async def get_plugin_list(
        async_db=Depends(get_async_db)
):
    manager = get_plugins_manager()

    obj_list = await resolve_plugins(async_db, manager)
    return obj_list


@api.get(
    '/{identifier}/detail/', name="plugin-detail", response_model=PluginVisible,

    dependencies=[Depends(get_staff_user)]
)
async def retrieve_single_plugin(
        identifier: str,
        async_db=Depends(get_async_db),

):
    manager = get_plugins_manager()
    plugin = await resolve_plugin(async_db, identifier, manager)
    if plugin is None:
        raise HTTP404(detail="Plugin does not exists")

    return plugin


@api.get(
    '/{identifier}/update/', name='plugin-update', response_model=IResponseBase[PluginVisible],

    dependencies=[Depends(get_staff_user)]
)
async def update_plugin(
        identifier: str,
        obj_in: PluginConfigurationBase,
        async_db=Depends(get_async_db),
):
    manager = get_plugins_manager()
    plugin = await manager.get_plugin(identifier, async_db)
    await manager.save_plugin_configuration(identifier, obj_in.model_dump(), async_db)

    return {
        "message": "Plugin updated",
        "result": plugin
    }
