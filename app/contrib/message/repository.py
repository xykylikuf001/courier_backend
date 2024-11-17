from app.db.repository import CRUDBase

from .models import Message


class CRUDMessage(CRUDBase[Message]):
    pass


message_repo = CRUDMessage(Message)
