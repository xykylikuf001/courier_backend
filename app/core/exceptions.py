from fastapi import status, HTTPException
from typing import Any, Optional, Dict


class ImproperlyConfigured(Exception):
    """Somehow improperly configured"""
    pass


class HTTPExpiredSignatureError(HTTPException):
    def __init__(
            self,
    ) -> None:
        headers = {"WWW-Authenticate": "Bearer signature_expired"}
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signature expired", headers=headers)


class HTTPInvalidToken(HTTPException):
    def __init__(
            self,
            status_code: int = status.HTTP_401_UNAUTHORIZED,
            detail: Optional[str] = "Invalid token",
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer invalid_token"}
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class HTTPUnAuthorized(HTTPException):
    def __init__(
            self,
            status_code: int = status.HTTP_401_UNAUTHORIZED,
            detail: Optional[str] = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}

        if detail is None:
            detail = "No authorized"

        super().__init__(status_code=status_code, detail=detail, headers=headers)


class HTTPPermissionDenied(HTTPException):
    def __init__(
            self,
            status_code: Optional[int] = status.HTTP_403_FORBIDDEN,
            detail: Optional[str] = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        if detail is None:
            detail = 'Permission denied'
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class HTTP404(HTTPException):
    def __init__(
            self,
            status_code: Optional[int] = status.HTTP_404_NOT_FOUND,
            detail: Optional[str] = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if detail is None:
            detail = "Does not exist"
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class DocumentRawNotFound(Exception):
    pass
