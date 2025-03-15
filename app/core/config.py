# app/core/config.py

from typing import List, Optional, Union, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    アプリケーション設定。
    Pydantic v2のモデル構文とSettingsConfigDictを使用した最新の設定管理。
    """
    # 環境変数からの設定読み込み
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # アプリケーション設定
    APP_ENV: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "UniCore"
    API_V1_PREFIX: str = "/api/v1"
    
    # セキュリティ設定
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS設定
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # CORS設定のバリデーション
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        環境変数から渡されるCORS設定をリストに変換する
        Pydantic v2ではfield_validatorデコレータを使用
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # データベース設定
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None
    
    # 管理者ユーザー設定
    FIRST_SUPERUSER_EMAIL: str
    FIRST_SUPERUSER_PASSWORD: str
    
    # SQLAlchemyのURIアセンブル
    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        """
        DATABASE_URL が明示的に設定されていない場合、
        個別のPostgreSQL設定から構築する
        """
        if isinstance(v, str):
            return v
        
        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        server = info.data.get("POSTGRES_SERVER")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")
        
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"
    
    @field_validator("SYNC_DATABASE_URL", mode="before")
    def assemble_sync_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        """
        SYNC_DATABASE_URL が明示的に設定されていない場合、
        個別のPostgreSQL設定から構築する（Alembic用同期接続）
        """
        if isinstance(v, str):
            return v
        
        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        server = info.data.get("POSTGRES_SERVER")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")
        
        return f"postgresql://{user}:{password}@{server}:{port}/{db}"

# 設定インスタンスを作成
settings = Settings()

# 注: 本番環境では.envファイルではなく環境変数を使用することが推奨されます