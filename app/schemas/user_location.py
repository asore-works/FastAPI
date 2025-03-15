"""
app/schemas/user_location.py

ユーザーと拠点の関連を管理するPydanticスキーマ定義
ユーザーの拠点所属情報のAPI入出力を管理
"""

from pydantic import Field, field_validator
from datetime import date, datetime
from typing import Optional, List

from app.schemas.base import BaseSchema
from app.schemas.user import User

# ユーザー所属の基本情報
class UserLocationBase(BaseSchema):
    """ユーザー所属の基本情報スキーマ"""
    user_id: int = Field(..., title="ユーザーID")
    location_id: int = Field(..., title="拠点ID")
    is_primary: bool = Field(True, title="主所属かどうか")
    position: Optional[str] = Field(None, title="拠点内での役職")
    department: Optional[str] = Field(None, title="拠点内での部署")
    start_date: date = Field(..., title="所属開始日")
    end_date: Optional[date] = Field(None, title="所属終了日")
    notes: Optional[str] = Field(None, title="備考")

    # 日付バリデーション
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info):
        if v is not None:
            start_date = info.data.get('start_date')
            if start_date and v < start_date:
                raise ValueError("終了日は開始日より後である必要があります")
        return v

# ユーザー所属作成リクエスト
class UserLocationCreate(UserLocationBase):
    """ユーザー所属作成リクエスト"""
    start_date: date = Field(default_factory=date.today, title="所属開始日")

# ユーザー所属更新リクエスト
class UserLocationUpdate(BaseSchema):
    """ユーザー所属更新リクエスト"""
    is_primary: Optional[bool] = Field(None, title="主所属かどうか")
    position: Optional[str] = Field(None, title="拠点内での役職")
    department: Optional[str] = Field(None, title="拠点内での部署")
    start_date: Optional[date] = Field(None, title="所属開始日")
    end_date: Optional[date] = Field(None, title="所属終了日")
    notes: Optional[str] = Field(None, title="備考")

    # 日付バリデーション
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info):
        if v is not None:
            start_date = info.data.get('start_date')
            if start_date and v < start_date:
                raise ValueError("終了日は開始日より後である必要があります")
        return v

# データベース内のユーザー所属情報
class UserLocationInDBBase(UserLocationBase):
    """データベース内のユーザー所属情報"""
    id: int = Field(..., title="ID")
    created_at: datetime = Field(..., title="作成日時")
    updated_at: datetime = Field(..., title="更新日時")

# API応答用ユーザー所属情報
class UserLocation(UserLocationInDBBase):
    """API応答用ユーザー所属情報"""
    pass

# ユーザー情報を含むユーザー所属情報
class UserLocationWithUser(UserLocation):
    """ユーザー情報を含むユーザー所属情報"""
    user: User = Field(..., title="ユーザー")

# 拠点所属ユーザー一覧ページネーション
class UserLocationPage(BaseSchema):
    """ページネーション付き拠点所属ユーザー一覧"""
    items: List[UserLocationWithUser] = Field(..., title="ユーザー所属リスト")
    total: int = Field(..., title="総件数")
    page: int = Field(..., title="現在のページ")
    size: int = Field(..., title="ページサイズ")
    pages: int = Field(..., title="総ページ数")