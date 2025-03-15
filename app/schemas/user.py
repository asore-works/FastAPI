"""
app/schemas/user.py

ユーザー関連のPydanticスキーマ定義
ユーザーのAPI入出力とバリデーションを管理
"""

from datetime import datetime
from typing import Optional, List, Union
from pydantic import EmailStr, Field, HttpUrl, field_validator, ConfigDict

from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """ユーザー基本情報の共通フィールド"""
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[EmailStr] = Field(None, title="メールアドレス")
    first_name: Optional[str] = Field(None, title="名")
    last_name: Optional[str] = Field(None, title="姓")
    full_name: Optional[str] = Field(None, title="氏名")
    is_active: Optional[bool] = Field(True, title="アクティブ状態")
    role_id: Optional[int] = Field(None, title="ロールID")
    department: Optional[str] = Field(None, title="部署")
    position: Optional[str] = Field(None, title="役職")
    phone: Optional[str] = Field(None, title="電話番号")
    mobile_phone: Optional[str] = Field(None, title="携帯電話番号")
    employee_id: Optional[str] = Field(None, title="従業員ID")
    address: Optional[str] = Field(None, title="住所")
    profile_image_url: Optional[HttpUrl] = Field(None, title="プロフィール画像URL")
    date_of_birth: Optional[datetime] = Field(None, title="生年月日")
    hire_date: Optional[datetime] = Field(None, title="入社日")


class UserCreate(BaseSchema):
    """ユーザー作成リクエスト"""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr = Field(..., title="メールアドレス")
    password: str = Field(..., min_length=8, max_length=100, title="パスワード")
    first_name: Optional[str] = Field(None, title="名")
    last_name: Optional[str] = Field(None, title="姓")
    full_name: Optional[str] = Field(None, title="氏名")
    is_superuser: Optional[bool] = Field(False, title="管理者権限")
    role_id: Optional[int] = Field(None, title="ロールID")
    department: Optional[str] = Field(None, title="部署")
    position: Optional[str] = Field(None, title="役職")
    employee_id: Optional[str] = Field(None, title="従業員ID")
    phone: Optional[str] = Field(None, title="電話番号")
    mobile_phone: Optional[str] = Field(None, title="携帯電話番号")
    address: Optional[str] = Field(None, title="住所")
    date_of_birth: Optional[datetime] = Field(None, title="生年月日")
    hire_date: Optional[datetime] = Field(None, title="入社日")
    
    # 氏名の自動生成：full_nameが明示的に設定されていない場合、first_nameとlast_nameから生成
    @field_validator('full_name', mode='before')
    @classmethod
    def generate_full_name(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            values = info.data
            first = values.get('first_name', '')
            last = values.get('last_name', '')
            if first or last:
                return f"{last or ''} {first or ''}".strip()
        return v


class UserUpdate(BaseSchema):
    """ユーザー更新リクエスト"""
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[EmailStr] = Field(None, title="メールアドレス")
    first_name: Optional[str] = Field(None, title="名")
    last_name: Optional[str] = Field(None, title="姓")
    full_name: Optional[str] = Field(None, title="氏名")
    password: Optional[str] = Field(None, min_length=8, max_length=100, title="パスワード")
    is_active: Optional[bool] = Field(None, title="アクティブ状態")
    is_superuser: Optional[bool] = Field(None, title="管理者権限")
    role_id: Optional[int] = Field(None, title="ロールID")
    department: Optional[str] = Field(None, title="部署")
    position: Optional[str] = Field(None, title="役職")
    employee_id: Optional[str] = Field(None, title="従業員ID")
    phone: Optional[str] = Field(None, title="電話番号")
    mobile_phone: Optional[str] = Field(None, title="携帯電話番号")
    address: Optional[str] = Field(None, title="住所")
    profile_image_url: Optional[HttpUrl] = Field(None, title="プロフィール画像URL")
    date_of_birth: Optional[datetime] = Field(None, title="生年月日")
    hire_date: Optional[datetime] = Field(None, title="入社日")
    
    # UserCreate と同様の氏名自動生成バリデーション
    @field_validator('full_name', mode='before')
    @classmethod
    def generate_full_name(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            values = info.data
            first = values.get('first_name', '')
            last = values.get('last_name', '')
            if first or last:
                return f"{last or ''} {first or ''}".strip()
        return v


class UserInDBBase(UserBase):
    """データベース内のユーザー情報の基本クラス"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., title="ユーザーID")
    is_superuser: bool = Field(..., title="管理者権限")
    created_at: datetime = Field(..., title="作成日時")
    updated_at: datetime = Field(..., title="更新日時")
    last_login: Optional[datetime] = Field(None, title="最終ログイン日時")


class User(UserInDBBase):
    """APIレスポンス用ユーザー情報"""
    model_config = ConfigDict(from_attributes=True)
    pass


class UserWithRole(User):
    """ロール情報を含むユーザー情報"""
    model_config = ConfigDict(from_attributes=True)
    role: Optional["Role"] = Field(None, title="ユーザーロール")


# 循環参照回避のための更新
from app.schemas.role import Role
UserWithRole.model_rebuild()