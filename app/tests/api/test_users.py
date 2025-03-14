import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.core.config import settings
from app.services.user import UserService


class TestUsersAPI:
    """ユーザーAPI関連のテストクラス"""

    @pytest.mark.asyncio
    async def test_read_user_me(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str]):
        """自分自身のユーザー情報取得テスト"""
        # 自分自身の情報を取得
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/users/me",
            headers=normal_user_token_headers,
        )
        
        # レスポンス検証
        assert response.status_code == 200
        user_data = response.json()
        assert "email" in user_data
        assert "id" in user_data
        assert "is_active" in user_data
        assert "password" not in user_data
        assert "hashed_password" not in user_data

    @pytest.mark.asyncio
    async def test_read_user_me_without_auth(self, async_client: AsyncClient):
        """認証なしでの自分自身のユーザー情報取得テスト"""
        # 認証なしでのリクエスト
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/users/me",
        )
        
        # エラーレスポンス検証
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_update_user_me(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str]):
        """自分自身のユーザー情報更新テスト"""
        # 更新データ
        update_data = {
            "full_name": "Updated My Name",
            "password": "newpassword123",
        }
        
        # ユーザー情報を更新
        response = await async_client.put(
            f"{settings.API_V1_PREFIX}/users/me",
            headers=normal_user_token_headers,
            json=update_data,
        )
        
        # レスポンス検証
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["full_name"] == update_data["full_name"]
        assert "password" not in user_data
        assert "hashed_password" not in user_data

    @pytest.mark.asyncio
    async def test_update_user_me_superuser(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str]):
        """一般ユーザーが自分自身を管理者に昇格させようとするテスト（拒否されるべき）"""
        # 更新データ（管理者フラグあり）
        update_data = {
            "full_name": "Trying to be Admin",
            "is_superuser": True,
        }
        
        # ユーザー情報を更新
        response = await async_client.put(
            f"{settings.API_V1_PREFIX}/users/me",
            headers=normal_user_token_headers,
            json=update_data,
        )
        
        # レスポンス検証（is_superuserが変更されずに更新が成功する）
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["full_name"] == update_data["full_name"]
        assert user_data["is_superuser"] == False  # 一般ユーザーのままであることを確認

    @pytest.mark.asyncio
    async def test_read_user_by_id(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], normal_user):
        """特定のユーザー情報取得テスト（管理者）"""
        # 管理者が一般ユーザーの情報を取得
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/users/{normal_user.id}",
            headers=superuser_token_headers,
        )
        
        # レスポンス検証
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["id"] == normal_user.id
        assert user_data["email"] == normal_user.email

    @pytest.mark.asyncio
    async def test_read_other_user_by_id(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], superuser):
        """一般ユーザーが他のユーザー情報を取得しようとするテスト（拒否されるべき）"""
        # 一般ユーザーが管理者の情報を取得
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/users/{superuser.id}",
            headers=normal_user_token_headers,
        )
        
        # エラーレスポンス検証
        assert response.status_code == 403
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_read_users(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str]):
        """全ユーザー一覧取得テスト（管理者）"""
        # 管理者が全ユーザー一覧を取得
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=superuser_token_headers,
        )
        
        # レスポンス検証
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0
        # 各ユーザーに必要なフィールドがあることを確認
        for user in users:
            assert "id" in user
            assert "email" in user
            assert "is_active" in user

    @pytest.mark.asyncio
    async def test_read_users_normal_user(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str]):
        """一般ユーザーが全ユーザー一覧を取得しようとするテスト（拒否されるべき）"""
        # 一般ユーザーが全ユーザー一覧を取得
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=normal_user_token_headers,
        )
        
        # エラーレスポンス検証
        assert response.status_code == 403
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_create_user_admin(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], db_session: AsyncSession):
        """管理者による新規ユーザー作成テスト"""
        # 新規ユーザーデータ
        user_data = {
            "email": "admin_created@example.com",
            "password": "adminpassword",
            "full_name": "Admin Created User",
            "is_superuser": False,
        }
        
        # 管理者がユーザーを作成
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/users/",
            headers=superuser_token_headers,
            json=user_data,
        )
        
        # レスポンス検証
        assert response.status_code == 201
        new_user = response.json()
        assert new_user["email"] == user_data["email"]
        assert new_user["full_name"] == user_data["full_name"]
        assert new_user["is_superuser"] == user_data["is_superuser"]
        
        # データベースに登録されたことを確認
        db_user = await UserService.get_by_email(db_session, user_data["email"])
        assert db_user is not None
        assert db_user.email == user_data["email"]

    @pytest.mark.asyncio
    async def test_create_user_normal(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str]):
        """一般ユーザーが新規ユーザーを作成しようとするテスト（拒否されるべき）"""
        # 新規ユーザーデータ
        user_data = {
            "email": "normal_created@example.com",
            "password": "normalpassword",
            "full_name": "Normal Created User",
        }
        
        # 一般ユーザーがユーザー作成を試みる
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/users/",
            headers=normal_user_token_headers,
            json=user_data,
        )
        
        # エラーレスポンス検証
        assert response.status_code == 403
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_update_user_admin(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], normal_user):
        """管理者による他のユーザーの更新テスト"""
        # 更新データ
        update_data = {
            "full_name": "Admin Updated Name",
            "is_active": True,
        }
        
        # 管理者が一般ユーザーを更新
        response = await async_client.put(
            f"{settings.API_V1_PREFIX}/users/{normal_user.id}",
            headers=superuser_token_headers,
            json=update_data,
        )
        
        # レスポンス検証
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["id"] == normal_user.id
        assert updated_user["full_name"] == update_data["full_name"]
        assert updated_user["is_active"] == update_data["is_active"]

    @pytest.mark.asyncio
    async def test_delete_user_admin(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], db_session: AsyncSession):
        """管理者によるユーザー削除テスト"""
        # 削除対象のユーザーを作成
        user_data = {
            "email": "to_delete@example.com",
            "password": "deletepassword",
            "full_name": "User To Delete",
        }
        
        create_response = await async_client.post(
            f"{settings.API_V1_PREFIX}/users/",
            headers=superuser_token_headers,
            json=user_data,
        )
        
        created_user = create_response.json()
        user_id = created_user["id"]
        
        # 管理者がユーザーを削除
        response = await async_client.delete(
            f"{settings.API_V1_PREFIX}/users/{user_id}",
            headers=superuser_token_headers,
        )
        
        # レスポンス検証
        assert response.status_code == 200
        deleted_user = response.json()
        assert deleted_user["id"] == user_id
        
        # データベースから削除されたことを確認
        db_user = await UserService.get(db_session, user_id)
        assert db_user is None

    @pytest.mark.asyncio
    async def test_delete_self_admin(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], superuser):
        """管理者が自分自身を削除しようとするテスト（拒否されるべき）"""
        # 管理者が自分自身を削除
        response = await async_client.delete(
            f"{settings.API_V1_PREFIX}/users/{superuser.id}",
            headers=superuser_token_headers,
        )
        
        # エラーレスポンス検証
        assert response.status_code == 400
        assert "detail" in response.json()