"""
中间件包

包含 FastAPI 应用程序的中间件：
- cors: 跨域资源共享中间件
- logging: 日志中间件
- error_handler: 错误处理中间件
- webhook_guard: Webhook 路径保护中间件
"""

from .cors import setup_cors
from .error_handler import setup_error_handlers
from .logging import LoggingMiddleware
from .webhook_guard import WebhookGuardMiddleware

__all__ = [
    "setup_cors",
    "LoggingMiddleware",
    "setup_error_handlers",
    "WebhookGuardMiddleware",
]
