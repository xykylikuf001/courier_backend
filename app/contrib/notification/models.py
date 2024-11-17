from uuid import UUID
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as SUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import CreationModificationDateBase


class Notification(CreationModificationDateBase):
    user: Mapped[Optional[UUID]] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey("user.id", name='fx_notification_user_id', ondelete="CASCADE"),
        nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    plain_body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

