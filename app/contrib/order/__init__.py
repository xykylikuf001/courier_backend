from app.core.enums import TextChoices
from app.utils.translation import gettext_lazy as _

class OrderStatus(TextChoices):
    pending = "pending", _("Pending")
    completed = "completed", _("Completed"),
    cancelled = "cancelled", _("Cancelled"),
    rejected = "rejected", _("Rejected"),

