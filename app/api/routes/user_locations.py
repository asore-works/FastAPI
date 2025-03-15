"""
app/api/routes/user_locations.py

ユーザーと拠点の関連を管理するAPI定義
ユーザーの拠点所属情報の管理エンドポイントを提供
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.api.dependencies.auth import get_current_active_user
from app.core.permissions import has_permission, Permission
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.schemas.user_location import (
    UserLocation, UserLocationCreate, UserLocationUpdate,
    UserLocationWithUser
)
from app.services.user_location import UserLocationService
from app.services.user import UserService
from app.services.location import LocationService

router = APIRouter()

@router.post("/", response_model=UserLocation, status_code=status.HTTP_201_CREATED)
async def create_user_location(
    user_location_in: UserLocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_LOCATIONS)),
) -> Any:
    """
    新しいユーザー所属情報を作成
    - WRITE_LOCATIONS権限が必要
    """
    user_location = await UserLocationService.create(db, user_location_in)
    return user_location

@router.get("/{user_location_id}", response_model=UserLocationWithUser)
async def read_user_location(
    user_location_id: int = Path(..., gt=0, description="ユーザー所属ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    特定のユーザー所属情報を取得
    - READ_LOCATIONS権限が必要
    """
    user_location = await UserLocationService.get(db, user_location_id)
    if not user_location:
        raise NotFoundException(detail=f"ユーザー所属ID {user_location_id} は存在しません")
    return user_location

@router.put("/{user_location_id}", response_model=UserLocation)
async def update_user_location(
    user_location_id: int = Path(..., gt=0, description="ユーザー所属ID"),
    user_location_in: UserLocationUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_LOCATIONS)),
) -> Any:
    """
    ユーザー所属情報を更新
    - WRITE_LOCATIONS権限が必要
    """
    user_location = await UserLocationService.get(db, user_location_id)
    if not user_location:
        raise NotFoundException(detail=f"ユーザー所属ID {user_location_id} は存在しません")
    
    updated_user_location = await UserLocationService.update(db, user_location, user_location_in)
    return updated_user_location

@router.delete("/{user_location_id}", response_model=UserLocation)
async def delete_user_location(
    user_location_id: int = Path(..., gt=0, description="ユーザー所属ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_LOCATIONS)),
) -> Any:
    """
    ユーザー所属情報を削除
    - WRITE_LOCATIONS権限が必要
    """
    user_location = await UserLocationService.delete(db, user_location_id)
    return user_location

@router.get("/user/{user_id}", response_model=List[UserLocation])
async def read_user_locations(
    user_id: int = Path(..., gt=0, description="ユーザーID"),
    include_inactive: bool = Query(False, description="終了日が設定されたレコードも含める"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    ユーザーの所属拠点一覧を取得
    - READ_LOCATIONS権限が必要
    """
    # ユーザーの存在確認
    user = await UserService.get(db, user_id)
    if not user:
        raise NotFoundException(detail=f"ユーザーID {user_id} は存在しません")
    
    # ユーザーの所属拠点一覧を取得
    user_locations = await UserLocationService.get_user_locations(
        db=db,
        user_id=user_id,
        include_inactive=include_inactive
    )
    
    return user_locations

@router.post("/check-availability", response_model=dict)
async def check_user_location_availability(
    user_id: int = Query(..., gt=0, description="ユーザーID"),
    location_id: int = Query(..., gt=0, description="拠点ID"),
    start_date: date = Query(..., description="開始日"),
    is_primary: bool = Query(False, description="主所属かどうか"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    ユーザーが指定された日付で拠点に所属可能かチェック
    - READ_LOCATIONS権限が必要
    """
    # ユーザーと拠点の存在確認
    user = await UserService.get(db, user_id)
    location = await LocationService.get(db, location_id)
    
    if not user:
        raise NotFoundException(detail=f"ユーザーID {user_id} は存在しません")
    if not location:
        raise NotFoundException(detail=f"拠点ID {location_id} は存在しません")
    
    # 既存の所属情報をチェック
    existing_assignments = await UserLocationService.get_by_user_location(
        db=db,
        user_id=user_id,
        location_id=location_id,
        include_inactive=True
    )
    
    # 同じ日付で既に所属情報があるかチェック
    conflicts = []
    for assignment in existing_assignments:
        if assignment.end_date is None or assignment.end_date >= start_date:
            conflicts.append({
                "id": assignment.id,
                "start_date": assignment.start_date,
                "end_date": assignment.end_date,
                "is_primary": assignment.is_primary
            })
    
    # 主所属の場合、他の主所属もチェック
    primary_conflicts = []
    if is_primary:
        query = await db.execute(
            select(UserLocation)
            .where(
                and_(
                    UserLocation.user_id == user_id,
                    UserLocation.is_primary == True,
                    or_(
                        UserLocation.end_date == None,
                        UserLocation.end_date >= start_date
                    )
                )
            )
        )
        primary_locations = query.scalars().all()
        for loc in primary_locations:
            if loc.location_id != location_id:
                primary_conflicts.append({
                    "id": loc.id,
                    "location_id": loc.location_id,
                    "start_date": loc.start_date,
                    "end_date": loc.end_date
                })
    
    return {
        "available": len(conflicts) == 0,
        "conflicts": conflicts,
        "primary_conflicts": primary_conflicts,
    }