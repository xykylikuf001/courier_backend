from app.db.repository import CRUDBase

from .models import Order


class CRUDOrder(CRUDBase[Order]):
    pass


order_repo = CRUDOrder(Order)
