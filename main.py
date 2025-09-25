#!/usr/bin/env python3
"""
feedsieve - Content filtering and management system
Main application entry point

Author: Terry Ma <terry.o.ma@outlook.com>
"""

import logging

import uvicorn

from app.core.app import create_app

logger = logging.getLogger(__name__)

# 创建应用程序实例
app = create_app()


def main():
    """主函数 - 启动应用程序"""
    try:
        # 启动 FastAPI 应用程序
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise


if __name__ == "__main__":
    main()
