from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.conf.config import settings

from .mptt.events import TreesManager
from .mptt.mixins import BaseNestedSets
async_engine = create_async_engine(str(settings.DATABASE_URL), pool_pre_ping=True, echo=False)

db_uri = str(settings.DATABASE_URL).replace('+asyncpg', '')
engine = create_engine(db_uri, pool_pre_ping=True, echo=False)


tree_manager = TreesManager(BaseNestedSets)
tree_manager.register_events()
mptt_session_maker = tree_manager.register_factory

SessionLocal = mptt_session_maker(sessionmaker(
    expire_on_commit=True,
    autocommit=False,
    autoflush=False,
    # twophase=True,
    bind=engine
))

sync_maker = sessionmaker()


AsyncSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    # future=True,
    sync_session_class=sync_maker
)
event.listen(sync_maker, 'after_flush_postexec', tree_manager.after_flush_postexec)


test_db_uri = str(settings.TEST_DATABASE_URL).replace('+asyncpg', '')
testing_engine = create_engine(test_db_uri, pool_pre_ping=True)

test_async_engine = create_async_engine(
    str(settings.TEST_DATABASE_URL), pool_pre_ping=True, echo=False,
)
TestingSessionLocal = mptt_session_maker(sessionmaker(
    expire_on_commit=True,
    # twophase=True,
    autoflush=False,
    autocommit=False,
    bind=testing_engine
))
test_sync_maker = sessionmaker()

AsyncTestingSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    # twophase=True,
    autoflush=False,
    autocommit=False,
    bind=test_async_engine,
    # future=True,
    sync_session_class=test_sync_maker,
    # join_transaction_mode="create_savepoint"
)
event.listen(test_sync_maker, 'after_flush_postexec', tree_manager.after_flush_postexec)

