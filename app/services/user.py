from typing import Any, Dict, Optional, Union, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    ユーザー関連のビジネスロジックを扱うサービスクラス
    SQLAlchemy 2.0の非同期APIを活用
    """
    
    @staticmethod
    async def get(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        IDによるユーザー取得
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            
        Returns:
            Optional[User]: 見つかったユーザー、見つからない場合はNone
        """
        # SQLAlchemy 2.0のSELECT構文
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        メールアドレスによるユーザー取得
        
        Args:
            db: データベースセッション
            email: メールアドレス
            
        Returns:
            Optional[User]: 見つかったユーザー、見つからない場合はNone
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        """
        複数ユーザーの取得（ページネーション付き）
        
        Args:
            db: データベースセッション
            skip: スキップ数
            limit: 取得上限
            is_active: アクティブユーザーのみに絞り込み
            
        Returns:
            List[User]: ユーザーリスト
        """
        query = select(User).offset(skip).limit(limit)
        
        # フィルタが指定されている場合は適用
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: UserCreate) -> User:
        """
        ユーザー作成
        
        Args:
            db: データベースセッション
            obj_in: 作成するユーザー情報
            
        Returns:
            User: 作成されたユーザー
            
        Raises:
            ConflictException: メールアドレスが既に存在する場合
        """
        # パスワードをハッシュ化
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise ConflictException(detail="Email already exists")
            
        await db.refresh(db_obj)
        return db_obj
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        ユーザー情報更新
        
        Args:
            db: データベースセッション
            db_obj: 更新対象のユーザー
            obj_in: 更新データ
            
        Returns:
            User: 更新されたユーザー
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # パスワードが含まれる場合はハッシュ化
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        # SQLAlchemy 2.0のUPDATE構文
        stmt = (
            update(User)
            .where(User.id == db_obj.id)
            .values(**update_data)
            .returning(User)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: int) -> User:
        """
        ユーザー削除
        
        Args:
            db: データベースセッション
            user_id: 削除するユーザーのID
            
        Returns:
            User: 削除されたユーザー
            
        Raises:
            NotFoundException: ユーザーが見つからない場合
        """
        # 存在確認
        user = await UserService.get(db, user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
            
        # SQLAlchemy 2.0のDELETE構文
        stmt = delete(User).where(User.id == user_id).returning(User)
        result = await db.execute(stmt)
        
        # 削除されたユーザーを取得
        deleted_user = result.scalar_one_or_none()
        if not deleted_user:
            # 通常はここには到達しないはず
            raise NotFoundException(detail=f"User with ID {user_id} not found")
            
        await db.commit()
        return deleted_user
    
    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """
        メールアドレスとパスワードによるユーザー認証
        
        Args:
            db: データベースセッション
            email: メールアドレス
            password: パスワード
            
        Returns:
            Optional[User]: 認証成功時はユーザー、失敗時はNone
        """
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user