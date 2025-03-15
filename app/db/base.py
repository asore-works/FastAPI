"""
ファイル: app/db/base.py
説明: Alembicマイグレーション用にモデルを一括インポートするモジュール。
      すべてのモデルをインポートすることで、Alembicがモデルを検出できるようにします。
"""

from app.db.base_class import Base
import app.models  # Alembicによるマイグレーション検出のために全モデルをインポート