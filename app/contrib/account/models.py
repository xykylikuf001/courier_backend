from uuid import UUID
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as SUUID
from sqlalchemy_utils import ChoiceType

from app.contrib.account import ServiceTypeChoices, UserTypeChoices
from app.db.models import CreationModificationDateBase, UUIDBase, ModelWithMetadataBase


class User(UUIDBase, CreationModificationDateBase):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    phone: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_type: Mapped[UserTypeChoices] = mapped_column(
        ChoiceType(choices=UserTypeChoices, impl=String(25)),
        nullable=False, default=UserTypeChoices.user
    )

    sessions = relationship("UserSession", lazy="noload")


class UserSession(UUIDBase, CreationModificationDateBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_session_user_id')
    )
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    firebase_device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class ExternalAccount(CreationModificationDateBase, ModelWithMetadataBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_ext_acc_user_id'),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    username: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    service_type: Mapped[ServiceTypeChoices] = mapped_column(
        ChoiceType(choices=ServiceTypeChoices, impl=String(50)), nullable=False
    )


class UserPhone(CreationModificationDateBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_up_user_id'),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(String(255), nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Address(CreationModificationDateBase, ModelWithMetadataBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_u_address_user_id'),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    street_address_1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    street_address_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    place_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("place.id", ondelete="RESTRICT", name="fx_u_address_place_id")
    )
    phone: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
