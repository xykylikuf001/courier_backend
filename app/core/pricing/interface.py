from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from app.contrib.discount import DiscountTypeChoices

if TYPE_CHECKING:
    from app.contrib.discount.models import OrderLineDiscount, Voucher
    from app.contrib.order.models import OrderLine


@dataclass
class LineInfo:
    line: Union["OrderLine"]
    discounts: Iterable[Union["OrderLineDiscount"]]
    voucher: Optional["Voucher"]
    voucher_code: Optional[str]

    def get_voucher_discounts(self):
        return [
            discount
            for discount in self.discounts
            if discount.type == DiscountTypeChoices.voucher
        ]
