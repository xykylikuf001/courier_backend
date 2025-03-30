from typing import (
    Generic, Optional, Type, TypeVar, Union, Any, TYPE_CHECKING, Iterable,
    Dict, Sequence
)
from uuid import UUID, uuid4
from sqlalchemy import func, select, text, delete, Select, update
from sqlalchemy.exc import NoResultFound

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.core.exceptions import DocumentRawNotFound
from app.core.enums import Choices
from app.utils.slugify import slugify

from .models import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)
BaseSchemaType = TypeVar("BaseSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


def get_slug_string(obj_in: dict,
                    field_name: Optional[str] = 'slug',
                    from_field: Optional[str] = 'name') -> str:
    slug_in = obj_in.get(field_name)
    if not slug_in:
        slug_in = obj_in.get(from_field)
    assert slug_in is not None, f'"{from_field}" is empty'
    assert isinstance(slug_in, str), f'"{from_field}, is not string type'
    return slugify(slug_in)


def prepare_data_with_slug_sync(
        db: "Session",
        obj_in: dict,
        obj_repo_sync: "CRUDBaseSync",
        db_obj: Optional[ModelType] = None,
        field_name: Optional[str] = 'slug',
        from_field: Optional[str] = 'name'
) -> dict:
    slug_in = get_slug_string(obj_in, field_name, from_field)
    expressions = [obj_repo_sync.model.slug.like(f'{slug_in}%')]
    if db_obj:
        expressions.append(obj_repo_sync.model.id != db_obj.id)
    count = obj_repo_sync.count(db, expressions=expressions)

    if count > 0:
        if len(slug_in) > 222:  # slug string max_length=255, uuid hex length=32; 255-32-1=222
            slug_in = f'{slug_in[0:222:1]}-{uuid4().hex}'
        else:
            slug_in = f'{slug_in}-{uuid4().hex}'
    obj_in[field_name] = slug_in
    return obj_in


async def prepare_data_with_slug(
        async_db: "AsyncSession",
        obj_in: dict,
        obj_repo: "CRUDBase",
        db_obj: Optional[ModelType] = None,
        field_name: Optional[str] = 'slug',
        from_field: Optional[str] = 'name'
) -> dict:
    slug_in = get_slug_string(obj_in, field_name, from_field)
    expressions = [getattr(obj_repo.model, field_name).ilike(f'{slug_in}%')]
    if db_obj:
        expressions.append(obj_repo.model.id != db_obj.id)

    count = await obj_repo.count(async_db, expressions=expressions)

    if count > 0:
        if len(slug_in) > 222:  # slug string max_length=255, uuid hex length=32; 255-32-1=222
            slug_in = f'{slug_in[0:222:1]}-{uuid4().hex}'
        else:
            slug_in = f'{slug_in}-{uuid4().hex}'

    obj_in[field_name] = slug_in

    return obj_in


class CRUDBaseSync(Generic[ModelType]):
    __slots__ = ('model', 'primary_field')

    def __init__(self, model: Type[ModelType], primary_field: Optional[str] = 'id'):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**


        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.primary_field = primary_field

    def first(
            self,
            db: "Session",
            params: Optional[dict] = None,
            options: Optional[Iterable] = None,
            order_by: Optional[Iterable] = None,
            expressions: Optional[Iterable] = None,
    ) -> Optional[ModelType]:
        """
        Soft retrieve obj
        :param db:
        :param params:
        :param options:
        :param order_by:
        :param expressions:
        :return:
        """

        stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        if order_by:
            stmt = stmt.order_by(*order_by)
        return db.execute(stmt).scalars().first()

    def create(self, db: "Session", obj_in: dict) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in, custom_encoder={Choices: lambda x: x.value})
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def count(
            self, db: "Session", *,
            expressions: Optional[list] = None,
            params: Optional[dict] = None,
    ) -> int:
        """

        :param db:
        :param expressions:
        :param params:
        :return:
        """
        if params is None:
            params = {}

        stmt = select(func.count(self.model.id))
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        return db.execute(stmt).scalar_one()

    def exists(
            self, db: "Session",
            expressions: Optional[Iterable] = None,
            params: Optional[dict] = None,
    ) -> Any:
        """
        Check the item exist
        :param db:
        :param expressions:
        :param params:
        :return:
        """
        stmt = select(self.model)
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        return db.execute(select(stmt.exists())).scalar_one()

    def get_all(
            self,
            db: "Session",
            *,
            stmt: Optional[Select] = None,
            offset: int = 0,
            limit: int = 100,
            q: Optional[dict] = None,
            order_by: Optional[Iterable[str]] = None,
            options: Optional[Iterable] = None,
            expressions: Optional[Iterable] = None,
    ) -> Iterable:
        """

        :param db: sqlalchemy.orm.Session
        :param offset:
        :param limit:
        :param q:
        :param order_by:
        :param expressions:
        :param options:
        :return:
        """
        if stmt is None:
            stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        if expressions:
            stmt = stmt.filter(*expressions)
        if q:
            stmt = stmt.filter_by(**q)
        if not order_by:
            sort = (getattr(self.model, self.primary_field).desc(),)
        else:
            sort = tuple(text(f'{i[1:]} DESC') if i.startswith('-') else text(f'{i} ASC') for i in order_by)
        stmt = stmt.order_by(*sort).offset(offset=offset).limit(limit=limit)

        result = db.execute(stmt).scalars().fetchall()
        return result

    def get_by_params(
            self, db: "Session",
            stmt: Optional[Select] = None,
            options: Optional[Iterable] = None,
            expressions: Optional[Iterable] = None,
            params: Optional[dict] = None
    ) -> ModelType:
        """
        Retrieve items by params
        :param db:
        :param options:
        :param expressions:
        :param params:
        :return:
        """
        if not stmt:
            stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        if expressions:
            stmt = stmt.filter(*expressions)
        if paremts:
            stmt = stmt.filter_by(**params)
        result = db.execute(stmt)
        return result.scalar_one()

    def get(
            self,
            db: "Session",
            obj_id: Union[int, UUID],
            options: Optional[Iterable] = ()
    ) -> ModelType:
        """
        Retrieve obj, if does not exist raise exception
        :param db:
        :param obj_id:
        :param options:
        :return:
        """
        result = db.execute(select(self.model).options(*options).where(self.model.id == obj_id))

        return result.scalar_one()

    @staticmethod
    def update(
            db: "Session",
            db_obj: ModelType,
            obj_in: Dict[str, Any],
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj, custom_encoder={Choices: lambda x: x.value})
        obj_in = jsonable_encoder(obj_in, custom_encoder={Choices: lambda x: x.value})
        for field in obj_data:
            if field in obj_in:
                print(field, obj_in[field])
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(
            db: "Session",
            db_obj: ModelType
    ) -> ModelType:
        """
        Delete obj
        :param db_obj:
        :param db:
        :return:
        """
        db.delete(db_obj)
        db.commit()
        return db_obj

    def remove(self, db: "Session", expressions: list):
        statement = delete(self.model).where(*expressions)
        result = db.execute(statement)
        db.commit()
        return result


