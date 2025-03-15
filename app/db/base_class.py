"""
ファイル: app/db/base_class.py
説明: SQLAlchemy 2.0のDeclarativeBaseを利用したベースクラス。
      自動テーブル名生成とインスタンスを辞書に変換するユーティリティメソッドを提供します。
"""

from typing import Any, Dict
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer


class Base(DeclarativeBase):
    """
    全てのデータベースモデルの基底クラス

    - クラス名を小文字に変換し、末尾に「s」を付加したテーブル名を自動生成
    - モデルインスタンスを辞書形式に変換するユーティリティメソッドを提供
    """
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        テーブル名を自動生成します（例: クラス名User -> テーブル名users）
        """
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        モデルインスタンスの各カラムを辞書形式に変換します。

        Returns:
            Dict[str, Any]: カラム名とその値の辞書
        """
        try:
            return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        except Exception as error:
            # 必要に応じてログ出力などのエラーハンドリングを追加可能
            raise error