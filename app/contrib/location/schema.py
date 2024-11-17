from typing import Optional
from pydantic import Field

from app.conf import LanguagesChoices
from app.contrib.location import PlaceLevelChoices
from app.core.schema import VisibleBase, ChoiceBase, BaseModel


class PostTranslationVisible(VisibleBase):
    id: int
    name: str
    full_name: str = Field(alias="fullName")
    locale: ChoiceBase[LanguagesChoices]


class PlaceBase(BaseModel):
    slug: Optional[str] = Field(max_length=255)
    location_level: Optional[PlaceLevelChoices] = Field(alias="locationLevel")

    parent_id: Optional[int] = Field(None, alias='parentId', gt=0)


class PlaceCreateWithTranslation(PlaceBase):
    name: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=255, alias="fullName")
    locale: LanguagesChoices = Field(..., alias="locale")


class PlaceVisible(VisibleBase):
    id: int
    slug: str

    name: Optional[str] = None
    full_name: Optional[str] = Field(None, alias="fullName")
    locale: Optional[ChoiceBase[LanguagesChoices]] = None
    parent_id: Optional[int] = Field(None, alias='parentId')
    tree_id: Optional[int] = Field(None, alias='treeId')
    left: int
    right: int
    level: int
