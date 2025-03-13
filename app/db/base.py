# モデルをインポートする集約モジュール
# Alembicがモデルを検出するために使用します

from app.db.base_class import Base

# モデルをインポート - Alembicのマイグレーション検出用
# 注意: 循環インポートを避けるためにbase_classとは別ファイルにしています
import app.models

# Base.metadata.create_all(bind=engine) は非推奨
# マイグレーションにはAlembicを使用すること