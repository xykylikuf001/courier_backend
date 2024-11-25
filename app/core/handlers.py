from typing import TYPE_CHECKING
from fastapi.responses import ORJSONResponse
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.encoders import jsonable_encoder
if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError, HTTPException

    from .exceptions import DocumentRawNotFound


async def request_document_raw_not_found_exception(request: "Request", exc: "DocumentRawNotFound"):
    return ORJSONResponse(status_code=HTTP_404_NOT_FOUND, content={"detail": str(exc)})


async def request_validation_error(request: "Request", exc: "RequestValidationError"):
    errors = exc.errors()
    print(errors)
    return ORJSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": jsonable_encoder(errors)})


async def request_http_exception_error(request: "Request", exc: "HTTPException"):
    errors = exc
    print(errors)
    return ORJSONResponse(status_code=400, content={"detail": str(exc.detail)})
