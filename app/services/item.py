from typing import Any, Dict, Optional, Union, List, Tuple

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate, ItemPage


class ItemService:
    """
    アイテム関連のビジネスロジックを扱うサービスクラス
    SQLAlchemy 2.0の非同期APIを活用
    """
    
    @staticmethod
    async def get(db: AsyncSession, item_id: int) -> Optional[Item]:
        """
        IDによるアイテム取得
        
        Args:
            db: データベースセッション
            item_id: アイテムID
            
        Returns:
            Optional[Item]: 見つかったアイテム、見つからない場合はNone
        """
        # SQLAlchemy 2.0のSELECT構文
        result = await db.execute(
            select(Item)
            .options(selectinload(Item.owner))  # リレーションシップの先読み
            .where(Item.id == item_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        owner_id: Optional[int] = None,
    ) -> Tuple[List[Item], int]:
        """
        複数アイテムの取得（ページネーション付き）
        
        Args:
            db: データベースセッション
            skip: スキップ数
            limit: 取得上限
            owner_id: オーナーIDによるフィルタリング
            
        Returns:
            Tuple[List[Item], int]: アイテムリストと総数のタプル
        """
        # クエリ構築
        query = select(Item)
        
        # フィルタが指定されている場合は適用
        if owner_id is not None:
            query = query.where(Item.owner_id == owner_id)
            
        # 総数取得
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar_one()
        
        # ページネーション適用
        items_query = query.offset(skip).limit(limit)
        result = await db.execute(items_query)
        items = result.scalars().all()
        
        return items, total_count
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: ItemCreate, owner_id: int) -> Item:
        """
        アイテム作成
        
        Args:
            db: データベースセッション
            obj_in: 作成するアイテム情報
            owner_id: オーナーID
            
        Returns:
            Item: 作成されたアイテム
        """
        # モデルインスタンス作成
        db_obj = Item(
            title=obj_in.title,
            description=obj_in.description,
            owner_id=owner_id,
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        db_obj: Item,
        obj_in: Union[ItemUpdate, Dict[str, Any]]
    ) -> Item:
        """
        アイテム情報更新
        
        Args:
            db: データベースセッション
            db_obj: 更新対象のアイテム
            obj_in: 更新データ
            
        Returns:
            Item: 更新されたアイテム
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # SQLAlchemy 2.0のUPDATE構文
        stmt = (
            update(Item)
            .where(Item.id == db_obj.id)
            .values(**update_data)
            .returning(Item)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()
    
    @staticmethod
    async def delete(db: AsyncSession, item_id: int) -> Item:
        """
        アイテム削除
        
        Args:
            db: データベースセッション
            item_id: 削除するアイテムのID
            
        Returns:
            Item: 削除されたアイテム
            
        Raises:
            NotFoundException: アイテムが見つからない場合
        """
        # 存在確認
        item = await ItemService.get(db, item_id)
        if not item:
            raise NotFoundException(detail=f"Item with ID {item_id} not found")
            
        # SQLAlchemy 2.0のDELETE構文
        stmt = delete(Item).where(Item.id == item_id).returning(Item)
        result = await db.execute(stmt)
        
        # 削除されたアイテムを取得
        deleted_item = result.scalar_one_or_none()
        if not deleted_item:
            # 通常はここには到達しないはず
            raise NotFoundException(detail=f"Item with ID {item_id} not found")
            
        await db.commit()
        return deleted_item
    
    @staticmethod
    async def get_page(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        owner_id: Optional[int] = None,
    ) -> ItemPage:
        """
        ページネーション付きアイテム一覧取得
        
        Args:
            db: データベースセッション
            page: ページ番号（1から開始）
            size: ページサイズ
            owner_id: オーナーIDによるフィルタリング
            
        Returns:
            ItemPage: ページネーション情報付きアイテムリスト
        """
        # スキップ数計算
        skip = (page - 1) * size
        
        # アイテム取得
        items, total = await ItemService.get_multi(
            db=db,
            skip=skip,
            limit=size,
            owner_id=owner_id,
        )
        
        # 総ページ数計算
        pages = (total + size - 1) // size  # 切り上げ
        
        # レスポンス構築
        return ItemPage(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )