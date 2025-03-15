# app/api/routes/users.py

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_active_superuser,
    oauth2_scheme,
)
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.services.user import UserService

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    現在ログインしているユーザー自身の情報を取得
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    現在ログインしているユーザー自身の情報を更新
    """
    # 管理者権限は自分で変更できない（セキュリティ対策）
    if user_in.is_superuser is not None:
        user_in.is_superuser = current_user.is_superuser
        
    # ユーザー情報更新
    user = await UserService.update(db, current_user, user_in)
    return user


@router.get("/{user_id}", response_model=UserSchema)
async def read_user_by_id(
    user_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    特定のユーザー情報を取得
    - 管理者: 全ユーザーの情報を取得可能
    - 一般ユーザー: 自分自身の情報のみ取得可能
    """
    # 自分自身または管理者のみアクセス可能
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    # ユーザー取得
    user = await UserService.get(db, user_id)
    if not user:
        raise NotFoundException(detail=f"User with ID {user_id} not found")
        
    return user


@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),  # 管理者のみアクセス可能
) -> Any:
    """
    ユーザー一覧を取得（管理者のみ）
    """
    users = await UserService.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),  # 管理者のみアクセス可能
) -> Any:
    """
    新しいユーザーを作成（管理者のみ）
    """
    user = await UserService.create(db, user_in)
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int = Path(..., gt=0),
    user_in: UserUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),  # 管理者のみアクセス可能
) -> Any:
    """
    ユーザー情報を更新（管理者のみ）
    """
    user = await UserService.get(db, user_id)
    if not user:
        raise NotFoundException(detail=f"User with ID {user_id} not found")
        
    user = await UserService.update(db, user, user_in)
    return user


@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
    user_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),  # 管理者のみアクセス可能
) -> Any:
    """
    ユーザーを削除（管理者のみ）
    """
    # 自分自身は削除できない
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
        
    user = await UserService.delete(db, user_id)
    return user