from typing import Optional

from sqlalchemy import String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import ChoiceType

from app.db.models import CreationModificationDateBase
from app.contrib.file import FileTypeChoices, ThumbnailCropChoices, ContentTypeChoices


class File(CreationModificationDateBase):
    __tablename__ = "file"
    file_type: Mapped[FileTypeChoices] = mapped_column(
        ChoiceType(choices=FileTypeChoices, impl=String(25)),
        nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    content_type: Mapped[ContentTypeChoices] = mapped_column(
        ChoiceType(choices=ContentTypeChoices, impl=String(50)), nullable=False
    )
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    poster: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Thumbnail(CreationModificationDateBase):
    original: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    crop: Mapped[ThumbnailCropChoices] = mapped_column(
        ChoiceType(choices=ThumbnailCropChoices, impl=String(25)),
        nullable=False
    )
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
