from typing import TYPE_CHECKING

from app.contrib.plugins.base_plugin import ConfigurationTypeField
from .schema import PluginVisible

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def hide_private_configuration_fields(configuration, config_structure):
    if not config_structure:
        return

    for field in configuration:
        name = field["name"]
        value = field["value"]
        if value is None:
            continue
        field_type = config_structure.get(name, {}).get("type")
        if field_type == ConfigurationTypeField.PASSWORD:
            field["value"] = "" if value else None

        if field_type in [
            ConfigurationTypeField.SECRET,
            ConfigurationTypeField.SECRET_MULTILINE,
        ]:
            if not value:
                field["value"] = None
            elif len(value) > 4:
                field["value"] = value[-4:]
            else:
                field["value"] = value[-1:]


async def resolve_plugin(
        async_db: "AsyncSession", identifier: str, manager
):
    plugin = await manager.get_plugin(identifier, async_db)
    if not plugin or plugin.HIDDEN is True:
        return None

    return PluginVisible(
        id=plugin.PLUGIN_ID,
        is_active=plugin.is_active,
        configuration=plugin.configuration,

        description=plugin.PLUGIN_DESCRIPTION,
        name=plugin.PLUGIN_NAME,
    )


async def resolve_plugins(
        async_db: "AsyncSession",
        manager
):
    all_plugins = await manager.get_all_plugins(async_db)
    plugins = []
    for plugin in all_plugins:
        hide_private_configuration_fields(plugin.configuration, plugin.CONFIG_STRUCTURE)
        if plugin.HIDDEN is True:
            continue
        plugins.append(PluginVisible(

            id=plugin.PLUGIN_ID,
            is_active=plugin.is_active,
            configuration=plugin.configuration,

            description=plugin.PLUGIN_DESCRIPTION,
            name=plugin.PLUGIN_NAME,
        ))
    return plugins
