"""
app/models/user.py

ユーザーのSQLAlchemyデータモデル定義
ユーザー情報の永続化と関連リレーションシップを管理
"""

from sqlalchemy import Boolean, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from app.db.base_class import Base

# 型ヒントのための条件付きインポート
if TYPE_CHECKING:
    from app.models.role import Role


class User(Base):
    """ユーザーモデル - SQLAlchemy 2.0の型指定マッピング"""

    # メインフィールド - 必須
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="メールアドレス"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="ハッシュ化パスワード"
    )

    # 基本情報
    first_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="名"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="姓"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="氏名"
    )

    # 役割と権限
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="アクティブ状態"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="管理者権限"
    )
    role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, comment="ロールID"
    )

    # 組織情報
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, unique=True, comment="従業員ID"
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="部署"
    )
    position: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="役職"
    )

    # 連絡先情報
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="電話番号"
    )
    mobile_phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="携帯電話番号"
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="住所"
    )
    profile_image_url: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="プロフィール画像URL"
    )

    # 日付情報
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="生年月日"
    )
    hire_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="入社日"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="最終ログイン日時"
    )

    # 監査フィールド - SQLAlchemy 2.0のserver_defaultを使用
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False, comment="作成日時"
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新日時",
    )

    # パフォーマンス向上のためのインデックス
    __table_args__ = (
        # 名前検索用の複合インデックス
        Index("ix_users_name_search", "last_name", "first_name", "full_name"),
        # 部署と役職用のインデックス
        Index("ix_users_department_position", "department", "position"),
    )

    # リレーションシップ
    if TYPE_CHECKING:
        role: Mapped["Role"]
        locations: Mapped[List["UserLocation"]]
    else:
        role = relationship(
            "Role",
            back_populates="users",
            lazy="joined",  # N+1問題回避のためJOINEDローディング
        )
        locations = relationship(
            "UserLocation", back_populates="user", cascade="all, delete-orphan"
        )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
