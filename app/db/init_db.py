import asyncio
import logging
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_first_superuser(db: AsyncSession) -> None:
    """
    初期管理者ユーザーを作成
    
    環境変数から設定された管理者アカウントを作成し、データベースに挿入
    既に存在する場合は作成をスキップ
    """
    # 環境変数から初期管理者情報を取得
    first_superuser_email = settings.FIRST_SUPERUSER_EMAIL
    first_superuser_password = settings.FIRST_SUPERUSER_PASSWORD

    # 管理者アカウントが設定されていない場合はスキップ
    if not first_superuser_email or not first_superuser_password:
        logger.warning(
            "初期管理者アカウントの設定がありません。"
            "FIRST_SUPERUSER_EMAILとFIRST_SUPERUSER_PASSWORDを設定してください。"
        )
        return

    # 既存の管理者ユーザーを検索
    result = await db.execute("SELECT * FROM users WHERE email = :email", {"email": first_superuser_email})
    user = result.fetchone()

    # 既に存在する場合はスキップ
    if user:
        logger.info(f"管理者アカウント {first_superuser_email} は既に存在します。スキップします。")
        return

    # 管理者ユーザーオブジェクトを作成
    superuser_obj = User(
        email=first_superuser_email,
        hashed_password=get_password_hash(first_superuser_password),
        full_name="Initial Admin User",
        is_superuser=True,
        is_active=True,
    )

    # データベースに追加
    db.add(superuser_obj)
    await db.commit()
    logger.info(f"管理者アカウント {first_superuser_email} を作成しました")


async def init_db() -> None:
    """
    データベース初期化メイン関数
    
    マイグレーション後に初期データを設定
    実際のマイグレーションはAlembicコマンドラインで実行することを推奨
    """
    try:
        # データベース接続
        async with AsyncSessionLocal() as db:
            # 初期管理者ユーザーの作成
            await create_first_superuser(db)
            
            # 他の初期データ設定もここに追加可能
            
            logger.info("データベース初期化が完了しました")
    except Exception as e:
        logger.error(f"データベース初期化中にエラーが発生しました: {e}")
        raise


# スクリプトとして実行した場合
if __name__ == "__main__":
    logger.info("データベース初期化を開始します")
    asyncio.run(init_db())