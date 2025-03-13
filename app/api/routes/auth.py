from typing import Any
from datetime import timedelta

from fastapi import APIRouter, Depends, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.schemas.user import Token, UserCreate, User, TokenPayload
from app.services.user import UserService

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    新規ユーザー登録

    - ユーザー情報のバリデーション (Pydantic v2)
    - メールアドレスの一意性チェック
    - パスワードのハッシュ化
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
    OAuth2の標準フローに対応

    注: OAuth2PasswordRequestFormではusernameフィールドにメールアドレスを指定
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
    リフレッシュトークンを使用して新しいアクセストークンを発行

    - リフレッシュトークンの検証
    - 新しいアクセストークンとリフレッシュトークンの発行
    - JWTのセキュリティを確保するためのベストプラクティスを採用
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
    
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


@router.post("/password-reset-request", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_request(
    email: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    パスワードリセットのリクエスト処理

    注: 実装ではユーザーの存在確認のみを行い、実際のメール送信は模擬的に処理
    本番環境では実際のメール送信機能との連携が必要
    """
    user = await UserService.get_by_email(db, email)
    
    if user:
        reset_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(hours=1),
        )
        # ここでメール送信のロジックを実装する
        # 例: await send_reset_password_email(email=user.email, token=reset_token)
        pass
    
    # 204 No Content を Response オブジェクトで明示的に返す
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    パスワードリセットの実行

    トークンを検証し、新しいパスワードに更新
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