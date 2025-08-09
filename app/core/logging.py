"""
日志系统配置

提供全局的日志配置和管理功能
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from .config import config


def setup_logging():
    """设置日志系统"""

    # 确保data目录存在
    log_dir = Path("data")
    log_dir.mkdir(exist_ok=True)

    # 获取日志配置
    log_config = config.get_logging_config()
    log_level = getattr(logging, log_config["level"].upper())
    log_format = log_config["format"]

    # 创建formatter
    formatter = logging.Formatter(log_format)

    # 设置根日志级别
    logging.getLogger().setLevel(log_level)

    # 移除现有的处理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 2. 应用主日志文件处理器 (永久保存)
    app_handler = logging.FileHandler(
        filename=log_dir / "feedsieve.log",
        encoding="utf-8"
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)

    # 3. 错误日志文件处理器 (永久保存)
    error_handler = logging.FileHandler(
        filename=log_dir / "error.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # 4. Webhook日志处理器 (永久保存)
    webhook_handler = logging.FileHandler(
        filename=log_dir / "webhook.log",
        encoding="utf-8"
    )
    webhook_handler.setLevel(logging.INFO)
    webhook_handler.setFormatter(formatter)

    # 5. 队列处理日志处理器 (永久保存)
    queue_handler = logging.FileHandler(
        filename=log_dir / "queue.log",
        encoding="utf-8"
    )
    queue_handler.setLevel(logging.INFO)
    queue_handler.setFormatter(formatter)

    # 6. LLM服务日志处理器 (永久保存)
    llm_handler = logging.FileHandler(
        filename=log_dir / "llm.log",
        encoding="utf-8"
    )
    llm_handler.setLevel(logging.INFO)
    llm_handler.setFormatter(formatter)

    # 7. Readwise服务日志处理器 (永久保存)
    readwise_handler = logging.FileHandler(
        filename=log_dir / "readwise.log",
        encoding="utf-8"
    )
    readwise_handler.setLevel(logging.INFO)
    readwise_handler.setFormatter(formatter)

    # 添加处理器到根日志器
    logging.root.addHandler(console_handler)
    logging.root.addHandler(app_handler)
    logging.root.addHandler(error_handler)

    # 设置专用日志器
    setup_specialized_loggers(
        webhook_handler, queue_handler, llm_handler, readwise_handler)

    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {log_config['level']}")
    logger.info(f"日志目录: {log_dir.absolute()}")


def setup_specialized_loggers(webhook_handler, queue_handler, llm_handler, readwise_handler):
    """设置专用日志器"""

    # Webhook日志器
    webhook_logger = logging.getLogger("feedsieve.webhook")
    webhook_logger.addHandler(webhook_handler)
    webhook_logger.setLevel(logging.INFO)
    webhook_logger.propagate = True  # 继续传播到根日志器

    # 队列处理日志器
    queue_logger = logging.getLogger("feedsieve.queue")
    queue_logger.addHandler(queue_handler)
    queue_logger.setLevel(logging.INFO)
    queue_logger.propagate = True

    # LLM服务日志器
    llm_logger = logging.getLogger("feedsieve.llm")
    llm_logger.addHandler(llm_handler)
    llm_logger.setLevel(logging.INFO)
    llm_logger.propagate = True

    # Readwise服务日志器
    readwise_logger = logging.getLogger("feedsieve.readwise")
    readwise_logger.addHandler(readwise_handler)
    readwise_logger.setLevel(logging.INFO)
    readwise_logger.propagate = True


def get_logger(name: str = None) -> logging.Logger:
    """获取指定名称的日志器"""
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def get_webhook_logger() -> logging.Logger:
    """获取Webhook专用日志器"""
    return logging.getLogger("feedsieve.webhook")


def get_queue_logger() -> logging.Logger:
    """获取队列处理专用日志器"""
    return logging.getLogger("feedsieve.queue")


def get_llm_logger() -> logging.Logger:
    """获取LLM服务专用日志器"""
    return logging.getLogger("feedsieve.llm")


def get_readwise_logger() -> logging.Logger:
    """获取Readwise服务专用日志器"""
    return logging.getLogger("feedsieve.readwise")
