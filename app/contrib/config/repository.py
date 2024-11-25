from app.db.repository import CRUDBase

from .models import Config, ConfigTranslation


class CRUDConfig(CRUDBase[Config]):
    pass


class CRUDConfigTranslation(CRUDBase[ConfigTranslation]):
    pass


config_repo = CRUDConfig(Config)
config_tr_repo = CRUDConfigTranslation(ConfigTranslation)
