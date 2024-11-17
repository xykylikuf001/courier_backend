from app.db.repository import CRUDBase

from .models import Notification


class CRUDNotification(CRUDBase[Notification]):
    pass


notification_repo = CRUDNotification(Notification)
