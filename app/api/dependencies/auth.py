from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenPayload
from app.services.user import UserService


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(lambda: ""),  # OAuth2PasswordBearerから取得するように後で修正
) -> User:
    """
    現在のユーザーを取得する依存関係
    
    Args:
        db: データベースセッション
        token: JWTトークン
        
    Returns:
        User: 現在のユーザー
        
    Raises:
        UnauthorizedException: トークンが無効な場合
    """
    try:
        # トークンが空の場合は認証エラー
        if not token:
            raise UnauthorizedException()
            
        # トークンをデコード
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        
        # トークンタイプとサブジェクトの検証
        if token_data.type != "access" or not token_data.sub:
            raise UnauthorizedException()
            
        # 有効期限の検証はJoseライブラリ内で自動的に行われる
            
    except JWTError:
        raise UnauthorizedException()
        
    # ユーザーの取得
    user = await UserService.get(db, int(token_data.sub))
    if not user:
        raise UnauthorizedException()
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    現在のアクティブなユーザーを取得する依存関係
    
    Args:
        current_user: 現在のユーザー
        
    Returns:
        User: 現在のアクティブなユーザー
        
    Raises:
        ForbiddenException: ユーザーが非アクティブな場合
    """
    if not current_user.is_active:
        raise ForbiddenException(detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    現在のアクティブな管理者ユーザーを取得する依存関係
    
    Args:
        current_user: 現在のアクティブなユーザー
        
    Returns:
        User: 現在のアクティブな管理者ユーザー
        
    Raises:
        ForbiddenException: ユーザーが管理者でない場合
    """
    if not current_user.is_superuser:
        raise ForbiddenException(detail="Not enough permissions")
    return current_user