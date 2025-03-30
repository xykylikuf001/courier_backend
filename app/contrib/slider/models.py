from typing import Optional
from sqlalchemy import Boolean, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy_utils import ChoiceType

from app.db.models import CreationModificationDateBase, Base
from app.conf import LanguagesChoices


class Slider(CreationModificationDateBase):
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=99)

    file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('file.id', ondelete="RESTRICT", name="fx_slider_file_id"),
        nullable=False, unique=True
    )

    file = relationship(
        "File", lazy='noload', single_parent=True, uselist=False,
    )

    translations = relationship(
        "SliderTranslation",
        lazy='noload',
        viewonly=True,
    )
    current_translation = relationship(
        "SliderTranslation",
        lazy='noload',
        viewonly=True,
        uselist=False,
    )

    @hybrid_property
    def title(self):
        return self.current_translation.title

    @hybrid_property
    def caption(self):
        return self.current_translation.caption

    @hybrid_property
    def locale(self):
        return self.current_translation.locale


class SliderTranslation(Base):
    __tablename__: str = "slider_tr"

    id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey('slider.id', ondelete='CASCADE', name='fx_slider_slider_tr_id'),
        primary_key=True,
        autoincrement=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    caption: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    locale: Mapped[str] = mapped_column(
        ChoiceType(choices=LanguagesChoices, impl=String(10)), primary_key=True, unique=True,
    )
    __table_args__ = (
        UniqueConstraint('id', 'locale', name='ux_slider_tr_id_locale'),
    )
