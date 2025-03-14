import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

# conftest.py が "app/tests" 内にある場合、3階層上がプロジェクトルートになります
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

import os
from typing import AsyncGenerator, Generator, Dict

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from httpx import AsyncClient

from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService

# テスト用のデータベースURLを環境変数から取得（なければデフォルト値を使用）
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://unicore_test_user:your_test_password@localhost:5432/unicore_test")

# PostgreSQL 用の非同期エンジンを作成
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    future=True,
)

# テスト用のセッション作成関数
async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async_session = AsyncSession(engine, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.close()

# FastAPI の依存関係をオーバーライド
app.dependency_overrides[get_db] = get_test_db

# テスト用のデータベース初期化フィクスチャ
@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """
    各テスト関数の前にテスト用データベースを初期化（drop_all -> create_all）
    テスト終了後にテーブルを削除します。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 同期HTTPクライアント（FastAPI の TestClient を利用）
@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

# 非同期HTTPクライアント
@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

# テスト用DBセッションフィクスチャ（setup_database に依存）
@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

# スーパーユーザー作成用フィクスチャ
@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    user_in = UserCreate(
        email="admin@example.com",
        password="password123",
        full_name="Test Admin",
        is_superuser=True,
    )
    user = await UserService.get_by_email(db_session, user_in.email)
    if not user:
        user = await UserService.create(db_session, obj_in=user_in)
    return user

# スーパーユーザーのアクセストークンヘッダー生成フィクスチャ
@pytest_asyncio.fixture
async def superuser_token_headers(superuser: User) -> Dict[str, str]:
    from app.core.security import create_access_token
    access_token = create_access_token(subject=superuser.id)
    return {"Authorization": f"Bearer {access_token}"}

# 一般ユーザー作成用フィクスチャ
@pytest_asyncio.fixture
async def normal_user(db_session: AsyncSession) -> User:
    user_in = UserCreate(
        email="user@example.com",
        password="password123",
        full_name="Test User",
        is_superuser=False,
    )
    user = await UserService.get_by_email(db_session, user_in.email)
    if not user:
        user = await UserService.create(db_session, obj_in=user_in)
    return user

# 一般ユーザーのアクセストークンヘッダー生成フィクスチャ
@pytest_asyncio.fixture
async def normal_user_token_headers(normal_user: User) -> Dict[str, str]:
    from app.core.security import create_access_token
    access_token = create_access_token(subject=normal_user.id)
    return {"Authorization": f"Bearer {access_token}"}

# テスト環境の環境変数をセットアップするフィクスチャ（セッションスコープ）
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    テスト実行前に必要な環境変数をセットアップします。
    テスト終了後に元の環境変数を復元します。
    """
    original_env = os.environ.copy()
    os.environ["SECRET_KEY"] = "your-test-secret-key"
    os.environ["APP_ENV"] = "testing"
    os.environ["POSTGRES_SERVER"] = "localhost"
    os.environ["POSTGRES_USER"] = "unicore_test_user"
    os.environ["POSTGRES_PASSWORD"] = "your_test_password"
    os.environ["POSTGRES_DB"] = "unicore_test"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["FIRST_SUPERUSER_EMAIL"] = "admin_test@example.com"
    os.environ["FIRST_SUPERUSER_PASSWORD"] = "admintestpassword"
    yield
    os.environ.clear()
    os.environ.update(original_env)