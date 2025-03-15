"""
app/schemas/role.py

ユーザーロール関連のPydanticスキーマ定義
ロールとそれに関連する権限情報のスキーマを管理
"""

from pydantic import Field, field_validator, ConfigDict
from typing import Optional, List
from app.core.permissions import Permission
from app.schemas.base import BaseSchema

# キャッシュ: 定義されている権限の集合を一度だけ計算しておく
_VALID_PERMISSIONS: set[str] = {p.value for p in Permission}


class RoleBase(BaseSchema):
    """ロール基本情報の共通フィールド"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., title="ロール名")
    description: Optional[str] = Field(None, title="説明")
    permissions: List[str] = Field(default=[], title="権限リスト")

    # 権限バリデーション
    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: List[str]) -> List[str]:
        for perm in v:
            if perm not in _VALID_PERMISSIONS:
                raise ValueError(f"無効な権限です: {perm}")
        return v


class RoleCreate(RoleBase):
    """ロール作成リクエスト"""
    # RoleBase の全フィールドを継承
    pass


class RoleUpdate(BaseSchema):
    """ロール更新リクエスト"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, title="ロール名")
    description: Optional[str] = Field(None, title="説明")
    permissions: Optional[List[str]] = Field(None, title="権限リスト")

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for perm in v:
            if perm not in _VALID_PERMISSIONS:
                raise ValueError(f"無効な権限です: {perm}")
        return v


class RoleInDBBase(RoleBase):
    """データベース内のロール情報の基本クラス"""
    id: int = Field(..., title="ロールID")
    is_system_role: bool = Field(..., title="システムロール")


class Role(RoleInDBBase):
    """APIレスポンス用ロール情報"""
    pass