#!/bin/bash

# UniCore テスト実行スクリプト
# SQLAlchemy 2.0、FastAPI、Pydantic v2 のテストスイート

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

# デフォルトのテストパス、カバレッジ、verbose オプションの初期値
TEST_PATH="app/tests"
COVERAGE=false
VERBOSE=false

# 引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test)
            TEST_PATH="${2:-app/tests}"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo -e "${GREEN}UniCore テスト実行スクリプト${NC}"
            echo "使用法: $0 [オプション]"
            echo "オプション:"
            echo "  -t, --test PATH     指定したパスのテストを実行 (デフォルト: app/tests)"
            echo "  -c, --coverage      カバレッジレポートを生成"
            echo "  -v, --verbose       詳細な出力"
            echo "  -h, --help          このヘルプを表示"
            exit 0
            ;;
        *)
            echo -e "${RED}不明なオプション: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}テスト環境を準備しています...${NC}"

# 環境変数設定（テスト用）
if [ -f .env.test ]; then
    echo -e "${GREEN}環境変数を .env.test から読み込んでいます...${NC}"
    set -a
    . ./.env.test
    set +a
else
    # .env.test が存在しない場合は、手動で設定（こちらは参考値）
    export APP_ENV="testing"
    export SECRET_KEY="your-test-secret-key"
    export POSTGRES_SERVER="localhost"
    export POSTGRES_USER="unicore_test_user"
    export POSTGRES_PASSWORD="your_test_password"
    export POSTGRES_DB="unicore_test"
    export POSTGRES_PORT="5432"
    export FIRST_SUPERUSER_EMAIL="admin_test@example.com"
    export FIRST_SUPERUSER_PASSWORD="admintestpassword"
fi

# テスト実行
if [ "$COVERAGE" = true ]; then
    echo -e "${GREEN}カバレッジレポート付きでテストを実行しています...${NC}"
    COVERAGE_OPTS="--cov=app --cov-report=term --cov-report=html:coverage_report"
    
    if [ "$VERBOSE" = true ]; then
        python3 -m pytest $TEST_PATH $COVERAGE_OPTS -v
    else
        python3 -m pytest $TEST_PATH $COVERAGE_OPTS
    fi
    echo -e "${GREEN}カバレッジレポートが coverage_report ディレクトリに生成されました${NC}"
else
    echo -e "${GREEN}テストを実行しています...${NC}"
    
    if [ "$VERBOSE" = true ]; then
        python3 -m pytest $TEST_PATH -v
    else
        python3 -m pytest $TEST_PATH
    fi
fi

echo -e "${GREEN}テスト完了${NC}"