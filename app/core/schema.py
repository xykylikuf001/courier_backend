from typing import Generic, Optional, TypeVar, List
from pydantic import (
    BaseModel as PydanticBaseModel, ConfigDict, Field,field_validator
)
from babel.support  import LazyProxy

from app.conf.config import settings
DataType = TypeVar("DataType")


def non_nullable_field(value):
    if value is None:
        raise ValueError(f"Invalid input: field must not be null value")
    return value


def non_empty_string_field(value):
    if value is None:
        raise ValueError(f"Invalid input: field must not zero length")
    return value


def string_to_null_field(value):
    return None if value == "" else value


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )


class IResponseBase(PydanticBaseModel, Generic[DataType]):
    message: Optional[str] = None
    data: DataType

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class IPaginationDataBase(PydanticBaseModel, Generic[DataType]):
    limit: int
    page: int
    rows: List[DataType]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class CommonsModel(PydanticBaseModel):
    limit: Optional[int] = settings.PAGINATION_MAX_SIZE
    offset: Optional[int] = 0
    page: Optional[int] = 1


class VisibleBase(PydanticBaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ChoiceBase(PydanticBaseModel, Generic[DataType]):
    value: DataType
    label: str

    @field_validator("label", mode="before")
    def normalize_label(cls, v):
        if isinstance(v, LazyProxy):
            return str(v)
        return v

class PhoneNumberExtendedModel(PydanticBaseModel):
    phone: str
    country_code: int = Field(alias='countryCode')
    national_number: int = Field(alias='nationalNumber')

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )
