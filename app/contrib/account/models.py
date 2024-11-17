from uuid import UUID
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as SUUID
from sqlalchemy_utils import ChoiceType
from app.contrib.account import ServiceTypeChoices, UserType
from app.db.models import CreationModificationDateBase, UUIDBase, ModelWithMetadataBase


class User(UUIDBase, CreationModificationDateBase):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    user_type: Mapped[UserType] = mapped_column(
        ChoiceType(choices=UserType, impl=String(25)),
        nullable=False, default=UserType.user
    )


class UserSession(UUIDBase, CreationModificationDateBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_session_user_id')
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class ExternalAccount(CreationModificationDateBase, ModelWithMetadataBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_ext_acc_user_id'),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserAddress(CreationModificationDateBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_u_address_user_id'),
        nullable=False,
    )
    place_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("place.id", ondelete="RESTRICT", name="fx_u_address_place_id")
    )
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
