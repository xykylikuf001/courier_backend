from typing import Optional
from pydantic import Field, field_validator
from app.core.schema import VisibleBase, BaseModel, non_nullable_field, ChoiceBase
from app.conf import LanguagesChoices


class PolicyTranslationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    _normalize_null = field_validator("title", "body")(non_nullable_field)


class PolicyTranslationCreate(PolicyTranslationBase):
    title: str = Field(..., max_length=255)
    body: str
    locale: LanguagesChoices


class PolicyTranslationVisible(VisibleBase):
    id: int
    title: str
    body: str
    locale: ChoiceBase[LanguagesChoices]
