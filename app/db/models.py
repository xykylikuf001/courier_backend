import re
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4, UUID

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, declared_attr, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as SUUID
from sqlalchemy.ext.hybrid import hybrid_method

metadata = sa.MetaData()


class UnMapped:
    __allow_unmapped__ = True


PlainBase = declarative_base(metadata=metadata, cls=UnMapped)


class Base(PlainBase):
    __name__: str
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        pattern = re.compile(r'(?<!^)(?=[A-Z])')
        return pattern.sub('_', cls.__name__).lower()


class UUIDBase(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(
        SUUID(as_uuid=True), unique=True, primary_key=True, index=True, default=uuid4,
        nullable=False)


class SlugBase(Base):
    __abstract__ = True
    slug: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True, nullable=False)


class CreationModificationDateBase(Base):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), onupdate=func.now(),
        nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True))


class PublishableModelBase(Base):
    __abstract__ = True

    publication_date: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_published: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    @hybrid_property
    def is_visible(self) -> bool:
        return self.is_published and (
                self.publication_date is None
                or self.publication_date <= datetime.today()
        )


class SeoModelBase(Base):
    __abstract__ = True
    seo_title: Mapped[str] = mapped_column('seo_title', sa.String(255), default='')
    seo_description: Mapped[str] = mapped_column('seo_description', sa.String(255), default='')
    seo_keywords: Mapped[str] = mapped_column('seo_keywords', sa.String(500), default='')


class ModelWithMetadataBase(Base):
    __abstract__ = True
    private_metadata: Mapped[dict] = mapped_column(sa.JSON, default={}, nullable=False)
    public_metadata: Mapped[dict] = mapped_column(sa.JSON, default={}, nullable=False)

    @hybrid_method
    def get_value_from_private_metadata(self, key: str, default: Any = None) -> Any:
        return self.private_metadata.get(key, default)

    @hybrid_method
    def store_value_in_private_metadata(self, items: dict):
        if not self.private_metadata:
            self.private_metadata = {}
        self.private_metadata.update(items)

    @hybrid_method
    def clear_private_metadata(self):
        self.private_metadata = {}

    @hybrid_method
    def delete_value_from_private_metadata(self, key: str):
        if key in self.private_metadata:
            del self.private_metadata[key]

    @hybrid_method
    def get_value_from_metadata(self, key: str, default: Any = None) -> Any:
        return self.public_metadata.get(key, default)

    @hybrid_method
    def store_value_in_metadata(self, items: dict):
        if not self.public_metadata:
            self.public_metadata = {}
        self.public_metadata.update(items)

    @hybrid_method
    def clear_metadata(self):
        self.public_metadata = {}

    @hybrid_method
    def delete_value_from_metadata(self, key: str):
        if key in self.public_metadata:
            del self.public_metadata[key]
