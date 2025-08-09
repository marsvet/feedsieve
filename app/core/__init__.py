"""
Core 模块

包含应用程序的核心组件：
- config: 配置管理
- database: 数据库连接和管理
- constants: 全局常量
- app: 应用程序工厂
- logging: 日志系统
"""

from .config import config
from .constants import (
    QueueStatus,
    RecordStatus,
)
from .database import db

__all__ = [
    "config",
    "db",
    "RecordStatus",
    "QueueStatus",
]
