from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Integer, UniqueConstraint, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import ChoiceType

from app.conf import LanguagesChoices
from app.db.models import Base


class Config(Base):
    support_phone: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    phones: Mapped[List[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, default=[],
    )
    emails: Mapped[List[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, default=[],
    )

    regular_shipping_price: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True), nullable=False
    )
    express_shipping_price: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2, asdecimal=True), nullable=False
    )
    translations = relationship(
        "ConfigTranslation",
        lazy='noload',
        viewonly=True,
    )
    current_translation = relationship(
        "ConfigTranslation",
        lazy='noload',
        viewonly=True,
        uselist=False,
    )

    @hybrid_property
    def site_name(self):
        return self.current_translation.site_name

    @hybrid_property
    def address(self):
        return self.current_translation.address

    @hybrid_property
    def seo_title(self):
        return self.current_translation.seo_title

    @hybrid_property
    def seo_description(self):
        return self.current_translation.seo_description

    @hybrid_property
    def seo_keywords(self):
        return self.current_translation.seo_keywords

    @hybrid_property
    def locale(self):
        return self.current_translation.locale


class ConfigTranslation(Base):
    __tablename__: str = "config_tr"
    id: Mapped[int] = mapped_column(
        Integer(), ForeignKey('config.id', ondelete='CASCADE', name='fx_config_config_tr_id'),
        primary_key=True,
        autoincrement=False,
    )
    site_name: Mapped[str] = mapped_column("site_name", String(255), nullable=False)
    address: Mapped[str] = mapped_column("address", String(255), nullable=False)

    seo_title: Mapped[str] = mapped_column('seo_title', String(255), default='')
    seo_description: Mapped[str] = mapped_column('seo_description', String(255), default='')
    seo_keywords: Mapped[str] = mapped_column('seo_keywords', String(500), default='')

    locale: Mapped[LanguagesChoices] = mapped_column(
        ChoiceType(choices=LanguagesChoices, impl=String(10)), primary_key=True, unique=True)
    __table_args__ = (
        UniqueConstraint('id', 'locale', name='ux_config_tr_id_locale'),
    )

