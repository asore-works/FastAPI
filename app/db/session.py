"""
ファイル: app/db/session.py
説明: 非同期SQLAlchemyエンジンとセッションファクトリの設定を行います。
      FastAPIの依存性注入で利用する非同期データベースセッション取得関数を提供します。
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLAlchemy 2.0のAPIを利用して非同期エンジンを作成
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# 非同期セッションのファクトリを設定
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPIで使用する非同期データベースセッションを提供する依存性関数。

    Yields:
        AsyncSession: リクエスト処理で使用するDBセッション
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise