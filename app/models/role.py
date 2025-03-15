"""
app/models/role.py

ユーザーロールのSQLAlchemyデータモデル定義
ロールと権限の永続化を管理
"""

from sqlalchemy import String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.db.base_class import Base

# 型ヒントのための条件付きインポート
if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    """ユーザーロールモデル - SQLAlchemy 2.0の型指定マッピング"""

    name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="ロール名"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="説明"
    )
    permissions: Mapped[str] = mapped_column(Text, comment="権限リスト（JSON文字列）")
    is_system_role: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="システム定義ロールかどうか"
    )

    # リレーションシップ
    if TYPE_CHECKING:
        users: Mapped[List["User"]]
    else:
        users = relationship(
            "User",
            back_populates="role",
            lazy="selectin",  # コレクションのN+1問題回避
        )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
