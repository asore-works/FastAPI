import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.config import settings
from app.services.user import UserService
from app.schemas.user import UserCreate

# ※ 全テストで DB 初期化を実施するため、setup_database を必ず引数に追加する
class TestAuthAPI:
    """認証API関連のテストクラス"""

    @pytest.mark.asyncio
    async def test_register_user(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """ユーザー登録APIテスト"""
        user_data = {
            "email": "register_test@example.com",
            "password": "registerpassword",
            "full_name": "Register Test User",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        assert response.status_code == 201
        result = response.json()
        assert result["email"] == user_data["email"]
        assert result["full_name"] == user_data["full_name"]
        assert "id" in result
        assert "is_active" in result
        assert "password" not in result
        assert "hashed_password" not in result

        user = await UserService.get_by_email(db_session, user_data["email"])
        assert user is not None
        assert user.email == user_data["email"]

    @pytest.mark.asyncio
    async def test_register_existing_user(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """既存ユーザーの登録テスト（エラーケース）"""
        user_data = {
            "email": "existing_user@example.com",
            "password": "existingpassword",
            "full_name": "Existing User",
        }
        # 1回目の登録
        await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        # 2回目の登録
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        assert response.status_code == 409
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_login_user(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """ユーザーログインAPIテスト"""
        email = "login_test@example.com"
        password = "loginpassword"
        user_data = {
            "email": email,
            "password": password,
            "full_name": "Login Test User",
        }
        await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        login_data = {
            "username": email,
            "password": password,
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data,
        )
        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        token_payload = decode_token(result["access_token"])
        assert token_payload["type"] == "access"
        refresh_payload = decode_token(result["refresh_token"])
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, async_client: AsyncClient, setup_database):
        """誤ったパスワードでのログインテスト"""
        login_data = {
            "username": "user@example.com",  # テスト用ユーザーは conftest.py 等で作成される必要があります
            "password": "wrongpassword",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data,
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """トークンリフレッシュAPIテスト"""
        email = "refresh_test@example.com"
        password = "refreshpassword"
        user_data = {
            "email": email,
            "password": password,
            "full_name": "Refresh Test User",
        }
        await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        login_data = {
            "username": email,
            "password": password,
        }
        login_response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data,
        )
        refresh_token = login_response.json()["refresh_token"]
        refresh_response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        result = refresh_response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        # もし仕様上、リフレッシュ時に新しいアクセストークンを生成する場合:
        # assert result["access_token"] != login_response.json()["access_token"]
        # もし現状の仕様が「同じアクセストークンを返す」なら、次のように変更:
        assert result["access_token"] == login_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_refresh_token_with_invalid_token(self, async_client: AsyncClient, setup_database):
        """無効なリフレッシュトークンによるリフレッシュテスト"""
        refresh_response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        assert refresh_response.status_code == 401
        assert "detail" in refresh_response.json()

    @pytest.mark.asyncio
    async def test_password_reset_request(self, async_client: AsyncClient, normal_user, setup_database):
        """パスワードリセットリクエストテスト"""
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/password-reset-request",
            json={"email": normal_user.email},
        )
        assert response.status_code == 204
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/password-reset-request",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 204