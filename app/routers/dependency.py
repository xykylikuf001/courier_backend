import json

from typing import Generator, Optional

from fastapi import Depends, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.security import lazy_jwt_settings, OAuth2PasswordBearerWithCookie
from app.conf.config import settings
from app.contrib.account.schema import TokenPayload, UserSession

from app.contrib.account.repository import user_repo, user_session_repo
from app.core.exceptions import HTTPUnAuthorized, HTTPInvalidToken, HTTPPermissionDenied
from app.core.schema import CommonsModel
from app.utils.jose import jwt
from app.db.session import AsyncSessionLocal, SessionLocal
from app.conf import LanguagesChoices

# from app.utils.translation import gettext as _
reusable_oauth2 = OAuth2PasswordBearerWithCookie(tokenUrl=f'{settings.API_V1_STR}/auth/get-token/', auto_error=False)


async def get_redis(request: Request):
    return request.app.redis_instance


async def get_aioredis(request: Request):
    return request.app.aioredis_instance


def get_db() -> Generator:
    try:
        with SessionLocal() as session:
            yield session
    finally:
        session.close()


async def get_async_db() -> Generator:
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        await session.close()


async def get_token_payload(
        token: Optional[str] = Depends(reusable_oauth2),
) -> TokenPayload:
    if token is None:
        raise HTTPUnAuthorized()
    try:
        payload = lazy_jwt_settings.JWT_DECODE_HANDLER(token)
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as e:
        raise HTTPInvalidToken()
    return token_data


async def get_current_user(
        token_payload: TokenPayload = Depends(get_token_payload),
        async_db: AsyncSession = Depends(get_async_db),
        aioredis_instance=Depends(get_aioredis),
) -> UserSession:
    """
    Get user by token
    :param token_payload:
    :param async_db:
    :param aioredis_instance:
    :return:
    """

    user_cache = await aioredis_instance.get(f'session-{token_payload.user_id}:{token_payload.jti}')
    if not user_cache:
        user_session = await user_session_repo.first(
            async_db=async_db,
            params={'id': token_payload.jti, "revoked_at": None}
        )
        if not user_session:
            raise HTTPUnAuthorized(detail="Token is invalid")
        user = await user_repo.first(async_db=async_db, params={'id': token_payload.user_id})

        if not user:
            raise HTTPInvalidToken(detail="Invalid token")
        user_id = user.id.__str__()
        data = {
            "id": user_id,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at.isoformat(),
            "name": user.name,
            "is_staff": user.is_staff,
            "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
            "email": user.email,
            "phone_verified_at": user.phone_verified_at.isoformat() if user.phone_verified_at else None,
            "phone": user.phone,
        }
        data_dumps = json.dumps(data)
        await aioredis_instance.set(name=f"session-{user_id}:{token_payload.jti.hex}", value=data_dumps, ex=3600)
    else:
        data = json.loads(user_cache)
    user_session = UserSession(
        id=data.get('id'),
        name=data.get('name'),
        username=data.get('username'),
        is_superuser=data.get('is_superuser'),
        is_active=data.get('is_active'),
        is_staff=data.get('is_staff'),
        birthday=data.get('birthday'),
        created_at=data.get('created_at'),
        email=data.get("email"),
        email_verified_at=data.get("email_verified_at"),
        phone=data.get("phone"),
        phone_verified_at=data.get("phone_verified_at")
    )
    return user_session


async def get_active_user(user: UserSession = Depends(get_current_user)) -> UserSession:
    if not user.is_active:
        raise HTTPPermissionDenied(detail="Your account is disabled")
    return user


async def get_staff_user(
        user: UserSession = Depends(get_active_user)
):
    if user.is_superuser or user.is_staff:
        return user
    raise HTTPPermissionDenied(detail="Staff member required")


async def get_commons(
        page: Optional[int] = 1,
        limit: Optional[int] = settings.PAGINATION_MAX_SIZE
) -> CommonsModel:
    """

    Get commons dict for list pagination
    :param limit: Optional[int] = 1
    :param page: Optional[int] = 25
    :return:
    """
    if not page or not isinstance(page, int):
        page = 1
    elif page < 0:
        page = 1
    offset = (page - 1) * limit
    return CommonsModel(
        limit=limit,
        offset=offset,
        page=page,
    )


def get_language(lang: Optional[LanguagesChoices] = None):
    return lang
