from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from typing import Callable

from app.api.api import api_router
from app.core.config import settings
from app.core.exceptions import AppException


# アプリケーション作成
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
)

# CORS設定
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# パフォーマンス計測ミドルウェア
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    """
    リクエスト処理時間を計測し、レスポンスヘッダーに追加するミドルウェア
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# カスタム例外ハンドラー
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    アプリケーション例外のグローバルハンドラー
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


# APIルーター登録
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ルートエンドポイント
@app.get("/")
def read_root():
    """
    アプリケーションルートエンドポイント
    """
    return {
        "message": "Welcome to UniCore API Server",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時に実行される処理
    """
    # ここでデータベース初期化などの処理を行うことができます
    pass


# アプリケーション終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    """
    アプリケーション終了時に実行される処理
    """
    # ここでリソースのクリーンアップなどを行うことができます
    pass


# アプリケーション実行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )