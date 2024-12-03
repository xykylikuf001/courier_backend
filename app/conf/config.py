from typing import List, Optional, Union
from pathlib import Path
from pydantic import EmailStr, field_validator, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Dirs
    BASE_DIR: Optional[str] = Path(__file__).resolve().parent.parent.parent.as_posix()
    PROJECT_DIR: Optional[str] = Path(__file__).resolve().parent.parent.as_posix()
    # Project
    DEBUG: Optional[bool] = False
    PAGINATION_MAX_SIZE: Optional[int] = 25

    DOMAIN: Optional[str] = 'localhost:8000'
    ENABLE_SSL: Optional[bool] = False
    SITE_URL: Optional[str] = 'http://localhost'
    ROOT_PATH: Optional[str] = ""
    ROOT_PATH_IN_SERVERS: Optional[bool] = True
    OPENAPI_URL: Optional[str] = '/openapi.json'

    API_V1_STR: Optional[str] = "/api/v1"

    SERVER_NAME: Optional[str] = 'localhost'
    SERVER_HOST: Optional[str] = 'http://localhost:8000'
    IMAGE_HOST: Optional[str] = 'http://localhost:8000'
    BACKEND_CORS_ORIGINS: Optional[List[str]] = []

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: Optional[str] = 'project_name'

    DATABASE_HOST: Optional[str] = "127.0.0.1"
    DATABASE_PORT: Optional[int] = 5432
    DATABASE_USER: Optional[str] = "change_this"
    DATABASE_PASSWORD: Optional[str] = "change_this"
    DATABASE_NAME: Optional[str] = "change_this"
    DATABASE_URL: Optional[PostgresDsn] = None
    TEST_DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL")
    def assemble_db_connection(cls, v: Optional[str], info):
        if isinstance(v, str):
            return v
        values = info.data
        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            host=values.get("DATABASE_HOST"),
            username=values.get("DATABASE_USER"),
            port=values.get("DATABASE_PORT"),
            password=values.get("DATABASE_PASSWORD"),
            path=f"{values.get('DATABASE_NAME') or ''}",
        )

    @field_validator("TEST_DATABASE_URL")
    def assemble_test_db_connection(cls, v: Optional[str], info):
        if isinstance(v, str):
            return v
        values = info.data

        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            host=values.get("DATABASE_HOST"),
            username=values.get("DATABASE_USER"),
            password=values.get("DATABASE_PASSWORD"),
            path='test',
        )

    REDIS_HOST: Optional[str] = '127.0.0.1'
    REDIS_PORT: Optional[int] = 6379
    REDIS_URL: Optional[RedisDsn] = None

    @field_validator('REDIS_URL')
    def assemble_redis_url(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        data = info.data
        return f'redis://{data.get("REDIS_HOST")}:{data.get("REDIS_PORT")}/0'

    SMTP_TLS: Optional[bool] = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = 'smtp.server.example'
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = "Mailer"

    VERIFICATION_CODE_EXPIRE_SECONDS: Optional[int] = 1800
    VERIFICATION_CODE_LENGTH: Optional[int] = 6
    EMAIL_TEMPLATES_DIR: Optional[str] = "app/email-templates/build"
    EMAILS_ENABLED: Optional[bool] = True

    FIRST_SUPERUSER_EMAIL: Optional[str] = 'admin@example.com'
    FIRST_SUPERUSER_PASSWORD: Optional[str] = 'change_this'

    DEFAULT_CURRENCY: Optional[str] = "TMT"

    LOCALE_PATH: Optional[str] = 'app/locale'
    USE_I18N: Optional[bool] = True
    LANGUAGE_HEADER: Optional[str] = "Accept-Language"
    LANGUAGE_COOKIE: Optional[str] = "Language"
    TIME_ZONE: Optional[str] = 'Asia/Ashgabat'
    USE_TZ: Optional[bool] = True
    LANGUAGES: tuple = (("en", "en"), ("ru", "ru"),("tk", "tk"))
    LANGUAGE_CODE: Optional[str] = 'tk'
    LANGUAGE_CODE_LENGTH: Optional[int] = 5

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding='utf-8',
        extra="ignore"
    )

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = "http://localhost:8000/auth/google"


class JWTSettings(BaseSettings):
    JWT_SECRET_KEY: Optional[str] = 'change_this'
    JWT_PUBLIC_KEY: Optional[str] = None
    JWT_PRIVATE_KEY: Optional[str] = None
    JWT_ALGORITHM: Optional[str] = "RS256"
    JWT_VERIFY: Optional[bool] = True
    JWT_VERIFY_EXPIRATION: Optional[bool] = True
    JWT_LEEWAY: Optional[int] = 0
    JWT_ARGUMENT_NAME: Optional[str] = 'token'
    JWT_EXPIRATION_MINUTES: Optional[int] = 60 * 24 * 30 * 12
    JWT_ALLOW_REFRESH: Optional[bool] = True
    JWT_REFRESH_EXPIRATION_DAYS: Optional[int] = 365
    JWT_PASSWORD_RESET_EXPIRATION_MINUTES: Optional[int] = 1440

    JWT_AUTH_HEADER_NAME: Optional[str] = 'HTTP_AUTHORIZATION'
    JWT_AUTH_HEADER_PREFIX: str = 'Bearer'
    JWT_AUDIENCE: Optional[str] = 'client'
    JWT_ISSUER: Optional[str] = 'backend'

    # Helper functions
    JWT_PASSWORD_VERIFY: Optional[str] = 'app.utils.security.verify_password'
    JWT_PASSWORD_HANDLER: Optional[str] = 'app.utils.security.get_password_hash'
    JWT_PAYLOAD_HANDLER: Optional[str] = 'app.utils.security.jwt_payload'
    JWT_ENCODE_HANDLER: Optional[str] = 'app.utils.security.jwt_encode'
    JWT_DECODE_HANDLER: Optional[str] = 'app.utils.security.jwt_decode'

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding='utf-8',
        extra="ignore"
    )


class StructureSettings(BaseSettings):
    # Dirs
    BASE_DIR: Optional[str] = Path(__file__).resolve().parent.parent.parent.as_posix()
    PROJECT_DIR: Optional[str] = Path(__file__).resolve().parent.parent.as_posix()
    MEDIA_DIR: Optional[str] = 'media'  # Without end slash
    MEDIA_URL: Optional[str] = '/media/'

    STATIC_DIR: Optional[str] = 'static'
    STATIC_URL: Optional[str] = '/static/'

    TEMPLATES: Optional[dict] = {
        'DIR': 'templates'
    }

    TEMP_PATH: Optional[str] = 'temp/'

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env", env_file_encoding='utf-8',
        extra="ignore"
    )


settings = Settings()
jwt_settings = JWTSettings()
structure_settings = StructureSettings()
