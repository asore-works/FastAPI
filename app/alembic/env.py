import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# このファイルはalembic.iniに指定された場所に置かれる
# モデルをインポートしてメタデータを公開する
from app.db.base import Base
from app.core.config import settings

# Alembic設定
config = context.config

# セクションがあれば、loggingセクションをファイルロガー設定で解釈する
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ターゲットのメタデータオブジェクト
target_metadata = Base.metadata

# 設定からURLを上書き
# 同期用と非同期用の2つのURLを使用
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


async def run_migrations_online() -> None:
    """
    オンラインマイグレーションの実行
    
    SQLAlchemy 2.0の非同期APIに対応したマイグレーション環境を提供
    """
    # 非同期環境でもマイグレーションは同期的に実行する必要があるため、
    # 一旦同期用のURLを使ってコネクションを取得
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Python 3.10以降では以下のようにasyncioを実行
    asyncio.run(run_migrations_online())