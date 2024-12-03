from app.db.repository import CRUDBase

from .models import PolicyTranslation

class CRUDPolicyTranslation(CRUDBase[PolicyTranslation]):
    pass

policy_tr_repo = CRUDPolicyTranslation(PolicyTranslation)
