from app.core.enums import TextChoices


class ServiceTypeChoices(TextChoices):
    telegram = "telegram"
    twitch = "twitch"
    binance = "binance"
    email = "email"
    steam = "steam"
    google = "google"


class UserType(TextChoices):
    staff = "staff"
    user = "user"
    driver = "driver"
