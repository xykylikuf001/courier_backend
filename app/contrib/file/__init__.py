from app.core.enums import TextChoices


class FileTypeChoices(TextChoices):
    image = "image"
    video = "video"
    gif = "gif"
    pdf = "pdf"
    mp3 = "mp3"


class ThumbnailCropChoices(TextChoices):
    center = 'center'
    left = 'left'
    right = 'right'


class ContentTypeChoices(TextChoices):
    slider = "slider"
