"""
错误处理中间件
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_404_NOT_FOUND

from ..models.schemas import ErrorResponse

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """设置全局错误处理器"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> Response:
        """处理 HTTP 异常"""
        # 对于 webhook 路径的 404 错误，返回空响应
        if (exc.status_code == 404 and
                request.url.path == "/api/webhook/053e46c8c41a4de199c4"):
            return Response(status_code=404)

        logger.warning(f"HTTP 异常: {exc.status_code}: {exc.detail}")

        error_response = ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            details={"status_code": exc.status_code},
        )

        return JSONResponse(status_code=exc.status_code, content=error_response.dict())

    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """处理 Starlette HTTP 异常"""
        logger.warning(f"Starlette 异常: {exc.status_code}: {exc.detail}")

        error_response = ErrorResponse(
            error="StarletteHTTPException",
            message=exc.detail,
            details={"status_code": exc.status_code},
        )

        return JSONResponse(status_code=exc.status_code, content=error_response.dict())

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """处理未捕获的异常"""
        logger.error(f"未处理异常: {type(exc).__name__}: {str(exc)}", exc_info=True)

        error_response = ErrorResponse(
            error="InternalServerError",
            message="服务器内部错误",
            details={"path": request.url.path, "method": request.method},
        )

        return JSONResponse(status_code=500, content=error_response.dict())

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """处理 404 错误"""
        path = request.url.path

        # 对于 webhook 路径，返回空响应
        if path == "/api/webhook/053e46c8c41a4de199c4":
            return Response(status_code=404)

        # 对于 API 请求返回 JSON 格式的 404
        if path.startswith("/api"):
            logger.warning(f"API 端点未找到: {request.method} {path}")

            error_response = ErrorResponse(
                error="NotFound",
                message=f"API 端点未找到: {request.method} {path}",
                details={
                    "path": path,
                    "method": request.method,
                    "available_endpoints": "请查看 /docs 获取可用的 API 端点",
                },
            )

            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND, content=error_response.dict()
            )

        # 对于非 API 请求，返回标准的 404 响应
        logger.warning(f"页面未找到: {request.method} {path}")
        return JSONResponse(
            status_code=HTTP_404_NOT_FOUND,
            content={
                "error": "Not Found",
                "message": f"页面未找到: {path}",
                "details": {"path": path, "method": request.method},
            },
        )
