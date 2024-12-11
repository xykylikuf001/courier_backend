from sqlalchemy import UniqueConstraint, String, Boolean, ForeignKey, Integer, Column
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy_utils import ChoiceType

from app.conf import LanguagesChoices
from app.db.models import SlugBase, Base
from app.contrib.location import PlaceLevelChoices
from app.db.mptt import BaseNestedSets


class Place(SlugBase, BaseNestedSets):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("place.id", ondelete="CASCADE"), nullable=True)

    location_level: Mapped[PlaceLevelChoices] = mapped_column(
        ChoiceType(choices=PlaceLevelChoices, impl=String(8)), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    translations = relationship(
        "PlaceTranslation",
        lazy='noload',
        viewonly=True,
    )
    current_translation = relationship(
        "PlaceTranslation",
        lazy='noload',
        viewonly=True,
        uselist=False,
    )

    @hybrid_property
    def name(self):
        return self.current_translation.name

    @hybrid_property
    def full_name(self):
        return self.current_translation.full_name

    @hybrid_method
    def get_display_name(self):
        # path_to_root = self.path_to_root()
        # return ', '.join([f'{place.name} {place.location_level.label}' for place in path_to_root])
        return f'{self.name} {self.location_level.label}'

    @hybrid_property
    def locale(self):
        return self.current_translation.locale


class PlaceTranslation(Base):
    __tablename__ = 'place_tr'

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey('place.id', ondelete='CASCADE', name='fx_place_tr_place_id'),
        primary_key=True, autoincrement=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    translation_parent = relationship(
        'Place',
        uselist=False,
        viewonly=True
    )

    locale: Mapped[str] = mapped_column(
        ChoiceType(choices=LanguagesChoices, impl=String(10)),
        primary_key=True,
    )

    __table_args__ = (
        UniqueConstraint('id', 'locale', name='ux_place_tr_id'),
    )

    def __repr__(self):
        return "<Node (%s)>" % self.id
