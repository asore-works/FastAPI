from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# 共通のアイテムフィールド
class ItemBase(BaseModel):
    """アイテム基本情報の共通フィールド"""
    title: Optional[str] = None
    description: Optional[str] = None


class ItemCreate(BaseModel):
    """アイテム作成リクエスト"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Pydantic v2ではmodel_configを使用
    model_config = ConfigDict(
        extra="forbid",  # 未定義のフィールドを許可しない
    )


class ItemUpdate(BaseModel):
    """アイテム更新リクエスト"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    model_config = ConfigDict(
        extra="forbid",
    )


class ItemInDBBase(ItemBase):
    """データベース内のアイテム情報の基本クラス"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    # Pydantic v2ではmodel_configを使用
    model_config = ConfigDict(
        from_attributes=True,  # SQLAlchemyモデルからの変換を可能に
    )


class Item(ItemInDBBase):
    """APIレスポンス用アイテム情報"""
    pass


# リスト表示用のページネーションレスポンス
class ItemPage(BaseModel):
    """ページネーション付きアイテムリスト"""
    items: list[Item]
    total: int
    page: int
    size: int
    pages: int
    
    model_config = ConfigDict(
        from_attributes=True,
    )