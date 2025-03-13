#!/bin/bash

# UniCore データベースマイグレーションスクリプト
# PostgreSQL 17とSQLAlchemy 2.0の非同期環境向け

set -e

# カラー設定
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 現在のディレクトリを保存
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# プロジェクトルートに移動
cd "$PROJECT_ROOT"

# 引数のチェック
if [ "$#" -lt 1 ]; then
    echo -e "${RED}エラー: コマンドが指定されていません${NC}"
    echo -e "${YELLOW}使用法: $0 [コマンド]${NC}"
    echo "コマンド:"
    echo "  init         - マイグレーション環境を初期化"
    echo "  create       - 新しいマイグレーションを作成"
    echo "  upgrade      - 最新バージョンにアップグレード"
    echo "  downgrade    - 1つ前のバージョンにダウングレード"
    echo "  version      - 現在のバージョンを表示"
    echo "  history      - マイグレーション履歴を表示"
    echo "  reset        - データベースをリセット (危険操作)"
    exit 1
fi

# コマンドを取得
COMMAND=$1
shift

# 環境変数読み込み
if [ -f .env ]; then
    echo -e "${GREEN}環境変数を.envから読み込んでいます...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# コマンド実行関数
alembic_command() {
    echo -e "${GREEN}実行: alembic $@${NC}"
    alembic $@
}

# コマンド処理
case "$COMMAND" in
    init)
        echo -e "${GREEN}マイグレーション環境を初期化しています...${NC}"
        alembic_command init app/alembic
        ;;
    create)
        if [ "$#" -lt 1 ]; then
            echo -e "${RED}エラー: マイグレーション名を指定してください${NC}"
            echo -e "${YELLOW}使用法: $0 create <マイグレーション名>${NC}"
            exit 1
        fi
        echo -e "${GREEN}新しいマイグレーション '$1' を作成しています...${NC}"
        alembic_command revision --autogenerate -m "$1"
        ;;
    upgrade)
        TARGET=${1:-"head"}
        echo -e "${GREEN}データベースを '$TARGET' にアップグレードしています...${NC}"
        alembic_command upgrade $TARGET
        # 初期管理者ユーザーの作成
        echo -e "${GREEN}初期データを設定しています...${NC}"
        python -m app.db.init_db
        ;;
    downgrade)
        TARGET=${1:-"-1"}
        echo -e "${YELLOW}警告: データベースを '$TARGET' にダウングレードします${NC}"
        read -p "続行しますか？ (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            alembic_command downgrade $TARGET
        else
            echo -e "${GREEN}ダウングレードをキャンセルしました${NC}"
        fi
        ;;
    version)
        echo -e "${GREEN}現在のマイグレーションバージョンを表示しています...${NC}"
        alembic_command current
        ;;
    history)
        echo -e "${GREEN}マイグレーション履歴を表示しています...${NC}"
        alembic_command history
        ;;
    reset)
        echo -e "${RED}警告: このコマンドはデータベースをリセットします。全てのデータが失われます！${NC}"
        read -p "本当に続行しますか？ (yes/no) " -r
        echo
        if [[ $REPLY == "yes" ]]; then
            echo -e "${YELLOW}データベースをリセットしています...${NC}"
            alembic_command downgrade base
            alembic_command upgrade head
            # 初期管理者ユーザーの作成
            echo -e "${GREEN}初期データを設定しています...${NC}"
            python -m app.db.init_db
            echo -e "${GREEN}データベースのリセットが完了しました${NC}"
        else
            echo -e "${GREEN}リセットをキャンセルしました${NC}"
        fi
        ;;
    *)
        echo -e "${RED}エラー: 不明なコマンド '$COMMAND'${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}完了しました${NC}"