"""
app/models/user_location.py

ユーザーと拠点の関連を管理するSQLAlchemyデータモデル定義
ユーザーの拠点への割り当て・異動履歴を管理する
"""

from sqlalchemy import ForeignKey, Boolean, String, Date, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime

from app.db.base_class import Base

class UserLocation(Base):
    """
    ユーザーと拠点の関連モデル - SQLAlchemy 2.0の型指定マッピング
    ユーザーの拠点所属情報を管理し、異動履歴を含む
    """
    
    # リレーションキー（複合主キーではなく、独自のIDを持つ設計）
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ユーザーID"
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="拠点ID"
    )
    
    # 所属情報
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="主所属かどうか"
    )
    position: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="拠点内での役職"
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="拠点内での部署"
    )
    
    # 期間情報
    start_date: Mapped[date] = mapped_column(
        server_default=func.current_date(),
        comment="所属開始日"
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        nullable=True,
        comment="所属終了日"
    )
    
    # 備考
    notes: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="備考"
    )
    
    # 監査フィールド
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False,
        comment="作成日時"
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False,
        comment="更新日時"
    )
    
    # ユニーク制約：同じユーザーと拠点の組み合わせで有効期間が重複しないようにする
    __table_args__ = (
        UniqueConstraint('user_id', 'location_id', 'is_primary', name='uq_user_location_primary'),
    )
    
    # リレーションシップ
    if TYPE_CHECKING:
        user: Mapped["User"]
        location: Mapped["Location"]
    else:
        user = relationship("User", back_populates="locations")
        location = relationship("Location", back_populates="users")
        
    def __repr__(self) -> str:
        return f"<UserLocation {self.user_id}@{self.location_id}>"