from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_current_active_superuser
from app.core.permissions import has_permission, Permission
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.schemas.role import Role, RoleCreate, RoleUpdate
from app.services.role import RoleService

router = APIRouter()

@router.get("/", response_model=List[Role])
async def read_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_system_roles: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_ROLES)),
) -> Any:
    """
    ロール一覧を取得
    - 管理者権限が必要
    """
    roles = await RoleService.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        include_system_roles=include_system_roles
    )
    return roles

@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_ROLES)),
) -> Any:
    """
    新規ロールを作成
    - 管理者権限が必要
    """
    role = await RoleService.create(db, role_in)
    return role

@router.get("/{role_id}", response_model=Role)
async def read_role(
    role_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.READ_ROLES)),
) -> Any:
    """
    特定のロール情報を取得
    - 管理者権限が必要
    """
    role = await RoleService.get(db, role_id)
    if not role:
        raise NotFoundException(detail=f"Role with ID {role_id} not found")
    return role

@router.put("/{role_id}", response_model=Role)
async def update_role(
    role_id: int = Path(..., gt=0),
    role_in: RoleUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_ROLES)),
) -> Any:
    """
    ロール情報を更新
    - 管理者権限が必要
    - システムロールは更新できない
    """
    role = await RoleService.get(db, role_id)
    if not role:
        raise NotFoundException(detail=f"Role with ID {role_id} not found")
    
    role = await RoleService.update(db, role, role_in)
    return role

@router.delete("/{role_id}", response_model=Role)
async def delete_role(
    role_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_permission(Permission.WRITE_ROLES)),
) -> Any:
    """
    ロールを削除
    - 管理者権限が必要
    - システムロールは削除できない
    """
    role = await RoleService.delete(db, role_id)
    return role

@router.post("/initialize", status_code=status.HTTP_204_NO_CONTENT)
async def initialize_system_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """
    システムロールを初期化
    - スーパーユーザー権限が必要
    """
    await RoleService.initialize_system_roles(db)
    return None