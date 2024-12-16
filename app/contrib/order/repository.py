from typing import TYPE_CHECKING, List

from app.db.repository import CRUDBase

from .models import (
    Order, OrderLine,
)
from .schema import OrderLineCheckout
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CRUDOrder(CRUDBase[Order]):
    pass

class CrudOrderLine(CRUDBase[OrderLine]):
    pass


order_repo = CRUDOrder(Order)
