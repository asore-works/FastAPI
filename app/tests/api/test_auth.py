# app/tests/api/test_auth.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.core.security import decode_token
from app.core.config import settings
from app.services.user import UserService
from app.schemas.user import UserCreate, TokenPayload

class TestAuthAPI:
    """認証API関連のテストクラス"""

    @pytest.mark.asyncio
    async def test_register_user(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """ユーザー登録APIテスト"""
        user_data = {
            "email": "register_test@example.com",
            "username": "register_test",
            "password": "registerpassword",
            "last_name": "Register",
            "first_name": "Test User",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        assert response.status_code == 201
        result = response.json()
        assert result["email"] == user_data["email"]
        # computed field full_name が出力される（"Register Test User"）
        expected_full_name = f"{user_data['last_name']} {user_data['first_name']}"
        assert result["full_name"] == expected_full_name
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
            "username": "existing_user",
            "password": "existingpassword",
            "last_name": "Existing",
            "first_name": "User",
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
        # Pydantic のバリデーションエラーの場合、422 Unprocessable Entity になる場合もある
        assert response.status_code in (409, 422)
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_login_user(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """ユーザーログインAPIテスト"""
        email = "login_test@example.com"
        password = "loginpassword"
        user_data = {
            "email": email,
            "username": "login_test",  # 登録時は username もセット
            "password": password,
            "last_name": "Login",
            "first_name": "Test User",
        }
        await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        login_data = {
            "username": email,  # OAuth2PasswordRequestForm では username にメールアドレスを指定
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
            "username": "nonexistent@example.com",
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
            "username": "refresh_test",
            "password": password,
            "last_name": "Refresh",
            "first_name": "Test User",
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
        login_json = login_response.json()
        assert "refresh_token" in login_json, "Login response must contain refresh_token"
        refresh_token = login_json["refresh_token"]
        refresh_response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        result = refresh_response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        # 新たに生成されたトークンは（iatの差分により）異なるはず
        assert result["access_token"] != login_json["access_token"]

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

    @pytest.mark.asyncio
    async def test_register_user_with_extended_fields(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """拡張フィールド付きのユーザー登録APIテスト"""
        user_data = {
            "email": "extended_register@example.com",
            "username": "extended_register",
            "password": "registerpassword",
            "last_name": "登録",
            "first_name": "拡張",
            "birth_date": "1988-07-07",
            "phone_number": "090-7777-8888",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user_data,
        )
        assert response.status_code == 201
        result = response.json()
        assert result["email"] == user_data["email"]
        assert result["username"] == user_data["username"]
        assert result["last_name"] == user_data["last_name"]
        assert result["first_name"] == user_data["first_name"]
        assert result["birth_date"] == user_data["birth_date"]
        assert result["phone_number"] == user_data["phone_number"]
        user = await UserService.get_by_email(db_session, user_data["email"])
        assert user is not None
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, async_client: AsyncClient, db_session: AsyncSession, setup_database):
        """重複ユーザー名での登録テスト（エラーケース）"""
        user1_data = {
            "email": "user1_dup@example.com",
            "username": "duplicate_username",
            "password": "password123",
        }
        await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user1_data,
        )
        user2_data = {
            "email": "user2_dup@example.com",
            "username": "duplicate_username",
            "password": "password456",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/auth/register",
            json=user2_data,
        )
        assert response.status_code in (409, 422)
        assert "detail" in response.json()