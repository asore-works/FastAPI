"""
app/services/user_location.py

ユーザーと拠点の関連を管理するビジネスロジックを扱うサービス
ユーザーの拠点所属情報のCRUD操作を実装
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError
from datetime import date

from app.core.exceptions import ConflictException, NotFoundException, BadRequestException
from app.models.user_location import UserLocation
from app.models.user import User
from app.models.location import Location
from app.schemas.user_location import UserLocationCreate, UserLocationUpdate, UserLocationPage

class UserLocationService:
    """
    ユーザー所属関連のビジネスロジックを扱うサービスクラス
    SQLAlchemy 2.0の非同期APIを活用
    """
    
    @staticmethod
    async def get(db: AsyncSession, user_location_id: int) -> Optional[UserLocation]:
        """
        IDによるユーザー所属情報取得
        
        Args:
            db: データベースセッション
            user_location_id: ユーザー所属ID
            
        Returns:
            Optional[UserLocation]: 見つかったユーザー所属情報、見つからない場合はNone
        """
        result = await db.execute(
            select(UserLocation)
            .options(
                joinedload(UserLocation.user),
                joinedload(UserLocation.location)
            )
            .where(UserLocation.id == user_location_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user_location(
        db: AsyncSession, 
        user_id: int, 
        location_id: int,
        include_inactive: bool = False
    ) -> List[UserLocation]:
        """
        ユーザーIDと拠点IDによるユーザー所属情報取得
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            location_id: 拠点ID
            include_inactive: 終了日が設定されたレコードも含めるかどうか
            
        Returns:
            List[UserLocation]: ユーザー所属情報リスト
        """
        query = (
            select(UserLocation)
            .options(
                joinedload(UserLocation.user),
                joinedload(UserLocation.location)
            )
            .where(
                and_(
                    UserLocation.user_id == user_id,
                    UserLocation.location_id == location_id
                )
            )
        )
        
        # アクティブな割り当てのみ（終了日が設定されていないか今日以降）
        if not include_inactive:
            today = date.today()
            query = query.where(
                or_(
                    UserLocation.end_date == None,
                    UserLocation.end_date >= today
                )
            )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_locations(
        db: AsyncSession,
        user_id: int,
        include_inactive: bool = False
    ) -> List[UserLocation]:
        """
        ユーザーIDによる所属拠点一覧取得
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            include_inactive: 終了日が設定されたレコードも含めるかどうか
            
        Returns:
            List[UserLocation]: ユーザー所属情報リスト
        """
        query = (
            select(UserLocation)
            .options(
                joinedload(UserLocation.location)
            )
            .where(UserLocation.user_id == user_id)
        )
        
        # アクティブな割り当てのみ（終了日が設定されていないか今日以降）
        if not include_inactive:
            today = date.today()
            query = query.where(
                or_(
                    UserLocation.end_date == None,
                    UserLocation.end_date >= today
                )
            )
            
        # 主所属を優先して並べ替え
        query = query.order_by(
            UserLocation.is_primary.desc(),
            UserLocation.start_date.desc()
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_location_users(
        db: AsyncSession,
        location_id: int,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        is_primary: Optional[bool] = None
    ) -> Tuple[List[UserLocation], int]:
        """
        拠点IDによる所属ユーザー一覧取得
        
        Args:
            db: データベースセッション
            location_id: 拠点ID
            skip: スキップ数
            limit: 取得上限
            include_inactive: 終了日が設定されたレコードも含めるかどうか
            search: ユーザー名またはメールアドレスによる検索
            is_primary: 主所属かどうかによるフィルタリング
            
        Returns:
            Tuple[List[UserLocation], int]: ユーザー所属情報リストと総数のタプル
        """
        # クエリ構築
        query = (
            select(UserLocation)
            .join(UserLocation.user)
            .where(UserLocation.location_id == location_id)
        )
        
        # フィルタリング条件を適用
        if not include_inactive:
            today = date.today()
            query = query.where(
                or_(
                    UserLocation.end_date == None,
                    UserLocation.end_date >= today
                )
            )
        
        if is_primary is not None:
            query = query.where(UserLocation.is_primary == is_primary)
            
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.employee_id.ilike(search_term)
                )
            )
            
        # 総数取得
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar_one()
        
        # ページネーション適用とリレーションシップのロード
        items_query = (
            query
            .options(
                joinedload(UserLocation.user),
                joinedload(UserLocation.location)
            )
            .order_by(
                UserLocation.is_primary.desc(),
                User.full_name
            )
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(items_query)
        user_locations = result.scalars().all()
        
        return user_locations, total_count
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: UserLocationCreate) -> UserLocation:
        """
        ユーザー所属情報作成
        
        Args:
            db: データベースセッション
            obj_in: 作成するユーザー所属情報
            
        Returns:
            UserLocation: 作成されたユーザー所属情報
            
        Raises:
            BadRequestException: ユーザーまたは拠点が存在しない場合
            ConflictException: 同じユーザーと拠点の組み合わせで主所属の割り当てが既に存在する場合
        """
        # ユーザーの存在確認
        user_result = await db.execute(select(User).where(User.id == obj_in.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise BadRequestException(detail=f"ユーザーID {obj_in.user_id} は存在しません")
            
        # 拠点の存在確認
        location_result = await db.execute(select(Location).where(Location.id == obj_in.location_id))
        location = location_result.scalar_one_or_none()
        if not location:
            raise BadRequestException(detail=f"拠点ID {obj_in.location_id} は存在しません")
        
        # 主所属の場合、既存の主所属をチェック
        if obj_in.is_primary:
            existing_primaries = await db.execute(
                select(UserLocation)
                .where(
                    and_(
                        UserLocation.user_id == obj_in.user_id,
                        UserLocation.is_primary == True,
                        or_(
                            UserLocation.end_date == None,
                            UserLocation.end_date >= obj_in.start_date
                        )
                    )
                )
            )
            
            primaries = existing_primaries.scalars().all()
            if primaries:
                # 既存の主所属がある場合は、その終了日を新しい開始日の前日に設定
                for primary in primaries:
                    primary.end_date = obj_in.start_date.replace(
                        day=obj_in.start_date.day - 1
                    )
                    db.add(primary)
        
        # モデルインスタンス作成
        db_obj = UserLocation(
            user_id=obj_in.user_id,
            location_id=obj_in.location_id,
            is_primary=obj_in.is_primary,
            position=obj_in.position,
            department=obj_in.department,
            start_date=obj_in.start_date,
            end_date=obj_in.end_date,
            notes=obj_in.notes
        )
        
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if "uq_user_location_primary" in str(e).lower():
                raise ConflictException(detail="同じユーザーと拠点の組み合わせで主所属の割り当てが既に存在します")
            else:
                raise ConflictException(detail=str(e))
                
        await db.refresh(db_obj)
        return db_obj
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        db_obj: UserLocation,
        obj_in: Union[UserLocationUpdate, Dict[str, Any]]
    ) -> UserLocation:
        """
        ユーザー所属情報更新
        
        Args:
            db: データベースセッション
            db_obj: 更新対象のユーザー所属情報
            obj_in: 更新データ
            
        Returns:
            UserLocation: 更新されたユーザー所属情報
            
        Raises:
            ConflictException: 同じユーザーと拠点の組み合わせで主所属の割り当てが既に存在する場合
        """
        # 更新データを準備
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # 主所属の変更がある場合
        if "is_primary" in update_data and update_data["is_primary"] and not db_obj.is_primary:
            # 既存の主所属をチェック
            existing_primaries = await db.execute(
                select(UserLocation)
                .where(
                    and_(
                        UserLocation.user_id == db_obj.user_id,
                        UserLocation.id != db_obj.id,
                        UserLocation.is_primary == True,
                        or_(
                            UserLocation.end_date == None,
                            UserLocation.end_date >= (
                                update_data.get("start_date", db_obj.start_date)
                            )
                        )
                    )
                )
            )
            
            primaries = existing_primaries.scalars().all()
            if primaries:
                # 既存の主所属がある場合は、その終了日を新しい開始日の前日に設定
                for primary in primaries:
                    primary.end_date = update_data.get("start_date", db_obj.start_date).replace(
                        day=update_data.get("start_date", db_obj.start_date).day - 1
                    )
                    db.add(primary)
        
        # SQLAlchemy 2.0のUPDATE構文
        stmt = (
            update(UserLocation)
            .where(UserLocation.id == db_obj.id)
            .values(**update_data)
            .returning(UserLocation)
        )
        
        try:
            result = await db.execute(stmt)
            await db.commit()
            
            # 更新されたユーザー所属情報を関連エンティティと共に取得
            updated_user_location = await UserLocationService.get(db, db_obj.id)
            return updated_user_location
        except IntegrityError as e:
            await db.rollback()
            if "uq_user_location_primary" in str(e).lower():
                raise ConflictException(detail="同じユーザーと拠点の組み合わせで主所属の割り当てが既に存在します")
            else:
                raise ConflictException(detail=str(e))
    
    @staticmethod
    async def delete(db: AsyncSession, user_location_id: int) -> UserLocation:
        """
        ユーザー所属情報削除
        
        Args:
            db: データベースセッション
            user_location_id: 削除するユーザー所属情報のID
            
        Returns:
            UserLocation: 削除されたユーザー所属情報
            
        Raises:
            NotFoundException: ユーザー所属情報が見つからない場合
        """
        # ユーザー所属情報の存在確認
        user_location = await UserLocationService.get(db, user_location_id)
        if not user_location:
            raise NotFoundException(detail=f"ユーザー所属情報ID {user_location_id} は存在しません")
        
        # SQLAlchemy 2.0のDELETE構文
        stmt = delete(UserLocation).where(UserLocation.id == user_location_id).returning(UserLocation)
        result = await db.execute(stmt)
        
        # 削除されたユーザー所属情報を取得
        deleted_user_location = result.scalar_one_or_none()
        if not deleted_user_location:
            # 通常はここには到達しないはず
            raise NotFoundException(detail=f"ユーザー所属情報ID {user_location_id} は存在しません")
            
        await db.commit()
        return deleted_user_location
    
    @staticmethod
    async def get_location_users_page(
        db: AsyncSession,
        location_id: int,
        page: int = 1,
        size: int = 20,
        include_inactive: bool = False,
        search: Optional[str] = None,
        is_primary: Optional[bool] = None
    ) -> UserLocationPage:
        """
        ページネーション付き拠点所属ユーザー一覧取得
        
        Args:
            db: データベースセッション
            location_id: 拠点ID
            page: ページ番号（1から開始）
            size: ページサイズ
            include_inactive: 終了日が設定されたレコードも含めるかどうか
            search: ユーザー名またはメールアドレスによる検索
            is_primary: 主所属かどうかによるフィルタリング
            
        Returns:
            UserLocationPage: ページネーション情報付き拠点所属ユーザーリスト
        """
        # スキップ数計算
        skip = (page - 1) * size
        
        # ユーザー所属情報取得
        user_locations, total = await UserLocationService.get_location_users(
            db=db,
            location_id=location_id,
            skip=skip,
            limit=size,
            include_inactive=include_inactive,
            search=search,
            is_primary=is_primary
        )
        
        # 総ページ数計算
        pages = (total + size - 1) // size  # 切り上げ
        
        # レスポンス構築
        return UserLocationPage(
            items=user_locations,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )