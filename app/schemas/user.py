from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

# 共通のユーザーフィールド
class UserBase(BaseModel):
    """ユーザー基本情報の共通フィールド"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserCreate(BaseModel):
    """ユーザー作成リクエスト"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None
    is_superuser: Optional[bool] = False
    
    # Pydantic v2ではmodel_configを使用
    model_config = ConfigDict(
        extra="forbid",  # 未定義のフィールドを許可しない
    )


class UserUpdate(BaseModel):
    """ユーザー更新リクエスト"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    
    model_config = ConfigDict(
        extra="forbid",
    )


class UserInDBBase(UserBase):
    """データベース内のユーザー情報の基本クラス"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Pydantic v2ではmodel_configを使用（from_attributesパラメータを使用）
    model_config = ConfigDict(
        from_attributes=True,  # SQLAlchemyモデルからの変換を可能に
    )


class User(UserInDBBase):
    """APIレスポンス用ユーザー情報（機密情報なし）"""
    pass


class UserInDB(UserInDBBase):
    """データベース内のユーザー情報（パスワードハッシュを含む）"""
    hashed_password: str


# トークン関連スキーマ
class Token(BaseModel):
    """アクセストークンスキーマ"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """トークンペイロードスキーマ"""
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


# パスワード操作
class PasswordReset(BaseModel):
    """パスワードリセットリクエスト"""
    email: EmailStr
    
    model_config = ConfigDict(
        extra="forbid",
    )


class PasswordResetConfirm(BaseModel):
    """パスワードリセット確認"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    model_config = ConfigDict(
        extra="forbid",
    )