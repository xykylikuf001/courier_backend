import re
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator, EmailStr, AwareDatetime

from app.core.schema import BaseModel, VisibleBase, non_nullable_field, ChoiceBase, string_to_null_field
from app.contrib.account import ServiceTypeChoices, UserTypeChoices
from app.utils.translation import gettext as _


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


class AuthPhone(BaseModel):
    phone: str = Field(..., max_length=255)
    password: str = Field(..., max_length=50, min_length=5)


class PasswordIn(BaseModel):
    old_password: str = Field(..., alias='oldPassword', max_length=50)
    password_confirm: str = Field(..., alias='passwordConfirm', max_length=50)
    password: str = Field(..., max_length=50, min_length=5)
    _validate_password = field_validator("password")(validate_password)


class ProfilePasswordIn(PasswordIn):
    code: str = Field(..., max_length=50)


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    email_verified_at: Optional[AwareDatetime] = Field(None, alias="emailVerifiedAt")
    phone: Optional[str] = Field(None, max_length=255)
    phone_verified_at: Optional[AwareDatetime] = Field(None, alias="phoneVerifiedAt")
    name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=50, min_length=8)
    is_staff: Optional[bool] = Field(None, alias="isStaff")
    is_active: Optional[bool] = Field(None, alias="isActive")
    user_type: Optional[UserTypeChoices] = Field(None, alias='userType')
    _normalize_nullable = field_validator(
        "name", "is_staff", "is_active", "password", "user_type"
    )(non_nullable_field)
    _normalize_empty = field_validator(
        "email",
        "phone",
        "email_verified_at",
        "phone_verified_at",
        mode="before"
    )(string_to_null_field)

    @field_validator("email_verified_at")
    def normalize_email_verified_at(cls, v: Optional[str], info):
        data = info.data
        email = data.get('email')
        if email is None:
            return None
        return v

    @field_validator("phone_verified_at")
    def normalize_phone_verified_at(cls, v: Optional[str], info):
        data = info.data
        phone = data.get('phone')
        if phone is None:
            return None
        return v


class UserCreate(UserBase):
    name: str = Field(..., max_length=255)
    email: EmailStr
    password: str = Field(..., max_length=50, min_length=8)


class UserVisible(VisibleBase):
    id: UUID
    name: str
    email: Optional[str] = None
    email_verified_at: Optional[datetime] = Field(None, alias="emailVerifiedAt")

    phone: Optional[str] = None
    phone_verified_at: Optional[datetime] = Field(None, alias="phoneVerifiedAt")

    created_at: datetime = Field(alias="createdAt")
    is_staff: bool = Field(alias='isStaff')
    is_active: bool = Field(alias='isActive')
    user_type: ChoiceBase[UserTypeChoices] = Field(alias="userType")
    external_accounts: List["ExternalAccountVisible"] = Field(None, alias="externalAccounts")
    sessions: List["UserSessionVisible"] = None


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
    with_email: Optional[bool] = Field(False, alias="withEmail")
    name: str = Field(..., alias='name', max_length=255)
    phone: Optional[str] = Field(None, alias='phone', max_length=255)
    email: Optional[EmailStr] = None
    password_confirm: str = Field(..., alias='passwordConfirm', max_length=50, min_length=5)
    password: str = Field(..., max_length=50, min_length=5)
    subscription: Optional[bool] = True
    policy: bool

    @field_validator("phone")
    def validate_phone(cls, v: Optional[str], info):
        values = info.data
        if values.get("with_email") is False and (v is None or v == ""):
            raise ValueError(_('Please provide your phone'))
        return v

    @field_validator("email")
    def validate_email(cls, v: Optional[str], info):
        values = info.data
        if values.get("with_email") is True and (v is None or v == ""):
            raise ValueError(_('Please provide your email'))
        return v

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
            raise ValueError(_('Passwords do not match'))
        return v


class UserSessionVisible(BaseModel):
    id: UUID
    user_id: UUID = Field(alias="userId")
    revoked_at: Optional[datetime] = Field(None, alias="revokedAt")
    expire_at: Optional[datetime] = Field(None, alias="expireAt")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    created_at: datetime = Field(alias="createdAt")
    firebase_device_id: Optional[str] = Field(None, alias="firebaseDeviceId")


class UserSession(BaseModel):
    id: UUID
    name: str
    is_superuser: bool
    is_active: bool
    is_staff: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")
    email_verified_at: Optional[datetime] = Field(alias="emailVerifiedAt")
    phone_verified_at: Optional[datetime] = Field(alias="phoneVerifiedAt")


class ExternalAccountVisible(BaseModel):
    id: int
    user_id: UUID = Field(alias="userId")
    account_id: str = Field(alias="accountId")
    phone: str
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


class PhoneVerify(VisibleBase):
    phone: str
    support_phone: Optional[str] = Field(None, alias="supportPhone")
