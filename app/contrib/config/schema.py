from typing import List, Optional
from decimal import Decimal
from pydantic import Field, condecimal, field_validator

from app.core.schema import BaseModel, VisibleBase, ChoiceBase, non_nullable_field
from app.conf import LanguagesChoices


class ConfigTranslationVisible(VisibleBase):
    id: int
    site_name: str = Field(alias='siteName')
    address: str
    seo_title: str = Field(alias='seoTitle')
    seo_description: str = Field(alias='seoDescription')
    seo_keywords: str = Field(alias='seoKeywords')
    locale: ChoiceBase[LanguagesChoices]


class ConfigBase(BaseModel):
    phones: List[Optional[None]] = Field(None, max_length=10)
    emails: List[Optional[None]] = Field(None, max_length=10)
    support_phone: Optional[str] = Field(None, alias="supportPhone", max_length=255)
    support_email: Optional[str] = Field(None, alias="supportEmail", max_length=255)
    regular_shipping_price: condecimal(decimal_places=2, max_digits=12) = Field(None, alias='regularShippingPrice')
    express_shipping_price: condecimal(decimal_places=2, max_digits=12) = Field(None, alias="expressShippingPrice")

    _normalize_nullable = field_validator(
        "regular_shipping_price", "express_shipping_price",
    )(non_nullable_field)


class ConfigCreate(ConfigBase):
    phones: List[str] = Field(..., max_length=10)
    emails: List[str] = Field(..., max_length=10)

    regular_shipping_price: condecimal(decimal_places=2, max_digits=12) = Field(..., alias='regularShippingPrice')
    express_shipping_price: condecimal(decimal_places=2, max_digits=12) = Field(..., alias="expressShippingPrice")


class ConfigVisible(VisibleBase):
    phones: List[str]
    emails: List[str]

    support_phone: Optional[str] = Field(None, alias="supportPhone")
    support_email: Optional[str] = Field(None, alias="supportEmail")
    regular_shipping_price: Decimal = Field(alias='regularShippingPrice')
    express_shipping_price: Decimal = Field(alias="expressShippingPrice")

    translations: Optional[List[ConfigTranslationVisible]] = None


class ConfigVisiblePublic(ConfigVisible):
    site_name: str = Field(alias='siteName')
    address: str

    seo_title: str = Field(alias='seoTitle')
    seo_description: str = Field(alias='seoDescription')
    seo_keywords: str = Field(alias='seoKeywords')

    support_phone: Optional[str] = Field(None, alias="supportPhone")
    support_email: Optional[str] = Field(None, alias="supportEmail")
    regular_shipping_price: Decimal = Field(alias='regularShippingPrice')
    express_shipping_price: Decimal = Field(alias="expressShippingPrice")

class ConfigTranslationBase(BaseModel):
    site_name: str = Field(max_length=255, alias='siteName')
    address: str = Field(max_length=255)

    seo_title: str = Field(max_length=255, alias='seoTitle')
    seo_description: str = Field(max_length=255, alias='seoDescription')
    seo_keywords: str = Field(max_length=255, alias='seoKeywords')


class ConfigTranslationCreate(ConfigTranslationBase):
    site_name: str = Field(..., max_length=255, alias='siteName')
    address: str = Field(..., max_length=255)


    locale: str = Field(..., max_length=255)
