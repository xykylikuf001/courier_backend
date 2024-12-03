from app.db.repository import CRUDBase

from .models import Contact, Manager


class CRUDContact(CRUDBase[Contact]):
    pass


class CRUDManager(CRUDBase[Manager]):
    pass


manager_repo = CRUDManager(Manager)
contact_repo = CRUDContact(Contact)
