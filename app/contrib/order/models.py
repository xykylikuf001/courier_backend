from uuid import UUID

from sqlalchemy_utils import ChoiceType
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as SUUID

from app.db.models import CreationModificationDateBase, ModelWithMetadataBase, UUIDBase
from app.contrib.order import OrderStatus


class Order(CreationModificationDateBase, ModelWithMetadataBase, UUIDBase):
    status: Mapped[OrderStatus] = mapped_column(
        ChoiceType(choices=OrderStatus, impl=String(50)),
        nullable=False,
        default=OrderStatus.pending
    )

    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_order_user_id'),
        nullable=False,
    )

    address: Mapped[int] = mapped_column(Integer, ForeignKey(

    ), nullable=False)
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)

    note: Mapped[str] = mapped_column(Text, nullable=False, default="")



class Invoice(CreationModificationDateBase, ModelWithMetadataBase):
    user_id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE', name='fx_order_user_id'),
        nullable=False,
    )
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
