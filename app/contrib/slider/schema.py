from typing import Optional, List
from datetime import datetime

from pydantic import Field, field_validator

from app.conf import LanguagesChoices
from app.contrib.file.schema import FileVisible
from app.core.schema import BaseModel, VisibleBase, non_nullable_field, ChoiceBase


class SliderTranslationVisible(VisibleBase):
    id: int
    title: str
    caption: str
    locale: ChoiceBase[LanguagesChoices]


class SliderBase(BaseModel):
    host: Optional[str] = Field(None, max_length=255)
    path: Optional[str] = Field(None, max_length=255)

    is_active: Optional[bool] = Field(None, alias="isActive")
    sort_order: Optional[int] = Field(None, alias="sortOrder", gt=0)
    _normalize_nullable = field_validator(
        "is_active", "sort_order"
    )(non_nullable_field)


class SliderCreateWithTranslation(SliderBase):
    title: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = Field(None, max_length=255)

    locale: LanguagesChoices = Field(..., alias="locale")
    _normalize_nullable = field_validator(
        "is_active", "sort_order", "title", "caption"
    )(non_nullable_field)


class SliderVisible(VisibleBase):
    id: int
    host: Optional[str] = None
    path: Optional[str] = None
    is_active: bool = Field(alias='isActive')
    sort_order: int = Field(alias='sortOrder')
    title: Optional[str] = None
    caption: Optional[str] = None
    file: Optional[FileVisible] = None
    created_at: datetime = Field(alias="createdAt")


class SliderVisibleExtended(SliderVisible):
    translations: Optional[List[SliderTranslationVisible]] = None


class SliderTranslationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = Field(None, max_length=255)
    _normalize_null = field_validator("title", "caption")(non_nullable_field)


class PlaceTranslationCreate(SliderTranslationBase):
    locale: LanguagesChoices = Field(..., alias="locale")
