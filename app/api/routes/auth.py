# app/api/routes/auth.py

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.db.session import get_db
from app.schemas.token import Token, TokenPayload
from app.schemas.user import UserCreate, User
from app.services.user import UserService

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    新規ユーザー登録

    - Pydantic v2 によるバリデーション
    - メールアドレスの一意性チェックとパスワードハッシュ化

    ※ User スキーマ側で computed field "full_name" を出力するために、
       model_config に computed_fields=["full_name"] を設定してください。
    """
    user = await UserService.create(db, user_in)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    ログイン認証とトークン発行

    OAuth2PasswordRequestForm の username フィールドにはメールアドレスを指定してください。
    """
    user = await UserService.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise UnauthorizedException(detail="Incorrect email or password")
    if not user.is_active:
        raise ForbiddenException(detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.id, expires_delta=refresh_token_expires)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    リフレッシュトークンを使用して新規アクセストークンを発行

    - refresh_token の検証
    - ユーザー存在およびアクティブ状態の確認
    - 新たに「iat」を含むアクセストークンとリフレッシュトークンの発行
    """
    try:
        payload = decode_token(refresh_token)
        token_data = TokenPayload(**payload)
        if token_data.type != "refresh":
            raise UnauthorizedException(detail="Invalid token type")
        user_id = int(token_data.sub)
    except (JWTError, ValueError):
        raise UnauthorizedException(detail="Invalid refresh token")
    
    user = await UserService.get(db, user_id)
    if not user:
        raise UnauthorizedException(detail="User not found")
    if not user.is_active:
        raise ForbiddenException(detail="Inactive user")
    
    new_access_token = create_access_token(user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    new_refresh_token = create_refresh_token(user.id, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/password-reset-request", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_request(
    email: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    パスワードリセットリクエスト

    ユーザー存在の確認のみ行い、実際のメール送信ロジックは未実装です。
    """
    user = await UserService.get_by_email(db, email)
    if user:
        reset_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(hours=1),
        )
        # ここにメール送信ロジックを実装してください
        pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    パスワードリセットの実行

    トークンを検証し、新しいパスワードに更新します。
    """
    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        user_id = int(token_data.sub)
    except (JWTError, ValueError):
        raise UnauthorizedException(detail="Invalid token")
    
    user = await UserService.get(db, user_id)
    if not user:
        raise UnauthorizedException(detail="User not found")
    
    await UserService.update(db, user, {"password": new_password})
    return Response(status_code=status.HTTP_204_NO_CONTENT)