# app/core/auth.py

"""
共通認証ユーティリティモジュール
循環インポートを避けるための共有コンポーネント
"""
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

# OAuth2認証スキーム - トークンURLを指定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")