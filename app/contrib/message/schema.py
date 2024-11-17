from typing import Optional
from datetime import datetime

from pydantic import Field, EmailStr

from app.core.schema import BaseModel, VisibleBase


class MessageBase(BaseModel):
    full_name: str = Field(max_length=255, alias='fullName')
    subject: Optional[str] = Field(None, max_length=255)
    body: str = Field(max_length=1000)
    email: EmailStr = Field(alias='email')
    phone: Optional[str] = Field(max_length=255)


class MessageCreate(MessageBase):
    full_name: str = Field(..., alias='fullName', max_length=255)
    body: str = Field(..., max_length=1000)
    email: EmailStr = Field(..., alias='email')


class MessageVisible(VisibleBase):
    id: int
    full_name: str = Field(..., alias="fullName")
    subject: Optional[str] = None
    body: str
    email: EmailStr
    phone: Optional[str] = None
    is_read: bool = Field(..., alias='isRead')
    created_at: datetime = Field(..., alias="createdAt")