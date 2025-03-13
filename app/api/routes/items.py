from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, oauth2_scheme
from app.core.exceptions import NotFoundException, ForbiddenException
from app.db.session import get_db
from app.models.user import User
from app.models.item import Item
from app.schemas.item import Item as ItemSchema, ItemCreate, ItemUpdate, ItemPage
from app.services.item import ItemService

router = APIRouter()


@router.get("/", response_model=ItemPage)
async def read_items(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    アイテム一覧を取得（ページネーション付き）
    - 管理者: 全アイテムの一覧を取得可能
    - 一般ユーザー: 自分のアイテムのみ取得可能
    """
    # 管理者以外は自分のアイテムのみ表示
    owner_id = None if current_user.is_superuser else current_user.id
    
    # ページネーション付きでアイテム取得
    items_page = await ItemService.get_page(
        db=db,
        page=page,
        size=size,
        owner_id=owner_id,
    )
    
    return items_page


@router.post("/", response_model=ItemSchema, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    新しいアイテムを作成
    """
    item = await ItemService.create(db, item_in, owner_id=current_user.id)
    return item


@router.get("/{item_id}", response_model=ItemSchema)
async def read_item(
    item_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    特定のアイテム情報を取得
    - 管理者: 全アイテムの情報を取得可能
    - 一般ユーザー: 自分のアイテムのみ取得可能
    """
    item = await ItemService.get(db, item_id)
    if not item:
        raise NotFoundException(detail=f"Item with ID {item_id} not found")
    
    # アクセス権限チェック
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise ForbiddenException(detail="Not enough permissions")
    
    return item


@router.put("/{item_id}", response_model=ItemSchema)
async def update_item(
    item_id: int = Path(..., gt=0),
    item_in: ItemUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    アイテム情報を更新
    - 管理者: 全アイテムを更新可能
    - 一般ユーザー: 自分のアイテムのみ更新可能
    """
    item = await ItemService.get(db, item_id)
    if not item:
        raise NotFoundException(detail=f"Item with ID {item_id} not found")
    
    # アクセス権限チェック
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise ForbiddenException(detail="Not enough permissions")
    
    item = await ItemService.update(db, item, item_in)
    return item


@router.delete("/{item_id}", response_model=ItemSchema)
async def delete_item(
    item_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    アイテムを削除
    - 管理者: 全アイテムを削除可能
    - 一般ユーザー: 自分のアイテムのみ削除可能
    """
    item = await ItemService.get(db, item_id)
    if not item:
        raise NotFoundException(detail=f"Item with ID {item_id} not found")
    
    # アクセス権限チェック
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise ForbiddenException(detail="Not enough permissions")
    
    item = await ItemService.delete(db, item_id)
    return item