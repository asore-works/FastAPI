# app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# パスワードハッシュ化のためのパスワードコンテキスト
# bcryptを使用（安全で広く利用されている）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    アクセストークン（JWT）の生成
    
    Args:
        subject: トークンのサブジェクト（通常はユーザーID）
        expires_delta: トークンの有効期限
        
    Returns:
        str: 生成されたJWTトークン
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    iat = datetime.now(timezone.utc)
    
    # トークンのペイロード
    to_encode = {"exp": expire, "iat": iat, "sub": str(subject), "type": "access"}
    
    # JWTの生成
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    リフレッシュトークン（JWT）の生成
    
    Args:
        subject: トークンのサブジェクト（通常はユーザーID）
        expires_delta: トークンの有効期限
        
    Returns:
        str: 生成されたJWTトークン
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    iat = datetime.now(timezone.utc)
    
    # リフレッシュトークン用のペイロード
    to_encode = {"exp": expire, "iat": iat, "sub": str(subject), "type": "refresh"}
    
    # JWTの生成
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文パスワードとハッシュ化されたパスワードを検証
    
    Args:
        plain_password: 平文パスワード
        hashed_password: ハッシュ化されたパスワード
        
    Returns:
        bool: パスワードが一致する場合True
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化
    
    Args:
        password: 平文パスワード
        
    Returns:
        str: ハッシュ化されたパスワード
    """
    return pwd_context.hash(password)


def decode_token(token: str) -> Dict[str, Any]:
    """
    JWTトークンをデコードしてペイロードを取得
    
    Args:
        token: JWTトークン
        
    Returns:
        Dict[str, Any]: トークンのペイロード
    """
    return jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ALGORITHM]
    )