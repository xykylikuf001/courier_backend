from dataclasses import dataclass

from app.utils.prices import Money


@dataclass
class OrderPricesData:
    """Store an order prices data with applied taxes.

    'price_with_discounts' includes voucher discount and sale discount if any valid
    exists.
    'un_discounted_price' is a price without any sale and voucher.
    """

    un_discounted_price: Money
    price_with_discounts: Money
