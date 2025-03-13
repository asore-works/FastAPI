from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer
from datetime import datetime


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0の新しいDeclarativeBase構文を使用したベースモデル
    全データベースモデルの基底クラス
    """
    
    # デフォルトのテーブル名自動生成
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # クラス名を小文字に変換し、複数形にしてテーブル名とする
        return f"{cls.__name__.lower()}s"
    
    # TypedなCLASSにすることでIDEの補完が効くように
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 共通メソッド
    def dict(self) -> dict[str, Any]:
        """
        モデルインスタンスを辞書に変換
        
        Returns:
            dict: モデルの属性を表す辞書
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# モデルのインポート
# ここにすべてのモデルをインポートすることで、Alembicがモデルを検出できる
from app.models.user import User  # noqa
from app.models.item import Item  # noqa

# Base.metadata.create_all(bind=engine) は非推奨
# マイグレーションにはAlembicを使用すること