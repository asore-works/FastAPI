"""
app/services/location.py

拠点（ロケーション）関連のビジネスロジックを扱うサービス
拠点のCRUD操作と関連する業務ルールを実装
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import select, update, delete, func, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotFoundException, BadRequestException
from app.models.location import Location, LocationType
from app.models.user_location import UserLocation
from app.schemas.location import LocationCreate, LocationUpdate, LocationPage

class LocationService:
    """
    拠点関連のビジネスロジックを扱うサービスクラス
    SQLAlchemy 2.0の非同期APIを活用
    """
    
    @staticmethod
    async def get(db: AsyncSession, location_id: int) -> Optional[Location]:
        """
        IDによる拠点取得
        
        Args:
            db: データベースセッション
            location_id: 拠点ID
            
        Returns:
            Optional[Location]: 見つかった拠点、見つからない場合はNone
        """
        # SQLAlchemy 2.0のSELECT構文
        result = await db.execute(
            select(Location)
            .options(
                joinedload(Location.parent),
                selectinload(Location.children),
                selectinload(Location.users)
            )
            .where(Location.id == location_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[Location]:
        """
        コードによる拠点取得
        
        Args:
            db: データベースセッション
            code: 拠点コード
            
        Returns:
            Optional[Location]: 見つかった拠点、見つからない場合はNone
        """
        # 常に大文字に正規化
        normalized_code = code.upper()
        
        result = await db.execute(
            select(Location)
            .options(
                joinedload(Location.parent),
                selectinload(Location.children)
            )
            .where(Location.code == normalized_code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        type: Optional[LocationType] = None,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        prefecture: Optional[str] = None,
    ) -> Tuple[List[Location], int]:
        """
        複数拠点の取得（フィルタリングとページネーション付き）
        
        Args:
            db: データベースセッション
            skip: スキップ数
            limit: 取得上限
            type: 拠点タイプによるフィルタリング
            parent_id: 親拠点IDによるフィルタリング
            is_active: アクティブステータスによるフィルタリング
            search: 名前またはコードによる検索
            prefecture: 都道府県によるフィルタリング
            
        Returns:
            Tuple[List[Location], int]: 拠点リストと総数のタプル
        """
        # クエリ構築
        query = select(Location)
        
        # フィルタリング条件を適用
        filters = []
        if type is not None:
            filters.append(Location.type == type)
            
        if parent_id is not None:
            filters.append(Location.parent_id == parent_id)
            
        if is_active is not None:
            filters.append(Location.is_active == is_active)
            
        if prefecture is not None:
            filters.append(Location.prefecture == prefecture)
            
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    Location.name.ilike(search_term),
                    Location.code.ilike(search_term),
                    Location.city.ilike(search_term),
                    Location.address1.ilike(search_term)
                )
            )
        
        # フィルタ条件を適用
        if filters:
            query = query.where(and_(*filters))
            
        # 総数取得
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar_one()
        
        # ページネーション適用とリレーションシップのロード
        items_query = (
            query
            .options(joinedload(Location.parent))
            .order_by(Location.type, Location.name)
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(items_query)
        locations = result.scalars().all()
        
        return locations, total_count
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: LocationCreate) -> Location:
        """
        拠点作成
        
        Args:
            db: データベースセッション
            obj_in: 作成する拠点情報
            
        Returns:
            Location: 作成された拠点
            
        Raises:
            ConflictException: 拠点コードが既に存在する場合
            BadRequestException: 親拠点が存在しない場合
        """
        # 親拠点の存在確認
        if obj_in.parent_id:
            parent = await LocationService.get(db, obj_in.parent_id)
            if not parent:
                raise BadRequestException(detail=f"親拠点ID {obj_in.parent_id} は存在しません")
        
        # コードを大文字に正規化
        normalized_code = obj_in.code.upper()
        
        # 循環参照をチェック
        if obj_in.parent_id:
            await LocationService._check_circular_reference(db, obj_in.parent_id, None)
        
        # モデルインスタンス作成
        db_obj = Location(
            name=obj_in.name,
            code=normalized_code,
            type=obj_in.type,
            parent_id=obj_in.parent_id,
            postal_code=obj_in.postal_code,
            prefecture=obj_in.prefecture,
            city=obj_in.city,
            address1=obj_in.address1,
            address2=obj_in.address2,
            phone=obj_in.phone,
            fax=obj_in.fax,
            email=obj_in.email,
            business_hours=obj_in.business_hours,
            description=obj_in.description,
            manager_name=obj_in.manager_name,
            capacity=obj_in.capacity,
            is_active=obj_in.is_active,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            established_date=obj_in.established_date,
        )
        
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if "code" in str(e).lower():
                raise ConflictException(detail=f"拠点コード '{normalized_code}' は既に使用されています")
            else:
                raise ConflictException(detail=str(e))
                
        await db.refresh(db_obj)
        return db_obj
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        db_obj: Location,
        obj_in: Union[LocationUpdate, Dict[str, Any]]
    ) -> Location:
        """
        拠点情報更新
        
        Args:
            db: データベースセッション
            db_obj: 更新対象の拠点
            obj_in: 更新データ
            
        Returns:
            Location: 更新された拠点
            
        Raises:
            ConflictException: 拠点コードが既に存在する場合
            BadRequestException: 親拠点が存在しない場合または循環参照が発生する場合
        """
        # 更新データを準備
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # コードの正規化（含まれている場合）
        if "code" in update_data and update_data["code"]:
            update_data["code"] = update_data["code"].upper()
        
        # 親拠点の変更がある場合
        if "parent_id" in update_data and update_data["parent_id"] != db_obj.parent_id:
            # 親拠点の存在確認
            if update_data["parent_id"]:
                parent = await LocationService.get(db, update_data["parent_id"])
                if not parent:
                    raise BadRequestException(detail=f"親拠点ID {update_data['parent_id']} は存在しません")
                
                # 循環参照をチェック
                await LocationService._check_circular_reference(db, update_data["parent_id"], db_obj.id)
        
        # SQLAlchemy 2.0のUPDATE構文
        stmt = (
            update(Location)
            .where(Location.id == db_obj.id)
            .values(**update_data)
            .returning(Location)
        )
        
        try:
            result = await db.execute(stmt)
            await db.commit()
            
            # 更新された拠点を関連エンティティと共に取得
            updated_location = await LocationService.get(db, db_obj.id)
            return updated_location
        except IntegrityError as e:
            await db.rollback()
            if "code" in str(e).lower():
                code = update_data.get("code", db_obj.code)
                raise ConflictException(detail=f"拠点コード '{code}' は既に使用されています")
            else:
                raise ConflictException(detail=str(e))
    
    @staticmethod
    async def delete(db: AsyncSession, location_id: int) -> Location:
        """
        拠点削除
        
        Args:
            db: データベースセッション
            location_id: 削除する拠点のID
            
        Returns:
            Location: 削除された拠点
            
        Raises:
            NotFoundException: 拠点が見つからない場合
            BadRequestException: 子拠点が存在する場合
        """
        # 拠点の存在確認
        location = await LocationService.get(db, location_id)
        if not location:
            raise NotFoundException(detail=f"拠点ID {location_id} は存在しません")
        
        # 子拠点の存在確認
        if location.children and len(location.children) > 0:
            raise BadRequestException(detail="子拠点が存在するため削除できません。先に子拠点を削除または移動してください。")
        
        # SQLAlchemy 2.0のDELETE構文
        stmt = delete(Location).where(Location.id == location_id).returning(Location)
        result = await db.execute(stmt)
        
        # 削除された拠点を取得
        deleted_location = result.scalar_one_or_none()
        if not deleted_location:
            # 通常はここには到達しないはず
            raise NotFoundException(detail=f"拠点ID {location_id} は存在しません")
            
        await db.commit()
        return deleted_location
    
    @staticmethod
    async def get_page(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        type: Optional[LocationType] = None,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        prefecture: Optional[str] = None,
    ) -> LocationPage:
        """
        ページネーション付き拠点一覧取得
        
        Args:
            db: データベースセッション
            page: ページ番号（1から開始）
            size: ページサイズ
            type: 拠点タイプによるフィルタリング
            parent_id: 親拠点IDによるフィルタリング
            is_active: アクティブステータスによるフィルタリング
            search: 名前またはコードによる検索
            prefecture: 都道府県によるフィルタリング
            
        Returns:
            LocationPage: ページネーション情報付き拠点リスト
        """
        # スキップ数計算
        skip = (page - 1) * size
        
        # 拠点取得
        locations, total = await LocationService.get_multi(
            db=db,
            skip=skip,
            limit=size,
            type=type,
            parent_id=parent_id,
            is_active=is_active,
            search=search,
            prefecture=prefecture,
        )
        
        # 総ページ数計算
        pages = (total + size - 1) // size  # 切り上げ
        
        # レスポンス構築
        return LocationPage(
            items=locations,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
    
    @staticmethod
    async def _check_circular_reference(
        db: AsyncSession,
        parent_id: int,
        current_id: Optional[int]
    ) -> None:
        """
        循環参照をチェック
        
        Args:
            db: データベースセッション
            parent_id: チェックする親拠点ID
            current_id: 現在の拠点ID（更新時）
            
        Raises:
            BadRequestException: 循環参照が検出された場合
        """
        # 親が自分自身の場合
        if parent_id == current_id:
            raise BadRequestException(detail="拠点は自分自身を親にできません")
        
        # 親の親を再帰的にチェック
        parent = await LocationService.get(db, parent_id)
        if not parent:
            return
        
        if parent.parent_id:
            # 親の親が現在の拠点の場合、循環参照となる
            if parent.parent_id == current_id:
                raise BadRequestException(detail="循環参照は許可されていません")
            
            # 親の親を再帰的にチェック
            await LocationService._check_circular_reference(db, parent.parent_id, current_id)