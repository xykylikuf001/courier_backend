import pytest
from datetime import timedelta

from starlette import status
from calendar import timegm

from typing import TYPE_CHECKING

from app.conf.config import settings, jwt_settings
from app.utils.datetime.timezone import now
from app.utils.security import lazy_jwt_settings

if TYPE_CHECKING:
    from app.contrib.account.models import User
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_token_api(
        async_client: "AsyncClient",
        app_user: "User",
) -> None:
    data = {
        'username': app_user.email,
        'password': "test_secret",
    }
    response = await async_client.post(f'{settings.API_V1_STR}/auth/get-token/', data=data)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    response = await async_client.post(
        f'{settings.API_V1_STR}/auth/get-token/',
        data={
            'username': "invalid",
            'password': "test_secret",
        }
    )
    result = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result == {
        'detail': [{'input': 'invalid',
                    'loc': ['body', 'username'],
                    'msg': 'Incorrect email or password',
                    'type': 'value_error'}]
    }


@pytest.mark.asyncio
async def test_expired_auth_token_api(
        async_client: "AsyncClient",
        simple_user,
        get_user_session,
) -> None:
    iat = now() - timedelta(days=40)
    expire = iat + timedelta(minutes=jwt_settings.JWT_EXPIRATION_MINUTES)
    user_session = await get_user_session(simple_user)

    payload = {
        'user_id': simple_user.id,
        'aud': jwt_settings.JWT_AUDIENCE,
        'iat': timegm(iat.utctimetuple()),
        "exp": timegm(expire.utctimetuple()),
        'iss': jwt_settings.JWT_ISSUER,
        'jti': user_session.id.hex
    }
    jwt_token = lazy_jwt_settings.JWT_ENCODE_HANDLER(payload)
    headers = {'Authorization': f'Bearer {jwt_token}'}
    response = await async_client.get(f'{settings.API_V1_STR}/auth/me/', headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


