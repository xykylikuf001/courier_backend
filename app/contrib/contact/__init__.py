from app.core.enums import TextChoices


class ContactTypeChoices(TextChoices):
    email = "email"
    facebook = "facebook"
    google = "google"
    imo = "imo"
    instagram = "instagram"
    link = "link"
    linkedin = "linkedin"
    pinterest = "pinterest"
    phone = "phone"
    telegram = "telegram"
    tiktok = "tiktok"
    twitter = "twitter"
    whatsapp = "whatsapp"
    wechat = "wechat"
    youtube = "youtube"


class SectionChoices(TextChoices):
    about_us = "about_us"
    application = "application"
    sponsor = "sponsor"
    hackathon = "hackathon"
    startup = "startup"
    contact = "contact"
