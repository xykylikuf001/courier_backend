from app.core.enums import TextChoices
from app.utils.translation import gettext_lazy as _


class DiscountValueTypeChoices(TextChoices):
    fixed = "fixed", "fixed"
    percentage = "percentage", "%"


class DiscountTypeChoices(TextChoices):
    voucher = "voucher", _("Voucher")
    manual = "manual", _("Manual")


class VoucherTypeChoices(TextChoices):
    shipping = "shipping", _("Entire order")
    entire_order = "entire_order", _("Shipping")
