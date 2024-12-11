import uvicorn
import redis

from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from pydantic import BaseModel

from app import __VERSION__
from app.conf.config import settings
from app.core.exceptions import DocumentRawNotFound
from app.core.handlers import request_document_raw_not_found_exception, request_http_exception_error
from app.core.app import FastAPI
from app.utils.translation import load_gettext_translations
from app.utils.translation.middleware import (
    LocaleFromHeaderMiddleware,
    LocaleFromCookieMiddleware,
    LocaleFromQueryParamsMiddleware
)
from app.routers.urls import router
from app.routers.api import api
from app.routers.dependency import get_locale
from app.core.handlers import request_validation_error

class HTTPExceptionModel(BaseModel):
    detail: Optional[str] = None


def custom_generate_unique_id(route: APIRoute):
    return route.name



def get_application(
        app_router: APIRouter,
        app_api: APIRouter,
        root_path: Optional[str] = None,
        root_path_in_servers: Optional[bool] = False,
        openapi_url: Optional[str] = "/openapi.json",
        api_prefix: Optional[str] = ''
) -> FastAPI:
    load_gettext_translations(directory=settings.LOCALE_PATH, domain='messages')

    application = FastAPI(
        dependencies=[Depends(get_locale)],
        default_response_class=ORJSONResponse,
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version=__VERSION__,
        openapi_url=openapi_url,
        root_path=root_path,
        root_path_in_servers=root_path_in_servers,
        generate_unique_id_function=custom_generate_unique_id,
        responses={
          400: {"model": HTTPExceptionModel},
        },
        exception_handlers={
            HTTPException: request_http_exception_error,
            DocumentRawNotFound: request_document_raw_not_found_exception,
            RequestValidationError: request_validation_error,
        },

        middleware=[
            Middleware(
                LocaleFromHeaderMiddleware,
                language_header=settings.LANGUAGE_HEADER,
                default_code=settings.LANGUAGE_CODE
            ),
            # Middleware(LocaleFromCookieMiddleware, language_cookie=settings.LANGUAGE_COOKIE),
            # Middleware(LocaleFromQueryParamsMiddleware),
        ],
    )
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @application.on_event('startup')
    async def startup():
        redis_instance = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf8",
        )
        aioredis_instance = redis.asyncio.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf8",
        )
        application.configure(
            redis_instance=redis_instance,
            aioredis_instance=aioredis_instance,
        )

    application.mount("/static", StaticFiles(directory="static", html=True), name="static")
    application.mount("/media", StaticFiles(directory="media", html=True), name="media")
    application.include_router(app_api, prefix=api_prefix)
    application.include_router(app_router)

    return application


app = get_application(
    root_path=settings.ROOT_PATH,
    root_path_in_servers=settings.ROOT_PATH_IN_SERVERS,
    openapi_url=settings.OPENAPI_URL,
    app_router=router,
    app_api=api,
    api_prefix=settings.API_V1_STR,
)

if __name__ == "__main__":
    # noinspection PyTypeChecker
    uvicorn.run(
        get_application(
            root_path=settings.ROOT_PATH,
            root_path_in_servers=settings.ROOT_PATH_IN_SERVERS,
            openapi_url=settings.OPENAPI_URL,
            app_router=router,
            app_api=api,
        ),
        host="0.0.0.0", port=8000
    )
