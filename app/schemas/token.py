"""
app/schemas/token.py

認証トークン関連のPydanticスキーマ定義
JWTトークンのペイロードなど、認証情報のスキーマを管理します。
"""

from pydantic import BaseModel, Field, ConfigDict

class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str = Field(..., title="アクセストークン")
    token_type: str = Field(..., title="トークンタイプ")

class TokenPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sub: str = Field(..., title="サブジェクト")
    exp: int = Field(..., title="有効期限 (UNIXタイムスタンプ)")
    # もしトークンタイプのフィールドが必要なら追加可能（例: type: str）