from app.utils.translation import gettext_lazy as _
from app.core.enums import TextChoices


class PlaceLevelChoices(TextChoices):
    country = 'country', _("country")
    region = 'region', _("region")
    city = 'city', _("city")
    district = 'district', _("district")
    village = 'village', _("village")
    other = 'other', _("other")
