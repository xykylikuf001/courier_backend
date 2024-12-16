from app.db.repository import CRUDBase

from .models import PluginConfiguration


class CRUDPluginConfiguration(CRUDBase[PluginConfiguration]):
    pass


plugin_config_repo = CRUDPluginConfiguration(PluginConfiguration)
