#!/bin/sh

# UniCore Docker エントリーポイントスクリプト
# コンテナ起動時の初期処理を行う

set -e

# カラー設定
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}UniCore API サーバーを開始しています...${NC}"

# 環境変数のチェック
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}警告: DATABASE_URL が設定されていません。代わりに個別の設定を使用します。${NC}"
fi

# データベース接続が確立されるまで待機
echo -e "${GREEN}データベース接続を確認しています...${NC}"
python -c "
import time
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def check_db():
    for i in range(30):
        try:
            # 非同期エンジンを作成して接続テスト
            engine = create_async_engine(settings.DATABASE_URL)
            async with engine.connect() as conn:
                await conn.execute('SELECT 1')
            print('データベースへの接続に成功しました')
            return True
        except Exception as e:
            print(f'データベース接続待機中... {i+1}/30 ({e})')
            await asyncio.sleep(1)
    print('データベース接続のタイムアウト')
    return False

if not asyncio.run(check_db()):
    exit(1)
"

# マイグレーションの実行（自動マイグレーションが有効な場合）
if [ "$AUTO_MIGRATE" = "true" ]; then
    echo -e "${GREEN}データベースマイグレーションを実行しています...${NC}"
    alembic upgrade head
    
    # 初期データの設定
    echo -e "${GREEN}初期データを設定しています...${NC}"
    python -m app.db.init_db
fi

# 本番環境設定の確認
if [ "$APP_ENV" = "production" ]; then
    echo -e "${GREEN}本番環境で実行しています${NC}"
    # Gunicornの設定
    WORKERS=${GUNICORN_WORKERS:-"4"}
    TIMEOUT=${GUNICORN_TIMEOUT:-"120"}
    
    # Gunicornを使用して起動
    exec gunicorn app.main:app \
        --bind 0.0.0.0:8000 \
        --workers $WORKERS \
        --worker-class uvicorn.workers.UvicornWorker \
        --timeout $TIMEOUT
else
    echo -e "${GREEN}開発環境で実行しています${NC}"
    # Uvicornを使用して起動
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi