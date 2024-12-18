from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from typing import Optional, List
from uuid import UUID

from app.core.pricing.interface import LineInfo
from app.utils.prices import zero_money, quantize_price
from app.contrib.discount import DiscountTypeChoices, VoucherTypeChoices
from app.contrib.discount.interface import fetch_voucher_info
from app.contrib.discount.models import OrderLineDiscount
from ..discount.utils.voucher import apply_voucher_to_line
from ..payment.models import Payment
from .models import Order, OrderLine


@dataclass
class OrderInfo:
    order: "Order"
    customer_email: "str"
    payment: Optional["Payment"]
    lines_data: Iterable["OrderLineInfo"]


@dataclass
class OrderLineInfo:
    line: "OrderLine"
    replace: bool = False
    line_discounts: Optional[Iterable["OrderLineDiscount"]] = None


def fetch_order_info(order: "Order") -> OrderInfo:
    order_lines_info = fetch_order_lines(order)
    order_data = OrderInfo(
        order=order,
        customer_email=order.customer_email,
        # payment=order.get_last_payment(),
        lines_data=order_lines_info,
    )
    return order_data


def fetch_order_lines(lines: List["OrderLine"]) -> list[OrderLineInfo]:
    lines_info = []
    for line in lines:
        lines_info.append(
            OrderLineInfo(line=line)
        )

    return lines_info


@dataclass
class EditableOrderLineInfo(LineInfo):
    line: "OrderLine"
    discounts: list["OrderLineDiscount"]

    def get_manual_line_discount(
            self,
    ) -> Optional["OrderLineDiscount"]:
        for discount in self.discounts:
            if discount.type == DiscountTypeChoices.manual:
                return discount
        return None


def fetch_draft_order_lines_info(
        order: "Order", lines: Optional[Iterable["OrderLine"]] = None,
) -> list[EditableOrderLineInfo]:
    # prefetch_related_fields = [
    #     "discounts__promotion_rule__promotion",
    #     "variant__channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
    #     "variant__channel_listings__variantlistingpromotionrule__promotion_rule__translations",
    #     "variant__product__collections",
    #     "variant__product__product_type",
    # ]
    lines_info = []

    for line in lines:
        lines_info.append(
            EditableOrderLineInfo(
                line=line,
                discounts=list(line.discounts),
                voucher=None,
                voucher_code=None,
            )
        )
    voucher = order.voucher
    if voucher and (
            voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order
    ):
        voucher_info = fetch_voucher_info(voucher, order.voucher_code)
        apply_voucher_to_line(voucher_info, lines_info)
    return lines_info


def get_prefetched_variant_listing(
        variant: Optional[ProductVariant], channel_id: int
) -> Optional[ProductVariantChannelListing]:
    if not variant:
        return None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            return channel_listing
    return None
