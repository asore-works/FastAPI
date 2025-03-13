from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class AppException(HTTPException):
    """
    アプリケーション全体で使用するカスタムHTTPException基底クラス
    Pydantic v2と連携するようデザインされています
    """
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(AppException):
    """
    リソースが見つからない場合のエラー
    """
    def __init__(
        self,
        detail: Any = "Resource not found",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
        )


class BadRequestException(AppException):
    """
    リクエストが不正な場合のエラー
    """
    def __init__(
        self,
        detail: Any = "Bad request",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
        )


class UnauthorizedException(AppException):
    """
    認証エラー
    """
    def __init__(
        self,
        detail: Any = "Not authenticated",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer", **(headers or {})},
        )


class ForbiddenException(AppException):
    """
    アクセス権限がない場合のエラー
    """
    def __init__(
        self,
        detail: Any = "Not enough permissions",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
        )


class ConflictException(AppException):
    """
    リソースの競合エラー（例：既に存在するメールアドレスでの登録）
    """
    def __init__(
        self,
        detail: Any = "Resource conflict",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
        )


class ServerException(AppException):
    """
    サーバー内部エラー
    """
    def __init__(
        self,
        detail: Any = "Internal server error",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
        )