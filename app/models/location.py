"""
app/models/location.py

拠点（ロケーション）のSQLAlchemyデータモデル定義
拠点情報の永続化と階層構造の管理を行う
"""

from enum import Enum as PyEnum
from sqlalchemy import String, Text, Boolean, ForeignKey, Index, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from app.db.base_class import Base

# 拠点タイプの列挙型
class LocationType(str, PyEnum):
    """
    拠点タイプの列挙型
    各拠点の種類を明確に分類するために使用
    """
    HEADQUARTERS = "headquarters"  # 本社
    BRANCH = "branch"              # 支店
    OFFICE = "office"              # 営業所
    WAREHOUSE = "warehouse"        # 倉庫
    STORE = "store"                # 店舗
    OTHER = "other"                # その他


class Location(Base):
    """
    拠点モデル - SQLAlchemy 2.0の型指定マッピング
    企業や組織の拠点情報を管理する
    階層構造（親子関係）をサポート
    """
    
    # 基本情報
    name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False,
        comment="拠点名"
    )
    code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False,
        comment="拠点コード"
    )
    type: Mapped[LocationType] = mapped_column(
        Enum(LocationType), nullable=False,
        comment="拠点タイプ"
    )
    
    # 親拠点への参照（自己参照）
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True,
        comment="親拠点ID"
    )
    
    # 住所・連絡先情報
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="郵便番号"
    )
    prefecture: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="都道府県"
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="市区町村"
    )
    address1: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="住所1（町名・番地）"
    )
    address2: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="住所2（建物名・部屋番号）"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="電話番号"
    )
    fax: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="FAX番号"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="メールアドレス"
    )
    
    # 営業情報
    business_hours: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="営業時間"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="説明"
    )
    
    # 管理情報
    manager_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="管理者名"
    )
    capacity: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="収容人数"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="アクティブ状態"
    )
    
    # 地理情報（将来的に地図表示などに使用可能）
    latitude: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="緯度"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="経度"
    )
    
    # 日付情報
    established_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="設立日"
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
    
    # インデックス設定
    __table_args__ = (
        # 住所検索用の複合インデックス
        Index("ix_locations_address", "prefecture", "city"),
        # 拠点タイプと名前の複合インデックス
        Index("ix_locations_type_name", "type", "name"),
    )
    
    # リレーションシップ
    if TYPE_CHECKING:
        parent: Mapped[Optional["Location"]]
        children: Mapped[List["Location"]]
        users: Mapped[List["UserLocation"]]
    else:
        # 親拠点（自己参照）
        parent = relationship(
            "Location", 
            remote_side="Location.id",
            back_populates="children",
            lazy="joined"
        )
        # 子拠点（自己参照）
        children = relationship(
            "Location", 
            back_populates="parent",
            cascade="all, delete-orphan",
            lazy="selectin"
        )
        # ユーザー割り当て
        users = relationship(
            "UserLocation", 
            back_populates="location",
            cascade="all, delete-orphan",
            lazy="selectin"
        )
        # 在庫アイテム（追加予定）
        # inventory_items = relationship("InventoryItem", back_populates="location")
        
    def __repr__(self) -> str:
        return f"<Location {self.name} ({self.code})>"