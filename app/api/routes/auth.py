from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.schemas.user import Token, UserCreate, User
from app.services.user import UserService

# OAuth2認証
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    新規ユーザー登録
    """
    # ユーザー作成（UserServiceでメールアドレスの重複チェックを行う）
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
    """
    # ユーザー認証
    user = await UserService.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise UnauthorizedException(detail="Incorrect email or password")
    if not user.is_active:
        raise ForbiddenException(detail="Inactive user")
    
    # アクセストークンの有効期限
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # リフレッシュトークンの有効期限
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # トークン生成
    access_token = create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.id, expires_delta=refresh_token_expires)
    
    # レスポンス
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token: str,  # リクエストボディからトークンを取得する予定（OAuth2形式に合わせる予定）
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    リフレッシュトークンを使用して新しいアクセストークンを発行
    """
    # 実装を省略 - トークンの検証、ユーザー取得、新しいトークン発行
    # 今後実装予定
    pass