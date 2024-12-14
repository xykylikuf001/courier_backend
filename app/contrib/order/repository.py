from typing import TYPE_CHECKING

from app.db.repository import CRUDBase

from .models import (
    Order, OrderLine,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CRUDOrder(CRUDBase[Order]):
    pass


class CrudOrderLine(CRUDBase[OrderLine]):
    pass


order_repo = CRUDOrder(Order)
