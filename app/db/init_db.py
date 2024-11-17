from typing import TYPE_CHECKING
from loguru import logger

from app.conf.config import settings
from app.contrib.account.repository import user_repo_sync, user_repo

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session


def init_db_sync(db: "Session"):
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    user = user_repo_sync.first(db, params={'email': settings.FIRST_SUPERUSER_EMAIL})
    if not user:
        user_in = {
            'name': "admin",
            'email': settings.FIRST_SUPERUSER_EMAIL,
            'password': settings.FIRST_SUPERUSER_PASSWORD,
            'is_active': True,
            "is_superuser": True,
            "is_staff": False,
            "user_type": "staff"
        }
        user = user_repo_sync.create(db, obj_in=user_in)  # noqa: F841
        logger.info("User successfully created")


async def init_db(async_db: "AsyncSession"):
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    user = await user_repo.first(async_db, params={'email': settings.FIRST_SUPERUSER_EMAIL})
    if not user:
        user_in = {
            'name': "admin",
            'email': settings.FIRST_SUPERUSER_EMAIL,
            'password': settings.FIRST_SUPERUSER_PASSWORD,
            'is_active': True,
            "is_superuser": True,
            "user_type": "staff"
        }
        user = await user_repo.create(async_db, obj_in=user_in)  # noqa: F841
        logger.info("User successfully created")
