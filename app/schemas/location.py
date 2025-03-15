"""
app/schemas/location.py

拠点（ロケーション）関連のPydanticスキーマ定義
API入出力のバリデーションとシリアライズを管理
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Union
from app.models.location import LocationType

from app.schemas.base import BaseSchema

# 拠点の基本情報
class LocationBase(BaseSchema):
    """拠点の基本情報スキーマ"""
    name: str = Field(..., title="拠点名")
    code: str = Field(..., title="拠点コード", pattern="^[A-Za-z0-9\\-_]{2,20}$")
    type: LocationType = Field(..., title="拠点タイプ")
    parent_id: Optional[int] = Field(None, title="親拠点ID")
    postal_code: Optional[str] = Field(None, title="郵便番号")
    prefecture: Optional[str] = Field(None, title="都道府県")
    city: Optional[str] = Field(None, title="市区町村")
    address1: Optional[str] = Field(None, title="住所1")
    address2: Optional[str] = Field(None, title="住所2")
    phone: Optional[str] = Field(None, title="電話番号")
    fax: Optional[str] = Field(None, title="FAX番号")
    email: Optional[str] = Field(None, title="メールアドレス")
    business_hours: Optional[str] = Field(None, title="営業時間")
    description: Optional[str] = Field(None, title="説明")
    manager_name: Optional[str] = Field(None, title="管理者名")
    capacity: Optional[int] = Field(None, ge=0, title="収容人数")
    is_active: bool = Field(True, title="アクティブ状態")
    latitude: Optional[float] = Field(None, title="緯度")
    longitude: Optional[float] = Field(None, title="経度")
    established_date: Optional[datetime] = Field(None, title="設立日")

    # 拠点コードのバリデーション
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v:
            raise ValueError("拠点コードは必須です")
        if len(v) < 2 or len(v) > 20:
            raise ValueError("拠点コードは2〜20文字である必要があります")
        if not all(c.isalnum() or c in ['-', '_'] for c in v):
            raise ValueError("拠点コードには英数字、ハイフン、アンダースコアのみ使用できます")
        return v.upper()  # 常に大文字に正規化

# 拠点作成リクエスト
class LocationCreate(LocationBase):
    """拠点作成リクエスト"""
    pass

# 拠点更新リクエスト
class LocationUpdate(BaseSchema):
    """拠点更新リクエスト"""
    name: Optional[str] = Field(None, title="拠点名")
    code: Optional[str] = Field(None, title="拠点コード", pattern="^[A-Za-z0-9\\-_]{2,20}$")
    type: Optional[LocationType] = Field(None, title="拠点タイプ")
    parent_id: Optional[int] = Field(None, title="親拠点ID")
    postal_code: Optional[str] = Field(None, title="郵便番号")
    prefecture: Optional[str] = Field(None, title="都道府県")
    city: Optional[str] = Field(None, title="市区町村")
    address1: Optional[str] = Field(None, title="住所1")
    address2: Optional[str] = Field(None, title="住所2")
    phone: Optional[str] = Field(None, title="電話番号")
    fax: Optional[str] = Field(None, title="FAX番号")
    email: Optional[str] = Field(None, title="メールアドレス")
    business_hours: Optional[str] = Field(None, title="営業時間")
    description: Optional[str] = Field(None, title="説明")
    manager_name: Optional[str] = Field(None, title="管理者名")
    capacity: Optional[int] = Field(None, ge=0, title="収容人数")
    is_active: Optional[bool] = Field(None, title="アクティブ状態")
    latitude: Optional[float] = Field(None, title="緯度")
    longitude: Optional[float] = Field(None, title="経度")
    established_date: Optional[datetime] = Field(None, title="設立日")

    # 拠点コードのバリデーション（LocationBaseと同じ）
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) < 2 or len(v) > 20:
            raise ValueError("拠点コードは2〜20文字である必要があります")
        if not all(c.isalnum() or c in ['-', '_'] for c in v):
            raise ValueError("拠点コードには英数字、ハイフン、アンダースコアのみ使用できます")
        return v.upper()  # 常に大文字に正規化

# データベース内の拠点基本情報
class LocationInDBBase(LocationBase):
    """データベース内の拠点情報"""
    id: int = Field(..., title="拠点ID")
    created_at: datetime = Field(..., title="作成日時")
    updated_at: datetime = Field(..., title="更新日時")
    
    model_config = ConfigDict(from_attributes=True)

# API応答用拠点情報
class Location(LocationInDBBase):
    """API応答用の拠点情報"""
    pass

# 詳細情報付き拠点情報
class LocationWithDetails(Location):
    """詳細情報（親拠点と子拠点）を含む拠点情報"""
    parent: Optional[Location] = Field(None, title="親拠点")
    children: List[Location] = Field(default=[], title="子拠点")
    user_count: int = Field(0, title="所属ユーザー数")

# 拠点一覧ページネーション
class LocationPage(BaseSchema):
    """ページネーション付き拠点一覧"""
    items: List[Location] = Field(..., title="拠点リスト")
    total: int = Field(..., title="総件数")
    page: int = Field(..., title="現在のページ")
    size: int = Field(..., title="ページサイズ")
    pages: int = Field(..., title="総ページ数")