from app.core.enums import TextChoices
from app.utils.translation import gettext_lazy as _

class OrderStatusChoices(TextChoices):
    pending = "pending", _("Pending")
    accepted = "accepted", _("Accepted")
    on_process = "on_process", _("On process")
    completed = "completed", _("Completed"),
    cancelled = "cancelled", _("Cancelled"),
    rejected = "rejected", _("Rejected"),


class ShippingTypeChoices(TextChoices):
    regular = "regular", _("Regular")
    express = "express", _("Express")

