from app.core.enums import TextChoices
from app.utils.translation import gettext_lazy as _


class ShippingMethodTypeChoices(TextChoices):
    price_based = "price_based", _("Price based shipping")
    weight_based = "weight_based", _("Weight based shipping")
