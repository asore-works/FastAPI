"""
app/services/user.py

ユーザー関連のビジネスロジックを扱うサービス
データアクセスとビジネスルールを実装
"""

from typing import Any, Dict, Optional, Union, List
import json
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
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
        IDによるユーザー取得（ロール情報も取得）
        """
        # SQLAlchemy 2.0のSELECT構文
        result = await db.execute(
            select(User)
            .options(selectinload(User.role))  # ロール情報も取得
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        メールアドレスによるユーザー取得（ロール情報も取得）
        """
        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_employee_id(db: AsyncSession, employee_id: str) -> Optional[User]:
        """
        従業員IDによるユーザー取得
        """
        result = await db.execute(select(User).where(User.employee_id == employee_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """
        複数ユーザーの取得（ページネーション付き）
        フィルタとして役割ID、アクティブステータス、検索キーワードを指定可能
        """
        query = select(User).options(selectinload(User.role))
        
        # フィルタが指定されている場合は適用
        if role_id is not None:
            query = query.where(User.role_id == role_id)
            
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_term)) |
                (User.full_name.ilike(search_term)) |
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term)) |
                (User.employee_id.ilike(search_term))
            )
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: UserCreate) -> User:
        """
        ユーザー作成（拡張）
        """
        # パスワードをハッシュ化
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            full_name=obj_in.full_name or f"{obj_in.first_name or ''} {obj_in.last_name or ''}".strip(),
            is_superuser=obj_in.is_superuser,
            role_id=obj_in.role_id,
            department=obj_in.department,
            position=obj_in.position,
            employee_id=obj_in.employee_id,
            phone=obj_in.phone,
            mobile_phone=obj_in.mobile_phone,
            address=obj_in.address,
            date_of_birth=obj_in.date_of_birth,
            hire_date=obj_in.hire_date
        )
        
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            # 一意性制約違反のエラーメッセージを特定
            if "email" in str(e).lower():
                raise ConflictException(detail="Email already exists")
            elif "employee_id" in str(e).lower():
                raise ConflictException(detail="Employee ID already exists")
            else:
                raise ConflictException(detail=str(e))
            
        await db.refresh(db_obj)
        return db_obj
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        ユーザー情報更新（拡張）
        """
        # 更新データを準備
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # パスワードが含まれる場合はハッシュ化して更新
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data.pop("password"))
            update_data["hashed_password"] = hashed_password
            
        # フルネームの自動生成（first_nameまたはlast_nameが更新された場合）
        if ("first_name" in update_data or "last_name" in update_data) and "full_name" not in update_data:
            first_name = update_data.get("first_name", db_obj.first_name) or ""
            last_name = update_data.get("last_name", db_obj.last_name) or ""
            update_data["full_name"] = f"{first_name} {last_name}".strip()
            
        # ユーザー最終ログイン時間の更新（含まれている場合）
        if "last_login" in update_data and update_data["last_login"]:
            update_data["last_login"] = update_data["last_login"]
            
        # SQLAlchemy 2.0のUPDATE構文
        stmt = (
            update(User)
            .where(User.id == db_obj.id)
            .values(**update_data)
            .returning(User)
        )
        
        try:
            result = await db.execute(stmt)
            await db.commit()
            
            # 更新されたユーザーを関連エンティティと共に取得
            updated_user = await UserService.get(db, db_obj.id)
            return updated_user
        except IntegrityError as e:
            await db.rollback()
            # 一意性制約違反のエラーメッセージを特定
            if "email" in str(e).lower():
                raise ConflictException(detail="Email already exists")
            elif "employee_id" in str(e).lower():
                raise ConflictException(detail="Employee ID already exists")
            else:
                raise ConflictException(detail=str(e))
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: int) -> User:
        """
        ユーザー削除
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
        """
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int) -> User:
        """
        ユーザーの最終ログイン時間を更新
        """
        # 現在時刻を取得
        current_time = func.now()
        
        # 更新クエリを実行
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login=current_time)
            .returning(User)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        # 更新されたユーザーを取得
        updated_user = result.scalar_one_or_none()
        if not updated_user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
            
        return updated_user