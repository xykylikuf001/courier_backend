"""prices.

Provides a Pythonic interface to deal with money types such as money amounts,
prices, discounts and taxes.
"""

from decimal import Decimal
from typing import TypeVar

from babel.numbers import get_currency_precision

from .discount import (
    fixed_discount, fractional_discount, percentage_discount)
from .money import Money
from .money_range import MoneyRange
from .tax import flat_tax
from .taxed_money import TaxedMoney
from .taxed_money_range import TaxedMoneyRange
from .utils import sum

PriceType = TypeVar("PriceType", TaxedMoney, Money, Decimal, TaxedMoneyRange)

__all__ = [
    'Money', 'MoneyRange', 'TaxedMoney', 'TaxedMoneyRange', 'fixed_discount',
    'flat_tax', 'fractional_discount', 'percentage_discount', 'sum',
    "quantize_price", "zero_money"
]


def quantize_price(price: PriceType, currency: str) -> PriceType:
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return price.quantize(number_places)


def zero_money(currency: str) -> Money:
    """Return a money object set to zero.

    This is a function used as a model's default.
    """
    return Money(0, currency)
