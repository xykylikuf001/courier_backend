from datetime import timedelta

import asyncio
import pytest

from typing import Optional, Callable, TYPE_CHECKING, Generator, Any, Iterator

from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport

from app.contrib.account.repository import user_repo, user_session_repo

from app.utils.security import lazy_jwt_settings
from app.main import app

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from fastapi import FastAPI
    from app.contrib.account.models import User, UserSession


# def _event_loop() -> Iterator[asyncio.AbstractEventLoop]:
#     """Yield an event loop.
#     This is necessary because pytest-asyncio needs an event loop with a with an equal or higher
#     pytest fixture scope as any of the async fixtures. And remember, pytest-asyncio is what allows us
#     to have async pytest fixtures.
#     """
#     loop = asyncio.get_event_loop()
#     yield loop
#     loop.close()


# event_loop = pytest.fixture(fixture_function=_event_loop, scope='session', name="event_loop")


@pytest.fixture(scope="session")
async def async_db():
    from app.db.session import AsyncTestingSessionLocal, test_async_engine
    from app.db.init_db import init_db
    from app.db.models import metadata
    from sqlalchemy_utils import database_exists, create_database, drop_database

    database_url = test_async_engine.url.render_as_string(hide_password=False).replace('+asyncpg', '')
    if not database_exists(database_url):
        create_database(database_url)
    # connect to the database
    is_echo = test_async_engine.echo
    test_async_engine.echo = False
    async with test_async_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)  # Create the tables.
    test_async_engine.echo = is_echo

    async with test_async_engine.connect() as conn:
        async with AsyncTestingSessionLocal(bind=conn) as session:
            await init_db(session)
            yield session

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        # await conn.rollback()

    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await test_async_engine.dispose()

    # Drop test database
    if database_exists(database_url):
        drop_database(database_url)


@pytest.fixture
def test_db():
    """
    Creates a fresh sqlalchemy session for each test that operates in a
    transaction. The transaction is rolled back at the end of each test ensuring
    a clean state.
    """
    from app.db.session import TestingSessionLocal, testing_engine
    from app.db.init_db import init_db_sync
    from app.db.models import metadata
    from sqlalchemy_utils import database_exists, create_database, drop_database
    if not database_exists(testing_engine.url):
        create_database(testing_engine.url)

    # connect to the database
    is_echo = testing_engine.echo
    testing_engine.echo = False
    metadata.create_all(bind=testing_engine)
    testing_engine.echo = is_echo

    # connect to the database
    connection = testing_engine.connect()
    # begin a non-ORM transaction
    transaction = connection.begin()
    # bind an individual Session to the connection
    session = TestingSessionLocal(bind=connection)
    init_db_sync(session)
    yield session  # use the session in tests.
    session.close()
    # rollback - everything that happened with the
    # Session above (including calls to commit())
    # is rolled back.
    transaction.rollback()
    # return connection to the Engine
    connection.close()
    if database_exists(testing_engine.url):
        drop_database(testing_engine.url)


@pytest.fixture
def get_user(async_db: "AsyncSession"):
    async def func(email: Optional[str] = None, **kwargs):
        if not email:
            email = 'user@example.com'
        db_obj = await user_repo.first(async_db=async_db, params={'email': email})
        if not db_obj:
            db_obj = await user_repo.create(
                async_db=async_db,
                obj_in={
                    "name": "user",
                    'email': email,
                    'password': 'test_secret',
                    'is_active': True,
                    **kwargs,
                }
            )
        return db_obj

    return func


@pytest.fixture
async def app_user(get_user):
    return await get_user(email='user@example.com')


@pytest.fixture
async def staff_user(get_user):
    return await get_user(email='staff_user@example.com', is_staff=True)


@pytest.fixture
def get_user_session(async_db: "AsyncSession") -> Callable:
    async def func(user: "User") -> "UserSession":
        return await user_session_repo.create(async_db=async_db, obj_in={'user_id': user.id})

    return func


@pytest.fixture
def get_user_token_headers() -> Callable:
    def func(user: "User", expires_delta: Optional[timedelta] = None) -> dict:
        payload = lazy_jwt_settings.JWT_PAYLOAD_HANDLER(
            {'user_id': str(user.id), "email": user.email, 'aud': lazy_jwt_settings.JWT_AUDIENCE},
            expires_delta=expires_delta
        )
        jwt_token = lazy_jwt_settings.JWT_ENCODE_HANDLER(payload)
        return {'Authorization': f'Bearer {jwt_token}'}

    return func


@pytest.fixture
def user_token_headers(app_user, get_user_token_headers) -> dict:
    """
    Retrieve user token auth header
    :param app_user:
    :param get_user_token_headers:
    :return: dict
    """
    return get_user_token_headers(app_user)


@pytest.fixture
def staff_token_headers(staff_user, get_user_token_headers) -> dict:
    """
    Retrieve user token auth header
    :param staff_user:
    :param get_user_token_headers:
    :return: dict
    """
    return get_user_token_headers(staff_user)


@pytest.fixture(autouse=True)
async def application() -> Generator["FastAPI", Any, None]:
    yield app


@pytest.fixture
async def async_client(
        application: "FastAPI", async_db: "AsyncSession",
) -> Generator[AsyncClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db` fixture to override
    the `get_db` dependency that is injected into routes.
    """
    from app.routers import dependency

    async def _get_test_async_db():
        return async_db

    application.dependency_overrides[dependency.get_async_db] = _get_test_async_db

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as _client:
            try:
                yield _client
            except Exception as exc:  # pylint: disable=broad-except
                print(exc)
