from datetime import datetime
from pydantic import Field

from app.core.schema import VisibleBase


class NotificationVisible(VisibleBase):
    id: int
    title: str
    body: str
    plain_body: str = Field(alias="plainBody")
    created_at: datetime = Field(alias="createdAt")
