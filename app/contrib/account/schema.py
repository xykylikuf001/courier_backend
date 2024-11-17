import re
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator, EmailStr, AwareDatetime

from app.core.schema import BaseModel, VisibleBase, non_nullable_field, ChoiceBase
from app.contrib.account import ServiceTypeChoices, UserType


def is_valid_string(s: str) -> str:
    """
    Check if the input string only contains alphabetic characters, underscores, and hyphens.

    :param s: The input string to check.
    :return: True if the string is valid, False otherwise.
    """
    pattern = r'^[a-zA-Z_-]+$'
    if not re.match(pattern, s):
        raise ValueError(f"Invalid input: {s}. Only alphabetic characters, underscores, and hyphens are allowed.")
    return s


def validate_password(v: Optional[str], info):
    """
    Validate password
    :param v:
    :param info:
    :return:
    """
    values = info.data
    password_confirm = values.get('password_confirm')
    if v != password_confirm:
        raise ValueError('Passwords do not match')
    return v


class ProfilePasswordIn(BaseModel):
    old_password: str = Field(..., alias='oldPassword', max_length=50)
    password_confirm: str = Field(..., alias='passwordConfirm', max_length=50)
    password: str = Field(..., max_length=50, min_length=5)
    code: str = Field(..., max_length=50)

    _validate_password = field_validator("password")(validate_password)


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=50, min_length=8)
    is_staff: Optional[bool] = Field(None, alias="isStaff")
    is_active: Optional[bool] = Field(None, alias="isActive")
    user_type: Optional[UserType] = Field(None, alias='userType')
    _normalize_nullable = field_validator(
        "name", "is_staff", "is_active", "password", "user_type"
    )(non_nullable_field)


class UserCreate(UserBase):
    name: str = Field(..., max_length=255)
    email: EmailStr
    password: str = Field(..., max_length=50, min_length=8)


class UserVisible(VisibleBase):
    id: UUID
    name: str
    email: Optional[str] = None
    email_verified_at: Optional[datetime] = Field(None, alias="emailVerifiedAt")
    created_at: datetime = Field(alias="createdAt")
    is_staff: bool = Field(alias='isStaff')
    is_active: bool = Field(alias='isActive')

    external_accounts: List["ExternalAccountVisible"] = None


class VerifyToken(BaseModel):
    access_token: str


class Token(BaseModel):
    user: UserVisible
    token_type: str
    access_token: str
    refresh_token: Optional[str] = None


class TokenPayload(PydanticBaseModel):
    user_id: UUID
    email: Optional[str] = None
    iat: Optional[int] = None
    exp: int
    jti: UUID
    aud: str


class SignUpResult(VisibleBase):
    user: UserVisible
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class SignUpIn(BaseModel):
    name: str = Field(..., alias='name', max_length=255)
    email: EmailStr
    password_confirm: str = Field(..., alias='passwordConfirm', max_length=50, min_length=5)
    password: str = Field(..., max_length=50, min_length=5)
    subscription: Optional[bool] = True
    policy: bool

    @field_validator('password')
    def validate_password(cls, v: Optional[str], info):
        """
        Validate password
        :param v:
        :param info:
        :return:
        """
        values = info.data
        password_confirm = values.get('password_confirm')
        if v != password_confirm:
            raise ValueError('Passwords do not match')
        return v


class UserSessionVisible(BaseModel):
    id: UUID
    user_id: UUID = Field(alias="userId")
    revoked_at: Optional[datetime] = Field(None, alias="revokedAt")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    created_at: datetime = Field(alias="createdAt")


class UserSession(BaseModel):
    id: UUID
    name: str
    is_superuser: bool
    is_active: bool
    is_staff: bool
    email: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")
    email_verified_at: Optional[datetime] = Field(alias="emailVerifiedAt")


class ExternalAccountVisible(BaseModel):
    id: int
    user_id: UUID = Field(alias="userId")
    account_id: str = Field(alias="accountId")
    username: str

    created_at: datetime = Field(alias="createdAt")
    service_type: ChoiceBase[ServiceTypeChoices]



class ProfileChangeEmail(BaseModel):
    code: str = Field(..., max_length=255)
    email_code: str = Field(..., max_length=255, alias="emailCode")
    email: EmailStr


class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    password_confirm: str = Field(..., alias='passwordConfirm', max_length=50)
    password: str = Field(..., max_length=50, min_length=5)
    code: str = Field(..., max_length=50)

    _validate_password = field_validator("password")(validate_password)


# class GoogleAuth(BaseModel):
#     code: str = Field(..., max_length=255)
#     scope: str = Field(..., max_length=255)
#     authuser: str = Field(..., max_length=255)
#     prompt: str = Field(..., max_length=255)

