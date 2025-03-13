from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from app.db.base_class import Base

# 型ヒントのための条件付きインポート
if TYPE_CHECKING:
    from app.models.item import Item


class User(Base):
    """
    ユーザーモデル
    SQLAlchemy 2.0の型指定マッピングを使用
    """
    # 必須フィールド
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # プロフィール情報
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # ステータスフラグ
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 監査フィールド - SQLAlchemy 2.0のserver_defaultを使用した自動タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # リレーションシップ - 遅延評価のために文字列型参照を使用
    # SQLAlchemy 2.0では、ここで文字列参照を使用するとモジュールのロード順序の問題が解決されます
    if TYPE_CHECKING:
        items: Mapped[List["Item"]]
    else:
        items = relationship(
            "Item", 
            back_populates="owner",
            cascade="all, delete-orphan",
        )

    def __repr__(self) -> str:
        return f"<User {self.email}>"