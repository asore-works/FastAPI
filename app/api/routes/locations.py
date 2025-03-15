"""
app/api/routes/locations.py

拠点（ロケーション）関連のAPI定義
拠点の管理に関するエンドポイントを提供
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.core.permissions import has_permission, Permission
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.models.location import LocationType
from app.schemas.location import (
    Location, LocationCreate, LocationUpdate,
    LocationWithDetails, LocationPage
)
from app.schemas.user_location import UserLocationPage
from app.services.location import LocationService
from app.services.user_location import UserLocationService

router = APIRouter()

@router.get("/", response_model=LocationPage)
async def read_locations(
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    type: Optional[LocationType] = Query(None, description="拠点タイプでフィルタ"),
    parent_id: Optional[int] = Query(None, description="親拠点IDでフィルタ"),
    is_active: Optional[bool] = Query(None, description="アクティブ状態でフィルタ"),
    search: Optional[str] = Query(None, description="名前またはコードで検索"),
    prefecture: Optional[str] = Query(None, description="都道府県でフィルタ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    拠点一覧を取得（ページネーション、フィルタリング機能付き）
    - READ_LOCATIONS権限が必要
    """
    locations_page = await LocationService.get_page(
        db=db,
        page=page,
        size=size,
        type=type,
        parent_id=parent_id,
        is_active=is_active,
        search=search,
        prefecture=prefecture,
    )
    return locations_page

@router.post("/", response_model=Location, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_LOCATIONS)),
) -> Any:
    """
    新しい拠点を作成
    - WRITE_LOCATIONS権限が必要
    """
    location = await LocationService.create(db, location_in)
    return location

@router.get("/types", response_model=List[dict])
async def read_location_types(
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    拠点タイプの一覧を取得
    - READ_LOCATIONS権限が必要
    """
    return [
        {"value": type.value, "label": type.name}
        for type in LocationType
    ]

@router.get("/{location_id}", response_model=LocationWithDetails)
async def read_location(
    location_id: int = Path(..., gt=0, description="拠点ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    特定の拠点情報を取得（親拠点、子拠点情報を含む）
    - READ_LOCATIONS権限が必要
    """
    location = await LocationService.get(db, location_id)
    if not location:
        raise NotFoundException(detail=f"拠点ID {location_id} は存在しません")
    
    # ユーザー数をカウント
    user_count = len(location.users) if location.users else 0
    
    # LocationWithDetailsスキーマにマッピング
    result = LocationWithDetails.model_validate(location)
    result.user_count = user_count
    
    return result

@router.get("/code/{code}", response_model=LocationWithDetails)
async def read_location_by_code(
    code: str = Path(..., description="拠点コード"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    拠点コードによる拠点情報取得（親拠点、子拠点情報を含む）
    - READ_LOCATIONS権限が必要
    """
    location = await LocationService.get_by_code(db, code)
    if not location:
        raise NotFoundException(detail=f"拠点コード '{code}' は存在しません")
    
    # ユーザー数をカウント
    user_count = len(location.users) if location.users else 0
    
    # LocationWithDetailsスキーマにマッピング
    result = LocationWithDetails.model_validate(location)
    result.user_count = user_count
    
    return result

@router.put("/{location_id}", response_model=Location)
async def update_location(
    location_id: int = Path(..., gt=0, description="拠点ID"),
    location_in: LocationUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_LOCATIONS)),
) -> Any:
    """
    拠点情報を更新
    - WRITE_LOCATIONS権限が必要
    """
    location = await LocationService.get(db, location_id)
    if not location:
        raise NotFoundException(detail=f"拠点ID {location_id} は存在しません")
    
    updated_location = await LocationService.update(db, location, location_in)
    return updated_location

@router.delete("/{location_id}", response_model=Location)
async def delete_location(
    location_id: int = Path(..., gt=0, description="拠点ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.MANAGE_LOCATIONS)),
) -> Any:
    """
    拠点を削除（子拠点がある場合は拒否される）
    - MANAGE_LOCATIONS権限が必要
    """
    location = await LocationService.delete(db, location_id)
    return location

@router.get("/{location_id}/users", response_model=UserLocationPage)
async def read_location_users(
    location_id: int = Path(..., gt=0, description="拠点ID"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    include_inactive: bool = Query(False, description="終了日が設定されたレコードも含める"),
    search: Optional[str] = Query(None, description="ユーザー名または従業員IDで検索"),
    is_primary: Optional[bool] = Query(None, description="主所属かどうかでフィルタ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_LOCATIONS)),
) -> Any:
    """
    拠点に所属するユーザー一覧を取得
    - READ_LOCATIONS権限が必要
    """
    # 拠点の存在確認
    location = await LocationService.get(db, location_id)
    if not location:
        raise NotFoundException(detail=f"拠点ID {location_id} は存在しません")
    
    # 拠点所属ユーザー一覧を取得
    user_locations = await UserLocationService.get_location_users_page(
        db=db,
        location_id=location_id,
        page=page,
        size=size,
        include_inactive=include_inactive,
        search=search,
        is_primary=is_primary
    )
    
    return user_locations