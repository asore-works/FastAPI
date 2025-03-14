import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.item import ItemService
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class TestItemService:
    """ItemServiceのテストクラス"""

    @pytest.mark.asyncio
    async def test_create_item(self, db_session: AsyncSession, normal_user: User):
        """アイテム作成の正常系テスト"""
        # テスト用アイテムデータ - Pydanticモデルを使用
        item_in = ItemCreate(
            title="Test Item",
            description="This is a test item",
        )
        
        # アイテム作成
        item = await ItemService.create(db_session, obj_in=item_in, owner_id=normal_user.id)
        
        # 検証
        assert item is not None
        assert item.title == item_in.title
        assert item.description == item_in.description
        assert item.owner_id == normal_user.id

    @pytest.mark.asyncio
    async def test_get_item(self, db_session: AsyncSession, normal_user: User):
        """アイテム取得テスト"""
        # テスト用アイテム作成 - Pydanticモデルを使用
        item_in = ItemCreate(
            title="Get Test Item",
            description="Item for get test",
        )
        created_item = await ItemService.create(db_session, obj_in=item_in, owner_id=normal_user.id)
        
        # アイテム取得
        item = await ItemService.get(db_session, created_item.id)
        
        # 検証
        assert item is not None
        assert item.id == created_item.id
        assert item.title == item_in.title
        assert item.owner_id == normal_user.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, db_session: AsyncSession):
        """存在しないアイテムの取得テスト"""
        # 存在しないIDでアイテム取得
        item = await ItemService.get(db_session, 9999)
        
        # 検証
        assert item is None

    @pytest.mark.asyncio
    async def test_update_item(self, db_session: AsyncSession, normal_user: User):
        """アイテム更新テスト"""
        # テスト用アイテム作成 - Pydanticモデルを使用
        item_in = ItemCreate(
            title="Update Test Item",
            description="Item for update test",
        )
        item = await ItemService.create(db_session, obj_in=item_in, owner_id=normal_user.id)
        
        # 更新データ - Pydanticモデルを使用
        update_data = ItemUpdate(
            title="Updated Item Title",
            description="Updated description",
        )
        
        # アイテム更新
        updated_item = await ItemService.update(db_session, item, update_data)
        
        # 検証
        assert updated_item is not None
        assert updated_item.id == item.id
        assert updated_item.title == update_data.title
        assert updated_item.description == update_data.description
        assert updated_item.owner_id == normal_user.id

    @pytest.mark.asyncio
    async def test_delete_item(self, db_session: AsyncSession, normal_user: User):
        """アイテム削除テスト"""
        # テスト用アイテム作成 - Pydanticモデルを使用
        item_in = ItemCreate(
            title="Delete Test Item",
            description="Item for delete test",
        )
        item = await ItemService.create(db_session, obj_in=item_in, owner_id=normal_user.id)
        
        # アイテム削除
        deleted_item = await ItemService.delete(db_session, item.id)
        
        # 検証
        assert deleted_item is not None
        assert deleted_item.id == item.id
        
        # 削除されたことを確認
        item_after_delete = await ItemService.get(db_session, item.id)
        assert item_after_delete is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_item(self, db_session: AsyncSession):
        """存在しないアイテムの削除テスト"""
        # 存在しないIDでアイテム削除
        with pytest.raises(NotFoundException):
            await ItemService.delete(db_session, 9999)

    @pytest.mark.asyncio
    async def test_get_multi_items(self, db_session: AsyncSession, normal_user: User, superuser: User):
        """複数アイテムの取得テスト"""
        # テスト用アイテム作成（各ユーザーに2つずつ）- Pydanticモデルを使用
        for i in range(2):
            await ItemService.create(
                db_session,
                obj_in=ItemCreate(title=f"User Item {i}", description=f"Description {i}"),
                owner_id=normal_user.id,
            )
            await ItemService.create(
                db_session,
                obj_in=ItemCreate(title=f"Admin Item {i}", description=f"Description {i}"),
                owner_id=superuser.id,
            )
        
        # すべてのアイテム取得
        all_items, total_count = await ItemService.get_multi(db_session)
        
        # 検証（最低でも4つのアイテムが存在する）
        assert len(all_items) >= 4
        assert total_count >= 4
        
        # オーナーIDでフィルタリング
        user_items, user_count = await ItemService.get_multi(db_session, owner_id=normal_user.id)
        
        # 検証
        assert len(user_items) >= 2
        assert user_count >= 2
        for item in user_items:
            assert item.owner_id == normal_user.id

    @pytest.mark.asyncio
    async def test_get_page_items(self, db_session: AsyncSession, normal_user: User):
        """ページネーション付きアイテム取得テスト"""
        # テスト用アイテム作成（5つ）- Pydanticモデルを使用
        for i in range(5):
            await ItemService.create(
                db_session,
                obj_in=ItemCreate(title=f"Page Item {i}", description=f"Description {i}"),
                owner_id=normal_user.id,
            )
        
        # ページネーション付きでアイテム取得（1ページ目、サイズ2）
        page1 = await ItemService.get_page(db_session, page=1, size=2, owner_id=normal_user.id)
        
        # 検証
        assert page1.items is not None
        assert len(page1.items) == 2
        assert page1.total >= 5
        assert page1.page == 1
        assert page1.size == 2
        assert page1.pages >= 3  # 5アイテムをサイズ2で分割すると最低3ページ
        
        # 2ページ目取得
        page2 = await ItemService.get_page(db_session, page=2, size=2, owner_id=normal_user.id)
        
        # 検証
        assert page2.items is not None
        assert len(page2.items) == 2
        assert page2.page == 2
        
        # ページ外取得（項目数より大きいページ）
        page_beyond = await ItemService.get_page(db_session, page=10, size=2, owner_id=normal_user.id)
        
        # 検証（空のページとなる）
        assert page_beyond.items is not None
        assert len(page_beyond.items) == 0