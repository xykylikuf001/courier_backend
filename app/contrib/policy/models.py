from sqlalchemy import String,  Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import ChoiceType


from app.conf import LanguagesChoices
from app.db.models import Base

class PolicyTranslation(Base):
    __tablename__ = "policy_tr"

    title: Mapped[str] = mapped_column('title', String(255), default='')
    body: Mapped[str] = mapped_column('body', Text, default='')

    locale: Mapped[LanguagesChoices] = mapped_column(
        ChoiceType(choices=LanguagesChoices, impl=String(10)), primary_key=True, unique=True,
    )
