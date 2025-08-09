"""
全局常量定义
"""

from enum import Enum


class RecordStatus(str, Enum):
    """记录状态枚举"""
    USEFUL = "useful"        # 1. 有用的 - 成功并符合要求
    USELESS = "useless"      # 2. 无用的 - 成功并不符合要求
    FAILED = "failed"        # 3. 未处理成功
    SKIP = "skip"            # 4. 不支持的feed - 直接skip


class QueueStatus(str, Enum):
    """队列状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
    UNRECOVERABLE = "unrecoverable"
