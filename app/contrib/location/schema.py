from typing import Optional, List
from pydantic import Field, field_validator

from app.conf import LanguagesChoices
from app.contrib.location import PlaceLevelChoices
from app.core.schema import VisibleBase, ChoiceBase, BaseModel, non_nullable_field, non_empty_string_field


class PlaceTranslationVisible(VisibleBase):
    id: int
    name: str
    full_name: str = Field(alias="fullName")
    locale: ChoiceBase[LanguagesChoices]


class PlaceBase(BaseModel):
    slug: Optional[str] = Field(None, max_length=255)
    location_level: Optional[PlaceLevelChoices] = Field(None, alias="locationLevel")
    is_active: Optional[bool] = Field(None, alias='isActive')
    parent_id: Optional[int] = Field(None, alias='parentId', gt=0)
    _normalize_empty = field_validator("slug")(non_empty_string_field)
    _normalize_null = field_validator(
        "location_level", "is_active", "slug"
    )(non_nullable_field)


class PlaceCreateWithTranslation(BaseModel):
    slug: Optional[str] = Field(None, max_length=255)
    location_level: Optional[PlaceLevelChoices] = Field(None, alias="locationLevel")
    is_active: Optional[bool] = Field(None, alias='isActive')
    parent_id: Optional[int] = Field(None, alias='parentId', gt=0)

    name: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=255, alias="fullName")
    locale: LanguagesChoices = Field(..., alias="locale")

    _normalize_empty = field_validator("full_name")(non_empty_string_field)
    _normalize_null = field_validator(
        "location_level", "is_active", "slug"
    )(non_nullable_field)


class PlaceVisible(VisibleBase):
    id: int
    slug: str

    name: Optional[str] = None
    full_name: Optional[str] = Field(None, alias="fullName")
    location_level: ChoiceBase[PlaceLevelChoices] = Field(alias="locationLevel")
    locale: Optional[ChoiceBase[LanguagesChoices]] = None
    parent_id: Optional[int] = Field(None, alias='parentId')
    tree_id: Optional[int] = Field(None, alias='treeId')
    left: int
    right: int
    level: int
    is_active: bool = Field(alias="isActive")
    has_children: bool = Field(alias='hasChildren')


class PlaceVisibleExtended(PlaceVisible):
    translations: Optional[List[PlaceTranslationVisible]] = None


class PlaceTranslationBase(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255, alias="fullName")
    _normalize_empty = field_validator("name")(non_empty_string_field)
    _normalize_null = field_validator("name")(non_nullable_field)


class PlaceTranslationCreate(PlaceTranslationBase):
    name: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=255, alias="fullName")

    locale: LanguagesChoices = Field(..., alias="locale")
