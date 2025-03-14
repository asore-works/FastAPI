import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.core.config import settings
from app.services.item import ItemService
from app.models.user import User
from app.schemas.item import ItemCreate  # Pydantic v2 のモデル


class TestItemsAPI:
    """アイテムAPI関連のテストクラス"""

    @pytest.mark.asyncio
    async def test_create_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], db_session: AsyncSession, setup_database):
        """新規アイテム作成テスト"""
        item_data = {
            "title": "Test API Item",
            "description": "This is a test item created via API",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/items/",
            headers=normal_user_token_headers,
            json=item_data,
        )
        assert response.status_code == 201
        created_item = response.json()
        assert created_item["title"] == item_data["title"]
        assert created_item["description"] == item_data["description"]
        assert "id" in created_item
        assert "owner_id" in created_item
        assert "created_at" in created_item

        # DB に登録されたことを確認
        db_item = await ItemService.get(db_session, created_item["id"])
        assert db_item is not None
        assert db_item.title == item_data["title"]

    @pytest.mark.asyncio
    async def test_create_item_without_auth(self, async_client: AsyncClient):
        """認証なしでアイテム作成テスト（拒否されるべき）"""
        item_data = {
            "title": "Unauthorized Item",
            "description": "This should not be created",
        }
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/items/",
            json=item_data,
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_read_items_normal_user(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], normal_user: User, db_session: AsyncSession, setup_database):
        """一般ユーザーのアイテム一覧取得テスト"""
        # 3件のアイテムを作成
        for i in range(3):
            item_data = {"title": f"User Item {i}", "description": f"Description {i}"}
            await ItemService.create(
                db_session,
                obj_in=ItemCreate(**item_data),
                owner_id=normal_user.id,
            )
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/items/",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        items_page = response.json()
        assert "items" in items_page
        assert "total" in items_page
        assert "page" in items_page
        assert "size" in items_page
        assert "pages" in items_page

        # 一般ユーザーは自分のアイテムのみ取得できる
        assert items_page["total"] >= 3
        for item in items_page["items"]:
            assert item["owner_id"] == normal_user.id

    @pytest.mark.asyncio
    async def test_read_items_superuser(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], superuser: User, db_session: AsyncSession, setup_database):
        """管理者のアイテム一覧取得テスト（作成した全件が見えるはず）"""
        # 管理者用のアイテムを2件作成
        for i in range(2):
            item_data = {"title": f"Admin Item {i}", "description": f"Admin Description {i}"}
            # ここでは明示的に superuser.id を利用
            await ItemService.create(
                db_session,
                obj_in=ItemCreate(**item_data),
                owner_id=superuser.id,
            )
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/items/",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        items_page = response.json()
        # ここでは、作成した2件が取得されることを期待（必要に応じて期待値は変更してください）
        assert items_page["total"] >= 2

    @pytest.mark.asyncio
    async def test_read_item_by_id(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], normal_user: User, db_session: AsyncSession, setup_database):
        """IDによるアイテム取得テスト"""
        item_data = {"title": "Get Item By ID", "description": "Test item for get by ID"}
        item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=normal_user.id)
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/items/{item.id}",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        item_data_resp = response.json()
        assert item_data_resp["id"] == item.id
        assert item_data_resp["title"] == item_data["title"]
        assert item_data_resp["description"] == item_data["description"]
        assert item_data_resp["owner_id"] == normal_user.id

    @pytest.mark.asyncio
    async def test_read_other_user_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], superuser: User, db_session: AsyncSession, setup_database):
        """他のユーザーのアイテム取得テスト（拒否されるべき）"""
        item_data = {"title": "Admin Item", "description": "This belongs to admin"}
        admin_item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=superuser.id)
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/items/{admin_item.id}",
            headers=normal_user_token_headers,
        )
        # 他ユーザーのアイテムは取得できないので 403 Forbidden を想定
        assert response.status_code == 403
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_read_nonexistent_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], setup_database):
        """存在しないアイテム取得テスト"""
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/items/9999",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_update_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], normal_user: User, db_session: AsyncSession, setup_database):
        """アイテム更新テスト"""
        item_data = {"title": "Update Test Item", "description": "This will be updated"}
        item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=normal_user.id)
        update_data = {"title": "Updated Title", "description": "Updated description"}
        response = await async_client.put(
            f"{settings.API_V1_PREFIX}/items/{item.id}",
            headers=normal_user_token_headers,
            json=update_data,
        )
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["id"] == item.id
        assert updated_item["title"] == update_data["title"]
        assert updated_item["description"] == update_data["description"]
        # セッションを最新状態にリフレッシュして確認
        await db_session.refresh(item)
        assert item.title == update_data["title"]

    @pytest.mark.asyncio
    async def test_update_other_user_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], superuser: User, db_session: AsyncSession, setup_database):
        """他のユーザーのアイテム更新テスト（拒否されるべき）"""
        item_data = {"title": "Admin Update Item", "description": "This belongs to admin"}
        admin_item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=superuser.id)
        update_data = {"title": "Trying to update", "description": "This should fail"}
        response = await async_client.put(
            f"{settings.API_V1_PREFIX}/items/{admin_item.id}",
            headers=normal_user_token_headers,
            json=update_data,
        )
        assert response.status_code == 403
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_delete_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], normal_user: User, db_session: AsyncSession, setup_database):
        """アイテム削除テスト"""
        item_data = {"title": "Delete Test Item", "description": "This will be deleted"}
        item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=normal_user.id)
        response = await async_client.delete(
            f"{settings.API_V1_PREFIX}/items/{item.id}",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        deleted_item = response.json()
        assert deleted_item["id"] == item.id
        db_item = await ItemService.get(db_session, item.id)
        assert db_item is None

    @pytest.mark.asyncio
    async def test_delete_other_user_item(self, async_client: AsyncClient, normal_user_token_headers: Dict[str, str], superuser: User, db_session: AsyncSession, setup_database):
        """他のユーザーのアイテム削除テスト（拒否されるべき）"""
        item_data = {"title": "Admin Delete Item", "description": "This belongs to admin"}
        admin_item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=superuser.id)
        response = await async_client.delete(
            f"{settings.API_V1_PREFIX}/items/{admin_item.id}",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 403
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_superuser_delete_any_item(self, async_client: AsyncClient, superuser_token_headers: Dict[str, str], normal_user: User, db_session: AsyncSession, setup_database):
        """管理者による他のユーザーのアイテム削除テスト（許可されるべき）"""
        item_data = {"title": "User Item for Admin Delete", "description": "This will be deleted by admin"}
        user_item = await ItemService.create(db_session, obj_in=ItemCreate(**item_data), owner_id=normal_user.id)
        response = await async_client.delete(
            f"{settings.API_V1_PREFIX}/items/{user_item.id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        deleted_item = response.json()
        assert deleted_item["id"] == user_item.id
        db_item = await ItemService.get(db_session, user_item.id)
        assert db_item is None