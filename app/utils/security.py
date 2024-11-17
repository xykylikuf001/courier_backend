import os
import json
import random

from typing import Optional, Dict
from datetime import datetime, timedelta

from calendar import timegm
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from passlib.context import CryptContext
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.encoders import jsonable_encoder

from app.conf.config import jwt_settings, structure_settings
from app.utils.jose import jwt

from .import_utils import perform_import

__all__ = (
    'jwt_payload', 'jwt_encode', 'jwt_decode', 'verify_password', 'get_password_hash',
    'generate_rsa_certificate', 'lazy_jwt_settings', 'OAuth2PasswordBearerWithCookie'
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

IMPORT_STRINGS = (
    'JWT_PASSWORD_VERIFY',
    'JWT_PASSWORD_HANDLER',
    'JWT_ENCODE_HANDLER',
    'JWT_DECODE_HANDLER',
    'JWT_PAYLOAD_HANDLER',
)


def jwt_payload(data: dict, expires_delta: Optional[timedelta] = None) -> dict:
    iat = datetime.utcnow()
    if expires_delta:
        expire = iat + expires_delta
    else:
        expire = iat + timedelta(minutes=jwt_settings.JWT_EXPIRATION_MINUTES)
    payload = data.copy()
    payload.update(
        {
            'iat': timegm(iat.utctimetuple()),
            "exp": timegm(expire.utctimetuple()),
            'iss': jwt_settings.JWT_ISSUER
        }
    )
    return payload


def jwt_encode(payload) -> str:
    return jwt.encode(
        jsonable_encoder(payload),
        jwt_settings.JWT_PRIVATE_KEY or jwt_settings.JWT_SECRET_KEY,
        jwt_settings.JWT_ALGORITHM,
    )


def jwt_decode(
        token, issuer: Optional[str] = jwt_settings.JWT_ISSUER,
        audience: Optional[str] = jwt_settings.JWT_AUDIENCE,
) -> dict:
    return jwt.decode(
        token=token,
        key=jwt_settings.JWT_PUBLIC_KEY or jwt_settings.JWT_SECRET_KEY,
        algorithms=[jwt_settings.JWT_ALGORITHM],
        options={
            'verify_signature': jwt_settings.JWT_VERIFY,
            'verify_exp': jwt_settings.JWT_VERIFY_EXPIRATION,
            "verify_jti": True,
            'leeway': jwt_settings.JWT_LEEWAY,
            'require_exp': True,
            "require_jti": False,
        },
        audience=audience,
        issuer=issuer,
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_rsa_certificate():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    private_key_str = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()

    public_key_str = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    secrets: dict = {
        'private_key': private_key_str.decode("utf-8"),
        'public_key': public_key_str.decode("utf-8")
    }

    path = os.path.join(structure_settings.PROJECT_DIR, 'conf', 'secrets.json')

    with open(path, 'w') as f:
        f.write(json.dumps(secrets, sort_keys=True))

    return secrets


class JWTSettings:
    def __init__(self, defaults, import_strings):
        self.defaults = defaults
        self.import_strings = import_strings
        self._cached_attrs = set()

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError('Invalid setting: `{}`'.format(attr))

        value = self.defaults.get(attr, self.defaults[attr])

        if attr in self.import_strings:
            value = perform_import(value, attr)

        self._cached_attrs.add(attr)
        setattr(self, attr, value)
        return value

    @property
    def user_settings(self):
        return self._user_settings

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)

        self._cached_attrs.clear()

        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


lazy_jwt_settings = JWTSettings(jwt_settings.model_dump(), IMPORT_STRINGS)


class OAuth2PasswordBearerWithCookie(OAuth2):
    __hash__ = lambda obj: id(obj)

    def __init__(
            self,
            tokenUrl: str,
            scheme_name: Optional[str] = None,
            scopes: Optional[Dict[str, str]] = None,
            description: Optional[str] = None,
            auto_error: Optional[bool] = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")
        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )
        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param
        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param
        else:
            authorization = False
            scheme = ''
            param = None

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


def rand_code(length: int):
    # Takes random choices from
    # ascii_letters and digits
    # generated_code = ''.join([random.choice(string.digits) for n in range(length)])

    random_number = random.randint(1, 10 ** length - 1)
    string_format = '{:0' + str(length) + '}'
    return string_format.format(random_number)
