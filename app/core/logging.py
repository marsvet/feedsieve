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

    # 2. 应用主日志文件处理器
    app_handler = logging.FileHandler(
        filename=log_dir / "feedsieve.log",
        encoding="utf-8"
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)

    # 添加处理器到根日志器
    logging.root.addHandler(console_handler)
    logging.root.addHandler(app_handler)

    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {log_config['level']}")
    logger.info(f"日志目录: {log_dir.absolute()}")


def get_logger(name: str = None) -> logging.Logger:
    """获取指定名称的日志器"""
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)
