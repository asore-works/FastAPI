from fastapi import APIRouter

from app.api.routes import auth, users, items

# メインAPIルーター
api_router = APIRouter()

# 各モジュールのルーターをインクルード
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])