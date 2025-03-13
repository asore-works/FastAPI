from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 非同期エンジンの作成
# SQLAlchemy 2.0の新しいAPI形式を使用
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # 接続プールの設定
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# 非同期セッションの設定
# expire_on_commitをFalseにして、commit後もオブジェクトにアクセスできるように
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPIのDependency Injectionで使用するための非同期DBセッション取得関数
    
    SQLAlchemy 2.0の非同期機能を活用した依存性
    
    Yields:
        AsyncSession: 非同期DBセッション
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # 明示的なコミットは呼び出し側の責任
        except Exception:
            # エラー発生時は自動的にロールバック
            await session.rollback()
            raise