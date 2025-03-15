"""
app/schemas/base.py

共通のPydanticスキーマ基底クラス定義
ファイル内で再利用可能な基本設定と共通機能を提供
"""

from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """共通の基本スキーマ設定"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,  # 文字列の前後の空白を自動除去
        validate_assignment=True,   # 属性代入時もバリデーション
    )