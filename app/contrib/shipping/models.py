from typing import Optional

from sqlalchemy import String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import ChoiceType

from app.db.models import ModelWithMetadataBase
from app.contrib.shipping import ShippingMethodTypeChoices


class ShippingZone(ModelWithMetadataBase):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ShippingMethod(ModelWithMetadataBase):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ShippingMethodTypeChoices] = mapped_column(
        ChoiceType(choices=ShippingMethodTypeChoices, impl=String(30)),
        nullable=False
    )
    shipping_zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('shipping_zone.id', name="fx_sp_m_sp_zone_id", ondelete="CASCADE"),
        nullable=False
    )
    maximum_delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minimum_delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
