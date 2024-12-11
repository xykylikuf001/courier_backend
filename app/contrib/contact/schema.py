from datetime import datetime
from pydantic import Field, EmailStr

from app.core.schema import BaseModel, VisibleBase, ChoiceBase, TranslatedField
from app.contrib.contact import ContactTypeChoices, SectionChoices


class ContactBase(BaseModel):
    contact: str = Field(max_length=255)
    contact_type: ContactTypeChoices = Field(alias='contactType')
    is_active: bool = Field(alias='isActive')


class ContactCreate(ContactBase):
    contact: str = Field(..., max_length=255)
    contact_type: ContactTypeChoices = Field(..., alias='contactType')
    is_active: bool = Field(..., alias='isActive')


class ContactVisible(VisibleBase):
    id: int
    contact: str
    contact_type: ChoiceBase[ContactTypeChoices] = Field(alias="contactType")
    is_active: bool = Field(alias='isActive')


class ManagerBase(BaseModel):
    title: TranslatedField
    full_name: str = Field(max_length=255, alias="fullName")
    email: EmailStr = Field(alias="email")
    phone: str = Field(max_length=255)
    section: SectionChoices = Field(alias="section")
    is_active: bool = Field(alias='isActive')


class ManagerCreate(BaseModel):
    title: TranslatedField
    full_name: str = Field(..., alias="fullName", max_length=255)
    email: EmailStr = Field(..., alias="email")
    phone: str = Field(..., max_length=255)
    section: SectionChoices = Field(..., alias="section")
    is_active: bool = Field(..., alias='isActive')


class ManagerVisible(VisibleBase):
    id: int
    title: TranslatedField
    email: str
    phone: str
    section: ChoiceBase[SectionChoices]
    full_name: str = Field(alias="fullName")
    is_active: bool = Field(alias='isActive')
