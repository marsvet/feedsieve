"""
Webhook 路径保护中间件

只允许访问特定的 webhook 路径，其他所有路径返回 404
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class WebhookGuardMiddleware(BaseHTTPMiddleware):
    """Webhook 路径保护中间件 - 仅允许访问指定的 webhook 路径"""

    def __init__(self, app, allowed_paths: list = None):
        super().__init__(app)
        # 仅允许访问的路径 (严格模式：只有 webhook 路径)
        self.allowed_paths = allowed_paths or [
            "/api/webhook/053e46c8c41a4de199c4",  # 唯一允许的 Webhook 路径
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        path = request.url.path

        # 检查路径是否在允许列表中
        if not self._is_path_allowed(path):
            # 返回 404，无响应内容
            logger.warning(f"拒绝访问未授权路径: {request.method} {path}")
            return PlainTextResponse("", status_code=404)

        # 允许的路径，继续处理
        return await call_next(request)

    def _is_path_allowed(self, path: str) -> bool:
        """检查路径是否被允许"""
        # 精确匹配允许的路径
        return path in self.allowed_paths