class CRUDBase(Generic[ModelType]):
    __slots__ = ('model', 'primary_field')

    def __init__(self, model: Type[ModelType], primary_field: Optional[str] = "id"):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**


        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.primary_field = primary_field

    async def count(
            self, async_db: "AsyncSession", *,
            expressions: Optional[list] = None,
            params: Optional[dict] = None,
    ) -> int:
        """

        :param async_db:
        :param expressions:
        :param params:
        :return:
        """

        if params is None:
            params = {}

        stmt = select(func.count(self.model.id))
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        result = await async_db.execute(stmt)
        return result.scalar_one()

    async def exists(
            self, async_db: "AsyncSession", *,

            expressions: Optional[list] = None,
            params: Optional[dict] = None,
    ) -> Any:
        """
        Check the item exist
        :param async_db:
        :param expressions:
        :param params:
        :return:
        """

        stmt = select(self.model)
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        result = await async_db.execute(select(stmt.exists()))
        return result.scalar_one()

    async def get_by_params(
            self,
            async_db: "AsyncSession",
            *,
            stmt: Optional[Select] = None,
            options: Optional[Sequence] = None,
            params: Optional[dict] = None,
            expressions: Optional[Sequence] = None,
            is_scalar: Optional[bool] = True

    ):
        """
        Retrieve items by params
        :param stmt:
        :param async_db:
        :param expressions:
        :param options:
        :param params:
        :param is_scalar:
        :return:

        """
        if stmt is None:
            stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        result = await async_db.execute(stmt)
        try:
            if is_scalar:
                return result.scalar_one()
            return result.one()
        except NoResultFound:
            self.does_not_exist()

    async def first(
            self,
            async_db: "AsyncSession",
            params: Optional[dict] = None,
            options: Optional[Iterable] = None,
            order_by: Optional[Iterable] = None,
            expressions: Optional[Iterable] = None,
    ) -> Optional[ModelType]:
        """
        Soft retrieve obj
        :param async_db:
        :param params:
        :param expressions:
        :param options:
        :param order_by:
        :return:
        """
        stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        if expressions:
            stmt = stmt.filter(*expressions)
        if params:
            stmt = stmt.filter_by(**params)
        if order_by:
            stmt = stmt.order_by(*order_by)

        result = await async_db.execute(stmt)
        return result.scalars().first()

    async def get(
            self,
            async_db: "AsyncSession",
            obj_id: Union[int, UUID],
            options: Optional[Iterable] = None,
    ) -> ModelType:
        """
        Retrieve obj, if it does not exist raise exception
        :param async_db:
        :param options:
        :param obj_id:
        :return:
        """

        stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        result = await async_db.execute(stmt.where(self.model.id == obj_id))
        try:
            return result.scalar_one()
        except NoResultFound:
            self.does_not_exist()

    async def get_all(
            self,
            async_db: "AsyncSession",
            *,
            stmt: Optional[Select] = None,
            offset: int = 0,
            limit: Optional[int] = None,
            q: Optional[dict] = None,
            order_by: Optional[Sequence[str]] = None,
            options: Optional[Sequence] = None,
            expressions: Optional[Sequence] = None,
            is_scalar: Optional[bool] = True
    ) -> Sequence[Any]:
        """

        :param async_db:
        :param stmt: sqlalchemy.Select
        :param offset: int
        :param limit: int
        :param q:
        :param order_by:
        :param options:
        :param expressions:
        :param is_scalar: bool
        :return:
        """
        if stmt is None:
            stmt = select(self.model)
        if options:
            stmt = stmt.options(*options)
        if expressions:
            stmt = stmt.filter(*expressions)
        if q:
            stmt = stmt.filter_by(**q)
        if not order_by:
            sort = (getattr(self.model, self.primary_field).desc(),)
        else:
            sort = tuple(text(f'{i[1:]} DESC') if i.startswith('-') else text(f'{i} ASC') for i in order_by)
        stmt = stmt.order_by(*sort).offset(offset=offset)
        if limit:
            stmt = stmt.limit(limit=limit)
        result = await async_db.execute(stmt)
        if is_scalar:
            return result.scalars().fetchall()
        return result.fetchall()

    async def create(
            self, async_db: "AsyncSession", obj_in: Union[dict, CreateSchemaType],
            commit: Optional[bool] = True,
            flush: Optional[bool] = False,
    ) -> ModelType:
        # obj_in_data = jsonable_encoder(obj_in, custom_encoder={Choices: lambda x: x.value})
        if isinstance(obj_in, dict):
            # obj_in_data = jsonable_encoder(obj_in, custom_encoder={Choices: lambda x: x.value})
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)  # type: ignore
        async_db.add(db_obj)
        if flush:
            await async_db.flush()
        if commit:
            await async_db.commit()
            await async_db.refresh(db_obj)
        return db_obj


    async def update(
            self,
            async_db: "AsyncSession",
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            commit: Optional[bool] = True
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj, custom_encoder={Choices: lambda x: x.value})
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        async_db.add(db_obj)
        if commit:
            await async_db.commit()
            await async_db.refresh(db_obj)
        return db_obj

    async def raw_update(
            self,
            async_db: "AsyncSession",
            expressions: Iterable,
            obj_in: dict
    ):
        stmt = (update(self.model).where(*expressions).values(**obj_in))
        result = await async_db.execute(stmt)
        await async_db.commit()
        return result

    @staticmethod
    async def delete(
            async_db: "AsyncSession",
            db_obj: Union[ModelType]
    ) -> ModelType:
        """
        Delete obj
        :param db_obj:
        :param async_db:
        :return:
        """
        await async_db.delete(db_obj)
        await async_db.commit()
        return db_obj

    async def remove(
            self,
            async_db: "AsyncSession",
            expressions: Iterable
    ):
        statement = delete(self.model).where(*expressions)
        result = await async_db.execute(statement)
        await async_db.commit()
        return result

    def does_not_exist(self):
        raise DocumentRawNotFound(f"No one row found on - {self.model.__name__}")
