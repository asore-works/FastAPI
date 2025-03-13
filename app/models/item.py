from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.db.base_class import Base

# 型ヒントのための条件付きインポート
if TYPE_CHECKING:
    from app.models.user import User


class Item(Base):
    """
    アイテムモデル（サンプル）
    SQLAlchemy 2.0の型指定マッピングを使用
    """
    # 必須フィールド
    title: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    
    # 任意フィールド
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # 外部キー - SQLAlchemy 2.0のForeignKeyを使用
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # 監査フィールド
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # リレーションシップ
    # SQLAlchemy 2.0では、ここで文字列参照を使用するとモジュールのロード順序の問題が解決されます
    if TYPE_CHECKING:
        owner: Mapped["User"]
    else:
        owner = relationship(
            "User", 
            back_populates="items",
        )

    def __repr__(self) -> str:
        return f"<Item {self.title}>"