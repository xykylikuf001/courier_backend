from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy_utils import ChoiceType

from app.db.models import Base
from app.contrib.contact import ContactTypeChoices, SectionChoices


class Contact(Base):
    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_type: Mapped[ContactTypeChoices] = mapped_column(
        ChoiceType(choices=ContactTypeChoices, impl=String(25)), nullable=False, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)

