import asyncio
from logging.config import fileConfig
import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, project_root)

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# このファイルはalembic.iniに指定された場所に置かれる
# 共通のBase classをインポート
from app.db.base_class import Base

# すべてのモデルをインポートするためにbase.pyをインポート（これにより間接的にすべてのモデルがロード）
import app.db.base

# 設定モジュールをインポート
from app.core.config import settings

# Alembic設定
config = context.config

# セクションがあれば、loggingセクションをファイルロガー設定で解釈する
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ターゲットのメタデータオブジェクト
target_metadata = Base.metadata

# 設定からURLを上書き
# 同期用のURLを設定（alembic.iniのsqlalchemy.urlを上書き）
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)


def run_migrations_offline() -> None:
    """
    オフラインマイグレーションの実行
    
    SQLAlchemyエンジンを使用せずに直接接続するマイグレーション環境を実行
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    マイグレーション実行
    
    同期コンテキストでマイグレーションを実行
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # compare_type=Trueとすると型の変更も検出される
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    非同期マイグレーションランナー
    
    SQLAlchemy 2.0の非同期APIに対応したマイグレーション環境を提供
    """
    # 設定から非同期エンジンを作成
    config_section = config.get_section(config.config_ini_section)
    
    # URI を非同期用に上書き (オリジナルを保存)
    db_url = config_section.get("sqlalchemy.url")
    config_section["sqlalchemy.url"] = settings.DATABASE_URL
    
    # 非同期エンジン作成
    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    # 接続後、同期コンテキストで実行
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    # エンジンをクローズ
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    オンラインマイグレーションの実行（同期版）
    
    非同期機能が利用できない場合のフォールバック
    """
    # 同期エンジンを作成
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        do_run_migrations(connection)
    
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # マイグレーションを実行
    # 非同期APIを使用してマイグレーションを実行
    try:
        # Python 3.10+では asyncio.run() を使用
        asyncio.run(run_async_migrations())
    except Exception as e:
        print(f"非同期マイグレーションでエラーが発生: {e}")
        print("同期モードにフォールバックします...")
        run_migrations_online()