"""
应用程序工厂

负责创建和配置 FastAPI 应用程序实例
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..controllers import webhook_router
from ..middleware import (
    LoggingMiddleware,
    WebhookGuardMiddleware,
    setup_cors,
    setup_error_handlers,
)
from ..services.queue_service import queue_service
from .database import db
from .logging import setup_logging

logger = logging.getLogger(__name__)


async def task_processor():
    """后台任务处理循环 - 根据配置间隔处理队列项以避免LLM限流"""
    from ..core.config import config

    # 获取队列处理间隔配置
    process_interval = config.get_queue_config().get("process_interval_seconds", 300)
    error_wait_time = min(60, process_interval // 5)  # 错误时等待时间，不超过配置间隔的1/5

    logger.info(f"队列处理间隔设置为: {process_interval}秒 ({process_interval//60}分钟)")

    while True:
        try:
            await queue_service.process_queue()
            await asyncio.sleep(process_interval)
        except Exception as e:
            logger.error(f"任务处理循环异常: {e}")
            await asyncio.sleep(error_wait_time)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时初始化
    logger.info("正在启动 feedsieve...")

    # 创建数据库表
    db.create_tables()

    # 启动任务处理循环
    asyncio.create_task(task_processor())

    logger.info("feedsieve 启动完成")
    yield

    # 关闭时清理
    logger.info("正在关闭 feedsieve...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用程序实例"""

    # 设置完善的日志系统
    setup_logging()

    # 创建应用程序实例 (禁用文档端点)
    app = FastAPI(
        title="feedsieve",
        description="内容过滤和管理系统",
        version="1.2.0",
        lifespan=lifespan,
        docs_url=None,  # 禁用 Swagger 文档
        redoc_url=None,  # 禁用 ReDoc 文档
        openapi_url=None,  # 禁用 OpenAPI schema
    )

    # 设置中间件
    setup_cors(app)
    setup_error_handlers(app)

    # 添加 Webhook 保护中间件 (最先执行，拦截不允许的路径)
    app.add_middleware(WebhookGuardMiddleware)

    # 添加日志中间件
    app.add_middleware(LoggingMiddleware)

    # 仅注册 webhook 路由
    app.include_router(webhook_router, prefix="")

    return app
