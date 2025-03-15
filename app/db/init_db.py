"""
ファイル: app/db/init_db.py
説明: システムロールおよび初期管理者（スーパーユーザー）の作成など、データベースの初期化を行います。
      マイグレーション後の初期データ投入用スクリプトです。
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.role import RoleService
from app.services.user import UserService
from app.schemas.user import UserCreate

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_roles(db: AsyncSession) -> None:
    """
    システムロールをデータベースに初期化します。
    """
    logger.info("システムロールの初期化を開始...")
    await RoleService.initialize_system_roles(db)
    logger.info("システムロールの初期化が完了しました。")


async def create_first_superuser(db: AsyncSession) -> None:
    """
    環境変数で設定された初期管理者（スーパーユーザー）アカウントを作成します。
    
    すでにアカウントが存在する場合や、設定がない場合は作成をスキップします。
    """
    email = settings.FIRST_SUPERUSER_EMAIL
    password = settings.FIRST_SUPERUSER_PASSWORD

    if not email or not password:
        logger.warning(
            "初期管理者アカウントの設定がありません。"
            "環境変数FIRST_SUPERUSER_EMAILとFIRST_SUPERUSER_PASSWORDを設定してください。"
        )
        return

    try:
        existing_user = await UserService.get_by_email(db, email)
        if existing_user:
            logger.info(f"管理者アカウント '{email}' は既に存在します。作成をスキップします。")
            return

        superuser_role = await RoleService.get_by_name(db, "スーパーユーザー")
        role_id = superuser_role.id if superuser_role else None

        user_in = UserCreate(
            email=email,
            password=password,
            full_name="Initial Admin User",
            is_superuser=True,
            role_id=role_id
        )

        logger.info(f"管理者アカウント '{email}' を作成中...")
        await UserService.create(db, user_in)
        logger.info(f"管理者アカウント '{email}' の作成に成功しました。")
    except Exception as error:
        logger.error(f"管理者アカウント作成中にエラーが発生しました: {error}")
        raise


async def init_db() -> None:
    """
    データベースの初期化メイン関数
    """
    try:
        logger.info("データベース接続を確立中...")
        async with AsyncSessionLocal() as db:
            await initialize_roles(db)
            await create_first_superuser(db)
            logger.info("データベースの初期化が完了しました。")
    except Exception as error:
        logger.error(f"データベース初期化中にエラーが発生しました: {error}")
        raise


if __name__ == "__main__":
    logger.info("データベース初期化を開始します...")
    asyncio.run(init_db())