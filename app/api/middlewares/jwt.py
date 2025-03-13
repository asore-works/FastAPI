from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status

class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, prefix: str = "", exclude_paths: list = None):
        super().__init__(app)
        self.prefix = prefix
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next):
        # 除外パスに含まれている場合は JWT 処理をスキップ
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # ここで JWT の検証処理など必要な処理を実装可能
        # 例: ヘッダーからトークンを抽出して検証する処理など

        response = await call_next(request)

        # 204 No Content の場合、明示的に空のレスポンスを返す
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return response